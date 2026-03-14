/**
 * Stephanie.ai Directory Agent
 *
 * AI-powered directory assistant that provides semantic search,
 * natural language queries, proactive suggestions, and avatar-driven
 * interactions for the Navigate Newburyport directory.
 *
 * Integrates with the Stephanie.ai orchestration layer and
 * NoblePort.eth ecosystem via MCP.
 *
 * @ens stephanie.nobleport.eth
 */

import {
  DIRECTORY_LISTINGS,
  DIRECTORY_CATEGORIES,
  COMMUNITY_EVENTS,
  HISTORIC_FACTS,
  NEWBURYPORT_STATS,
  NEWBURYPORT_AREAS,
  DirectoryListing,
} from '../data/newburyport-directory';

import {
  SemanticQuery,
  SemanticSearchResult,
  ProactiveSuggestion,
  QueryIntent,
  AVATAR_PERSONALITIES,
  NEWBURYPORT_DATA_SOURCES,
} from '../data/newburyport-schema';

// ============================================================================
// TYPES
// ============================================================================

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    intent?: QueryIntent;
    businessIds?: string[];
    eventIds?: string[];
    confidence?: number;
  };
}

export interface AgentConfig {
  personality: keyof typeof AVATAR_PERSONALITIES;
  enableVoice: boolean;
  enableProactiveSuggestions: boolean;
  maxConversationHistory: number;
}

export interface AgentResponse {
  text: string;
  listings?: DirectoryListing[];
  suggestions?: ProactiveSuggestion[];
  intent: QueryIntent;
  confidence: number;
  voiceText?: string;
  followUpQuestions?: string[];
}

// ============================================================================
// INTENT CLASSIFICATION
// ============================================================================

const INTENT_PATTERNS: Array<{ pattern: RegExp; intent: QueryIntent }> = [
  { pattern: /\b(restaurant|eat|food|dining|lunch|dinner|breakfast|brunch)\b/i, intent: 'find_restaurant' },
  { pattern: /\b(event|festival|concert|show|performance|market)\b/i, intent: 'find_event' },
  { pattern: /\b(recommend|suggest|best|top|favorite|popular)\b/i, intent: 'get_recommendation' },
  { pattern: /\b(hour|open|close|when|time)\b/i, intent: 'check_hours' },
  { pattern: /\b(history|historic|old|heritage|colonial|clipper|maritime)\b/i, intent: 'learn_history' },
  { pattern: /\b(explore|walk|tour|visit|see|do|activities)\b/i, intent: 'explore_area' },
  { pattern: /\b(plan|itinerary|day trip|weekend|schedule)\b/i, intent: 'plan_visit' },
  { pattern: /\b(direction|how to get|where is|location|address|map)\b/i, intent: 'get_directions' },
  { pattern: /\b(shop|store|buy|boutique|antique|gallery)\b/i, intent: 'find_business' },
  { pattern: /\b(find|looking for|search|where can)\b/i, intent: 'find_business' },
];

function classifyIntent(query: string): QueryIntent {
  for (const { pattern, intent } of INTENT_PATTERNS) {
    if (pattern.test(query)) return intent;
  }
  return 'find_business';
}

// ============================================================================
// KEYWORD SEARCH (local, no external API needed)
// ============================================================================

function scoreMatch(listing: DirectoryListing, terms: string[]): number {
  let score = 0;
  const nameL = listing.name.toLowerCase();
  const descL = listing.description.toLowerCase();
  const tagsL = listing.tags.map((t) => t.toLowerCase());
  const catL = listing.subcategory.toLowerCase();

  for (const term of terms) {
    if (nameL.includes(term)) score += 10;
    if (catL.includes(term)) score += 5;
    if (tagsL.some((t) => t.includes(term))) score += 3;
    if (descL.includes(term)) score += 1;
  }

  if (listing.featured) score += 2;
  if (listing.rating) score += listing.rating;

  return score;
}

function searchListings(query: string, maxResults = 6): DirectoryListing[] {
  const terms = query
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter((t) => t.length > 2);

  if (terms.length === 0) return DIRECTORY_LISTINGS.filter((l) => l.featured).slice(0, maxResults);

  const scored = DIRECTORY_LISTINGS.map((listing) => ({
    listing,
    score: scoreMatch(listing, terms),
  }))
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score);

  return scored.slice(0, maxResults).map((s) => s.listing);
}

// ============================================================================
// CONTEXT BUILDER (for RAG / LLM prompts)
// ============================================================================

export function buildDirectoryContext(): string {
  const categories = DIRECTORY_CATEGORIES.map((c) => c.name).join(', ');
  const totalListings = DIRECTORY_LISTINGS.length;
  const featuredNames = DIRECTORY_LISTINGS.filter((l) => l.featured)
    .map((l) => `${l.name} (${l.subcategory})`)
    .join(', ');
  const events = COMMUNITY_EVENTS.map((e) => `${e.name}: ${e.date}`).join('; ');
  const facts = HISTORIC_FACTS.map((f) => `${f.title} (${f.year || 'n/a'}): ${f.description}`).join('\n');
  const areas = NEWBURYPORT_AREAS.map((a) => `${a.name}: ${a.description}`).join('\n');

  return `
# Navigate Newburyport Directory Context

## City Overview
- Name: Newburyport, Massachusetts (${NEWBURYPORT_STATS.nickname})
- Population: ${NEWBURYPORT_STATS.population.toLocaleString()}
- Founded: ${NEWBURYPORT_STATS.founded}
- Motto: "${NEWBURYPORT_STATS.motto}"

## Directory Stats
- Total Listings: ${totalListings}
- Categories: ${categories}
- Featured Businesses: ${featuredNames}

## Community Events
${events}

## Neighborhoods
${areas}

## Historic Facts
${facts}

## Data Sources
${NEWBURYPORT_DATA_SOURCES.map((s) => `- ${s.name} (${s.reliability}): ${s.url || 'API'}`).join('\n')}
`.trim();
}

/**
 * Build a focused context string for a specific query
 */
export function buildQueryContext(query: string, intent: QueryIntent): string {
  const matchedListings = searchListings(query, 8);

  let context = `User query: "${query}"\nDetected intent: ${intent}\n\n`;

  if (matchedListings.length > 0) {
    context += 'Relevant listings:\n';
    for (const l of matchedListings) {
      context += `- ${l.name} [${l.subcategory}]: ${l.description}`;
      if (l.address) context += ` | ${l.address}`;
      if (l.hours) context += ` | Hours: ${l.hours}`;
      if (l.rating) context += ` | Rating: ${l.rating}/5`;
      if (l.priceRange) context += ` | Price: ${l.priceRange}`;
      context += '\n';
    }
  }

  if (intent === 'learn_history') {
    context += '\nHistoric facts:\n';
    for (const f of HISTORIC_FACTS) {
      context += `- ${f.title} (${f.year || ''}): ${f.description}\n`;
    }
  }

  if (intent === 'find_event') {
    context += '\nUpcoming/recurring events:\n';
    for (const e of COMMUNITY_EVENTS) {
      context += `- ${e.name}: ${e.date} at ${e.location} - ${e.description}\n`;
    }
  }

  if (intent === 'explore_area') {
    context += '\nNeighborhoods:\n';
    for (const a of NEWBURYPORT_AREAS) {
      context += `- ${a.name}: ${a.description} | Highlights: ${a.highlights.join(', ')}\n`;
    }
  }

  return context;
}

// ============================================================================
// STEPHANIE DIRECTORY AGENT
// ============================================================================

export class StephanieDirectoryAgent {
  private config: AgentConfig;
  private conversationHistory: ConversationMessage[] = [];

  constructor(config?: Partial<AgentConfig>) {
    this.config = {
      personality: config?.personality || 'FRIENDLY_LOCAL',
      enableVoice: config?.enableVoice ?? false,
      enableProactiveSuggestions: config?.enableProactiveSuggestions ?? true,
      maxConversationHistory: config?.maxConversationHistory ?? 20,
    };
  }

  get personality() {
    return AVATAR_PERSONALITIES[this.config.personality];
  }

  get greeting(): string {
    return this.personality.greeting;
  }

  // ========== CONVERSATION ==========

  async processQuery(userMessage: string): Promise<AgentResponse> {
    // Record user message
    this.addMessage('user', userMessage);

    // Classify intent
    const intent = classifyIntent(userMessage);

    // Search for relevant listings
    const listings = searchListings(userMessage);

    // Generate response based on intent
    const response = this.generateResponse(userMessage, intent, listings);

    // Record assistant response
    this.addMessage('assistant', response.text, {
      intent,
      businessIds: listings.map((l) => l.id),
      confidence: response.confidence,
    });

    return response;
  }

  private generateResponse(
    query: string,
    intent: QueryIntent,
    listings: DirectoryListing[]
  ): AgentResponse {
    const persona = this.personality;

    switch (intent) {
      case 'find_restaurant':
        return this.respondRestaurant(query, listings, persona.personality);

      case 'find_event':
        return this.respondEvent(query);

      case 'learn_history':
        return this.respondHistory(query, persona.personality);

      case 'get_recommendation':
        return this.respondRecommendation(query, listings, persona.personality);

      case 'explore_area':
        return this.respondExplore(query);

      case 'check_hours':
        return this.respondHours(query, listings);

      case 'plan_visit':
        return this.respondPlanVisit(query, listings);

      default:
        return this.respondGeneral(query, listings);
    }
  }

  private respondRestaurant(
    query: string,
    listings: DirectoryListing[],
    tone: string
  ): AgentResponse {
    const restaurants = listings.filter((l) => l.categoryId === 'dining');
    if (restaurants.length === 0) {
      // Fall back to all dining listings
      const allDining = DIRECTORY_LISTINGS.filter((l) => l.categoryId === 'dining')
        .sort((a, b) => (b.rating || 0) - (a.rating || 0))
        .slice(0, 4);
      return {
        text: `I couldn't find an exact match, but here are some top dining spots in Newburyport:\n\n${allDining.map((r) => `**${r.name}** (${r.subcategory}) - ${r.description.slice(0, 100)}...`).join('\n\n')}`,
        listings: allDining,
        intent: 'find_restaurant',
        confidence: 0.7,
        followUpQuestions: [
          'Want me to filter by cuisine type?',
          'Looking for waterfront dining specifically?',
          'Any price range preference?',
        ],
      };
    }

    const topPick = restaurants[0];
    const others = restaurants.slice(1, 4);

    let text = `Great choice exploring Newburyport's dining scene! I'd recommend **${topPick.name}** — ${topPick.description}`;
    if (topPick.priceRange) text += ` (${topPick.priceRange})`;
    if (topPick.rating) text += ` | ${topPick.rating}/5 stars`;

    if (others.length > 0) {
      text += `\n\nAlso worth checking out:\n${others.map((r) => `- **${r.name}** (${r.subcategory}): ${r.description.slice(0, 80)}...`).join('\n')}`;
    }

    return {
      text,
      listings: restaurants,
      intent: 'find_restaurant',
      confidence: 0.85,
      followUpQuestions: [
        `Want more details about ${topPick.name}?`,
        'Should I suggest spots with outdoor seating?',
        'Looking for a specific cuisine?',
      ],
    };
  }

  private respondEvent(query: string): AgentResponse {
    const queryL = query.toLowerCase();
    const matchedEvents = COMMUNITY_EVENTS.filter(
      (e) =>
        e.name.toLowerCase().includes(queryL) ||
        e.description.toLowerCase().includes(queryL) ||
        e.category.toLowerCase().includes(queryL)
    );

    const events = matchedEvents.length > 0 ? matchedEvents : COMMUNITY_EVENTS;

    const text = events
      .map((e) => `**${e.name}** — ${e.date}\n${e.location}\n${e.description}`)
      .join('\n\n');

    return {
      text: `Here are community events in Newburyport:\n\n${text}`,
      intent: 'find_event',
      confidence: matchedEvents.length > 0 ? 0.9 : 0.7,
      followUpQuestions: [
        'Want details about a specific event?',
        'Looking for events this weekend?',
        'Interested in arts, music, or food events?',
      ],
    };
  }

  private respondHistory(query: string, tone: string): AgentResponse {
    const queryL = query.toLowerCase();
    const matchedFacts = HISTORIC_FACTS.filter(
      (f) =>
        f.title.toLowerCase().includes(queryL) ||
        f.description.toLowerCase().includes(queryL)
    );

    const facts = matchedFacts.length > 0 ? matchedFacts : HISTORIC_FACTS;

    const intro =
      tone === 'historic'
        ? 'Ah, you want to hear about our storied past! Let me share some tales of this fine port city:'
        : 'Newburyport has a fascinating history! Here are some highlights:';

    const text =
      intro +
      '\n\n' +
      facts
        .map((f) => `**${f.title}** ${f.year ? `(${f.year})` : ''}\n${f.description}`)
        .join('\n\n');

    // Also find historic site listings
    const historicListings = DIRECTORY_LISTINGS.filter((l) => l.categoryId === 'historic');

    return {
      text,
      listings: historicListings,
      intent: 'learn_history',
      confidence: 0.9,
      followUpQuestions: [
        'Want to visit the Custom House Maritime Museum?',
        'Interested in a walking tour of the Historic District?',
        'Want to hear about Lord Timothy Dexter?',
      ],
    };
  }

  private respondRecommendation(
    query: string,
    listings: DirectoryListing[],
    tone: string
  ): AgentResponse {
    const top = listings.length > 0 ? listings : DIRECTORY_LISTINGS.filter((l) => l.featured).slice(0, 5);

    const intro =
      tone === 'enthusiastic'
        ? "Oh, you want the best of Newburyport? Here's my top picks!"
        : "Here are some of Newburyport's highlights I'd recommend:";

    const text =
      intro +
      '\n\n' +
      top
        .map(
          (l) =>
            `**${l.name}** (${l.subcategory})${l.rating ? ` — ${l.rating}/5` : ''}\n${l.description.slice(0, 120)}...`
        )
        .join('\n\n');

    return {
      text,
      listings: top,
      intent: 'get_recommendation',
      confidence: 0.85,
      followUpQuestions: [
        'Want recommendations for a specific category?',
        'Looking for family-friendly options?',
        'Interested in hidden gems off the beaten path?',
      ],
    };
  }

  private respondExplore(query: string): AgentResponse {
    const queryL = query.toLowerCase();
    const matchedAreas = NEWBURYPORT_AREAS.filter(
      (a) =>
        a.name.toLowerCase().includes(queryL) ||
        a.description.toLowerCase().includes(queryL) ||
        a.highlights.some((h) => h.toLowerCase().includes(queryL))
    );

    const areas = matchedAreas.length > 0 ? matchedAreas : NEWBURYPORT_AREAS;

    const text =
      'Here are the neighborhoods and areas to explore in Newburyport:\n\n' +
      areas
        .map(
          (a) => `**${a.name}**\n${a.description}\nHighlights: ${a.highlights.join(', ')}`
        )
        .join('\n\n');

    return {
      text,
      intent: 'explore_area',
      confidence: 0.85,
      followUpQuestions: [
        'Want to explore a specific neighborhood?',
        'Looking for waterfront or beach areas?',
        'Interested in hiking at Maudslay State Park?',
      ],
    };
  }

  private respondHours(query: string, listings: DirectoryListing[]): AgentResponse {
    const withHours = listings.filter((l) => l.hours);

    if (withHours.length === 0) {
      return {
        text: "I couldn't find specific hours for that. Can you tell me which business you're looking for?",
        intent: 'check_hours',
        confidence: 0.5,
        followUpQuestions: [
          'Which business are you looking for?',
          'Want to see all restaurants open now?',
        ],
      };
    }

    const text = withHours
      .map((l) => `**${l.name}**: ${l.hours}${l.phone ? ` | Call: ${l.phone}` : ''}`)
      .join('\n');

    return {
      text: `Here are the hours:\n\n${text}`,
      listings: withHours,
      intent: 'check_hours',
      confidence: 0.9,
    };
  }

  private respondPlanVisit(query: string, listings: DirectoryListing[]): AgentResponse {
    const morning = DIRECTORY_LISTINGS.filter(
      (l) => l.categoryId === 'dining' && l.subcategory === 'Cafes & Coffee'
    );
    const afternoon = DIRECTORY_LISTINGS.filter(
      (l) => l.categoryId === 'recreation' || l.categoryId === 'historic'
    );
    const evening = DIRECTORY_LISTINGS.filter(
      (l) => l.categoryId === 'dining' && ['Fine Dining', 'Seafood'].includes(l.subcategory)
    );

    const morningPick = morning[0];
    const afternoonPick = afternoon.filter((l) => l.featured)[0] || afternoon[0];
    const eveningPick = evening.filter((l) => l.featured)[0] || evening[0];

    let text = "Here's a perfect day in Newburyport:\n\n";
    if (morningPick) text += `**Morning:** Start at **${morningPick.name}** — ${morningPick.description.slice(0, 80)}...\n\n`;
    if (afternoonPick) text += `**Afternoon:** Head to **${afternoonPick.name}** — ${afternoonPick.description.slice(0, 80)}...\n\n`;
    if (eveningPick) text += `**Evening:** Dinner at **${eveningPick.name}** — ${eveningPick.description.slice(0, 80)}...\n\n`;
    text += "Don't forget to stroll the Waterfront Boardwalk at sunset!";

    return {
      text,
      listings: [morningPick, afternoonPick, eveningPick].filter(Boolean) as DirectoryListing[],
      intent: 'plan_visit',
      confidence: 0.8,
      followUpQuestions: [
        'Want me to adjust this for families with kids?',
        'Prefer a beach-focused day instead?',
        'Want to add shopping stops?',
      ],
    };
  }

  private respondGeneral(query: string, listings: DirectoryListing[]): AgentResponse {
    if (listings.length === 0) {
      return {
        text: `I couldn't find an exact match for "${query}". Try searching for a category like dining, shopping, recreation, or history. Or ask me for recommendations!`,
        intent: 'find_business',
        confidence: 0.4,
        followUpQuestions: [
          'What kind of place are you looking for?',
          'Want to see featured businesses?',
          'Need help exploring a specific area?',
        ],
      };
    }

    const text =
      `Here's what I found:\n\n` +
      listings
        .slice(0, 5)
        .map(
          (l) =>
            `**${l.name}** (${l.subcategory})${l.rating ? ` — ${l.rating}/5` : ''}\n${l.description.slice(0, 100)}...`
        )
        .join('\n\n');

    return {
      text,
      listings,
      intent: 'find_business',
      confidence: 0.75,
      followUpQuestions: [
        `Want more details about ${listings[0]?.name}?`,
        'Should I narrow the results?',
      ],
    };
  }

  // ========== PROACTIVE SUGGESTIONS ==========

  generateSuggestions(context: {
    timeOfDay?: string;
    dayOfWeek?: string;
    weather?: string;
    season?: string;
  }): ProactiveSuggestion[] {
    const suggestions: ProactiveSuggestion[] = [];

    if (context.weather === 'rain' || context.weather === 'cloudy') {
      suggestions.push({
        id: `weather-${Date.now()}`,
        type: 'weather_aware',
        title: 'Indoor Activities',
        message: 'Weather looks grey today. Perfect for browsing antique shops on Market Square or visiting the Custom House Maritime Museum!',
        businessIds: ['oldies-marketplace', 'custom-house-museum', 'the-cottage'],
        confidence: 0.85,
        context,
      });
    }

    if (context.dayOfWeek === 'saturday' || context.dayOfWeek === 'sunday') {
      suggestions.push({
        id: `weekend-${Date.now()}`,
        type: 'time_aware',
        title: 'Weekend Highlights',
        message: "It's the weekend! The Poynt has an incredible brunch, and Maudslay State Park is gorgeous for a morning hike.",
        businessIds: ['the-poynt', 'maudslay-state-park'],
        confidence: 0.88,
        context,
      });
    }

    if (context.timeOfDay === 'evening') {
      suggestions.push({
        id: `evening-${Date.now()}`,
        type: 'time_aware',
        title: 'Evening Plans',
        message: 'Looking for dinner? The Joy Nest has live jazz tonight, and The Black Cow has stunning sunset river views.',
        businessIds: ['joy-nest', 'black-cow'],
        confidence: 0.87,
        context,
      });
    }

    if (context.season === 'summer') {
      suggestions.push({
        id: `summer-${Date.now()}`,
        type: 'seasonal',
        title: 'Summer in Newburyport',
        message: 'Beach weather! Hit Plum Island Beach, grab a lobster roll at Plum Island Coffee, and catch the Waterfront Summer Concert Series on Thursday.',
        businessIds: ['plum-island-beach', 'plum-island-coffee'],
        eventIds: ['waterfront-concerts'],
        confidence: 0.92,
        context,
      });
    }

    return suggestions;
  }

  // ========== CONVERSATION MANAGEMENT ==========

  private addMessage(
    role: ConversationMessage['role'],
    content: string,
    metadata?: ConversationMessage['metadata']
  ): void {
    this.conversationHistory.push({
      role,
      content,
      timestamp: new Date(),
      metadata,
    });

    // Trim history
    if (this.conversationHistory.length > this.config.maxConversationHistory) {
      this.conversationHistory = this.conversationHistory.slice(-this.config.maxConversationHistory);
    }
  }

  getConversationHistory(): ConversationMessage[] {
    return [...this.conversationHistory];
  }

  clearConversation(): void {
    this.conversationHistory = [];
  }

  // ========== RAG CONTEXT FOR EXTERNAL LLM CALLS ==========

  getRAGContext(): string {
    return buildDirectoryContext();
  }

  getQueryRAGContext(query: string): string {
    const intent = classifyIntent(query);
    return buildQueryContext(query, intent);
  }
}

// ============================================================================
// FACTORY
// ============================================================================

export function createStephanieDirectoryAgent(
  config?: Partial<AgentConfig>
): StephanieDirectoryAgent {
  return new StephanieDirectoryAgent(config);
}

export default StephanieDirectoryAgent;
