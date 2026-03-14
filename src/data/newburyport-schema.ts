/**
 * Navigate Newburyport - Enhanced Entity Schema
 *
 * Enriched data model for a living directory with verification tiers,
 * voice/avatar integration, relationship graphs, and semantic search support.
 *
 * Designed for PostgreSQL + pgvector (semantic search) or Neo4j (relationships).
 */

// ============================================================================
// CORE ENTITY TYPES
// ============================================================================

/**
 * Business entity - the primary directory listing with enrichment layers
 */
export interface BusinessEntity {
  // Identity
  id: string;
  slug: string;
  name: string;
  legalName?: string;

  // Classification
  primaryCategory: string;
  categories: string[];
  tags: string[];
  naicsCode?: string;

  // Location
  address: Address;
  coordinates: Coordinates;
  serviceArea?: string[];

  // Contact
  phone?: string;
  email?: string;
  website?: string;
  socialMedia?: SocialMedia;

  // Operations
  hours: BusinessHours;
  timezone: string;
  seasonalNotes?: string;
  priceRange?: PriceRange;

  // Content
  description: string;
  shortDescription: string;
  signatureDishes?: string[];
  amenities: string[];
  highlights: string[];

  // Media
  photos: MediaAsset[];
  logoUrl?: string;
  virtualTourUrl?: string;

  // Verification & Trust
  verification: VerificationStatus;
  chamberMember: boolean;
  chamberMemberSince?: string;

  // Reviews & Ratings
  ratings: AggregatedRatings;

  // Voice & Avatar
  voiceGreeting?: string;
  avatarPersonality?: AvatarPersonalityHint;

  // Semantic / AI
  embedding?: number[];
  semanticTags?: string[];

  // Relationships
  relatedBusinessIds?: string[];
  ownerIds?: string[];
  eventIds?: string[];

  // Metadata
  createdAt: string;
  updatedAt: string;
  lastVerifiedAt?: string;
  dataSource: DataSource[];
  featured: boolean;
  active: boolean;
}

/**
 * Person entity - business owners, key contacts, notable figures
 */
export interface PersonEntity {
  id: string;
  name: string;
  title?: string;
  organization?: string;
  businessIds: string[];
  email?: string;
  phone?: string;
  bio?: string;
  historicFigure: boolean;
  active: boolean;
}

/**
 * Organization entity - non-business orgs (Chamber, city gov, nonprofits)
 */
export interface OrganizationEntity {
  id: string;
  name: string;
  type: 'chamber' | 'government' | 'nonprofit' | 'school' | 'religious' | 'civic';
  address: Address;
  phone?: string;
  website?: string;
  memberCount?: number;
  description: string;
  services: string[];
  active: boolean;
}

/**
 * Event entity - community events, recurring markets, festivals
 */
export interface EventEntity {
  id: string;
  name: string;
  description: string;
  category: string;
  location: string;
  address?: Address;
  coordinates?: Coordinates;

  // Scheduling
  startDate?: string;
  endDate?: string;
  recurring: boolean;
  recurrencePattern?: string;
  seasonalAvailability?: string;

  // Details
  ticketUrl?: string;
  priceRange?: PriceRange;
  organizer?: string;
  organizerBusinessId?: string;

  // AI
  weatherSensitive: boolean;
  indoorOutdoor: 'indoor' | 'outdoor' | 'both';
  familyFriendly: boolean;
  tags: string[];

  active: boolean;
}

/**
 * Location entity - neighborhoods, landmarks, geographic areas
 */
export interface LocationEntity {
  id: string;
  name: string;
  type: 'neighborhood' | 'landmark' | 'park' | 'beach' | 'district' | 'waterway';
  description: string;
  coordinates: Coordinates;
  boundary?: Coordinates[];
  highlights: string[];
  businessIds: string[];
  active: boolean;
}

// ============================================================================
// SUPPORTING TYPES
// ============================================================================

export interface Address {
  street: string;
  suite?: string;
  city: string;
  state: string;
  zip: string;
  country: string;
  formatted: string;
}

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface SocialMedia {
  instagram?: string;
  facebook?: string;
  twitter?: string;
  tiktok?: string;
  yelp?: string;
  tripadvisor?: string;
  googleBusiness?: string;
}

export interface BusinessHours {
  regular: DayHours[];
  exceptions?: HoursException[];
  note?: string;
}

export interface DayHours {
  day: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
  open: string;
  close: string;
  closed: boolean;
}

export interface HoursException {
  date: string;
  reason: string;
  open?: string;
  close?: string;
  closed: boolean;
}

export type PriceRange = '$' | '$$' | '$$$' | '$$$$';

export interface MediaAsset {
  url: string;
  alt: string;
  type: 'photo' | 'video' | 'virtual-tour';
  source: string;
  featured: boolean;
}

// ============================================================================
// VERIFICATION & TRUST
// ============================================================================

export interface VerificationStatus {
  tier: VerificationTier;
  chamberVerified: boolean;
  ownerClaimed: boolean;
  googleVerified: boolean;
  lastVerifiedDate?: string;
  badges: VerificationBadge[];
}

export type VerificationTier =
  | 'unverified'
  | 'basic'
  | 'chamber_member'
  | 'premium_verified'
  | 'blockchain_verified';

export interface VerificationBadge {
  type: string;
  label: string;
  issuedBy: string;
  issuedAt: string;
  expiresAt?: string;
}

// ============================================================================
// RATINGS & REVIEWS
// ============================================================================

export interface AggregatedRatings {
  average: number;
  count: number;
  distribution: Record<number, number>;
  sources: RatingSource[];
  lastUpdated: string;
}

export interface RatingSource {
  platform: 'google' | 'yelp' | 'tripadvisor' | 'internal' | 'chamber';
  rating: number;
  count: number;
  url?: string;
}

export interface Review {
  id: string;
  businessId: string;
  authorName: string;
  rating: number;
  text: string;
  date: string;
  source: string;
  verified: boolean;
  moderationStatus: 'pending' | 'approved' | 'flagged' | 'removed';
  aiModerationScore?: number;
  sentiment?: 'positive' | 'neutral' | 'negative';
}

// ============================================================================
// VOICE & AVATAR
// ============================================================================

export interface AvatarPersonalityHint {
  tone: 'warm' | 'professional' | 'enthusiastic' | 'historic' | 'casual';
  localKnowledge: 'expert' | 'knowledgeable' | 'basic';
  specialties: string[];
}

export interface VoiceConfig {
  provider: 'elevenlabs' | 'playht' | 'coqui' | 'web-speech-api';
  voiceId?: string;
  personality: string;
  greeting: string;
  accentNote?: string;
}

export const AVATAR_PERSONALITIES = {
  FRIENDLY_LOCAL: {
    id: 'friendly-local',
    name: 'The Friendly Local',
    description: 'Warm, knowledgeable local guide to Newburyport\'s culture, dining, and hidden gems. Always helpful, never salesy.',
    personality: 'warm' as const,
    greeting: 'Welcome to Newburyport! I\'m your guide to the Clipper City. What are you looking for today?',
    specialties: ['dining', 'shopping', 'events', 'neighborhoods'],
  },
  MARITIME_HISTORIAN: {
    id: 'maritime-historian',
    name: 'The Maritime Historian',
    description: 'An 1800s-era sea captain persona who brings Newburyport\'s rich maritime history to life with stories and facts.',
    personality: 'historic' as const,
    greeting: 'Ahoy! Welcome to the port city where clipper ships once ruled the seas. Let me share the stories of this fine harbor town.',
    specialties: ['history', 'maritime', 'architecture', 'landmarks'],
  },
  WEEKEND_EXPLORER: {
    id: 'weekend-explorer',
    name: 'The Weekend Explorer',
    description: 'Enthusiastic visitor-oriented guide focused on the best experiences for day-trippers and weekend visitors.',
    personality: 'enthusiastic' as const,
    greeting: 'Hey! Ready to explore Newburyport? I\'ve got the best spots for food, beaches, and fun lined up for you!',
    specialties: ['recreation', 'beaches', 'dining', 'nightlife'],
  },
} as const;

// ============================================================================
// DATA SOURCES & INGESTION
// ============================================================================

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  url?: string;
  lastFetched?: string;
  reliability: 'primary' | 'secondary' | 'supplementary';
  autoUpdate: boolean;
  updateFrequency?: string;
}

export type DataSourceType =
  | 'chamber_directory'
  | 'city_government'
  | 'google_places'
  | 'openstreetmap'
  | 'yelp'
  | 'tripadvisor'
  | 'manual_entry'
  | 'owner_claimed'
  | 'web_scrape'
  | 'rss_feed'
  | 'facebook_events';

export const NEWBURYPORT_DATA_SOURCES: DataSource[] = [
  {
    id: 'chamber-directory',
    name: 'Greater Newburyport Chamber of Commerce',
    type: 'chamber_directory',
    url: 'https://business.newburyportchamber.org/members',
    reliability: 'primary',
    autoUpdate: true,
    updateFrequency: 'weekly',
  },
  {
    id: 'shop-newburyport',
    name: 'Shop Newburyport Directory',
    type: 'web_scrape',
    url: 'https://www.newburyportshops.com/directory',
    reliability: 'primary',
    autoUpdate: true,
    updateFrequency: 'weekly',
  },
  {
    id: 'city-contacts',
    name: 'City of Newburyport Official Contacts',
    type: 'city_government',
    url: 'https://www.cityofnewburyport.com/contacts-directory',
    reliability: 'primary',
    autoUpdate: true,
    updateFrequency: 'monthly',
  },
  {
    id: 'newburyport-com',
    name: 'Newburyport.com Business Directory',
    type: 'web_scrape',
    url: 'https://newburyport.com/business-directory',
    reliability: 'secondary',
    autoUpdate: true,
    updateFrequency: 'weekly',
  },
  {
    id: 'google-places',
    name: 'Google Places API',
    type: 'google_places',
    reliability: 'secondary',
    autoUpdate: true,
    updateFrequency: 'daily',
  },
  {
    id: 'openstreetmap',
    name: 'OpenStreetMap',
    type: 'openstreetmap',
    reliability: 'supplementary',
    autoUpdate: true,
    updateFrequency: 'weekly',
  },
];

// ============================================================================
// SEMANTIC SEARCH TYPES
// ============================================================================

export interface SemanticQuery {
  naturalLanguage: string;
  intent?: QueryIntent;
  filters?: {
    category?: string;
    priceRange?: PriceRange;
    openNow?: boolean;
    familyFriendly?: boolean;
    indoorOutdoor?: 'indoor' | 'outdoor' | 'both';
    nearLocation?: string;
    withinMeters?: number;
  };
  context?: {
    weather?: string;
    timeOfDay?: string;
    dayOfWeek?: string;
    userPreferences?: string[];
    previousQueries?: string[];
  };
}

export type QueryIntent =
  | 'find_business'
  | 'find_restaurant'
  | 'find_event'
  | 'get_directions'
  | 'check_hours'
  | 'get_recommendation'
  | 'explore_area'
  | 'learn_history'
  | 'plan_visit';

export interface SemanticSearchResult {
  query: SemanticQuery;
  results: BusinessEntity[];
  explanation: string;
  suggestions?: string[];
  relatedEvents?: EventEntity[];
  avatarResponse?: string;
  confidence: number;
}

// ============================================================================
// PROACTIVE SUGGESTION TYPES (AGI LEARNING LOOP)
// ============================================================================

export interface ProactiveSuggestion {
  id: string;
  type: 'weather_aware' | 'time_aware' | 'preference_based' | 'trending' | 'seasonal';
  title: string;
  message: string;
  businessIds: string[];
  eventIds?: string[];
  confidence: number;
  context: Record<string, unknown>;
  expiresAt?: string;
}

// Example proactive suggestions the system would generate:
export const SAMPLE_PROACTIVE_SUGGESTIONS: ProactiveSuggestion[] = [
  {
    id: 'rain-indoor-1',
    type: 'weather_aware',
    title: 'Rainy Day Plan',
    message: 'Rain expected tomorrow. How about exploring indoor antique shops on Market Square instead of the waterfront walk?',
    businessIds: ['oldies-marketplace', 'the-cottage', 'green-plum-vintage'],
    confidence: 0.85,
    context: { weather: 'rain', temperature: 55 },
  },
  {
    id: 'sunset-dining-1',
    type: 'time_aware',
    title: 'Sunset Dinner',
    message: 'Sunset is at 7:42 PM tonight. The Black Cow has the best river views for dinner — want me to check availability?',
    businessIds: ['black-cow'],
    confidence: 0.9,
    context: { timeOfDay: 'evening', sunset: '7:42 PM' },
  },
  {
    id: 'weekend-brunch-1',
    type: 'time_aware',
    title: 'Weekend Brunch',
    message: 'It\'s Saturday! The Poynt has an excellent brunch scene, and Plum Island Coffee is perfect for a pre-beach stop.',
    businessIds: ['the-poynt', 'plum-island-coffee'],
    confidence: 0.88,
    context: { dayOfWeek: 'saturday', timeOfDay: 'morning' },
  },
  {
    id: 'summer-whale-1',
    type: 'seasonal',
    title: 'Whale Watching Season',
    message: 'Whale watching season is in full swing! Humpbacks and dolphins have been spotted this week. Tours depart from the harbor daily.',
    businessIds: ['whale-watching'],
    confidence: 0.92,
    context: { season: 'summer', month: 'july' },
  },
];
