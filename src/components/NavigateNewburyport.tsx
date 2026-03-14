'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  DirectoryListing,
  DirectoryCategory,
  DIRECTORY_CATEGORIES,
  DIRECTORY_LISTINGS,
  COMMUNITY_EVENTS,
  NEWBURYPORT_AREAS,
  NEWBURYPORT_STATS,
  HISTORIC_FACTS,
} from '../data/newburyport-directory';
import {
  createStephanieDirectoryAgent,
  StephanieDirectoryAgent,
  AgentResponse,
  ConversationMessage,
} from '../lib/stephanieDirectoryAgent';
import { AVATAR_PERSONALITIES } from '../data/newburyport-schema';

// ============================================================================
// ICON MAP (simple text-based icons for categories)
// ============================================================================

const CATEGORY_ICONS: Record<string, string> = {
  dining: '\u{1F374}',
  shopping: '\u{1F6CD}',
  services: '\u{1F4BC}',
  recreation: '\u{2600}',
  historic: '\u{1F3DB}',
  arts: '\u{1F3A8}',
  lodging: '\u{1F6CF}',
  community: '\u{1F3E2}',
};

const FACT_CATEGORY_COLORS: Record<string, string> = {
  maritime: 'border-sky-500/30 bg-sky-950/30',
  history: 'border-amber-500/30 bg-amber-950/30',
  people: 'border-purple-500/30 bg-purple-950/30',
  firsts: 'border-emerald-500/30 bg-emerald-950/30',
  culture: 'border-rose-500/30 bg-rose-950/30',
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const StarRating: React.FC<{ rating: number; count?: number }> = ({ rating, count }) => {
  const fullStars = Math.floor(rating);
  const hasHalf = rating - fullStars >= 0.5;

  return (
    <div className="flex items-center gap-1">
      <div className="flex">
        {Array.from({ length: 5 }, (_, i) => (
          <span
            key={i}
            className={`text-sm ${
              i < fullStars
                ? 'text-amber-400'
                : i === fullStars && hasHalf
                ? 'text-amber-300'
                : 'text-slate-600'
            }`}
          >
            {'\u2605'}
          </span>
        ))}
      </div>
      <span className="text-xs text-slate-400">
        {rating.toFixed(1)}
        {count !== undefined && ` (${count})`}
      </span>
    </div>
  );
};

const PriceBadge: React.FC<{ price?: string }> = ({ price }) => {
  if (!price) return null;
  return (
    <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
      {price}
    </span>
  );
};

const FeaturedBadge: React.FC = () => (
  <span className="text-xs font-medium text-amber-300 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-full">
    Featured
  </span>
);

const Tag: React.FC<{ label: string; onClick?: () => void }> = ({ label, onClick }) => (
  <button
    onClick={onClick}
    className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded hover:bg-slate-700 transition-colors"
  >
    {label}
  </button>
);

// ============================================================================
// LISTING CARD
// ============================================================================

const ListingCard: React.FC<{
  listing: DirectoryListing;
  onSelect: (listing: DirectoryListing) => void;
  isSelected: boolean;
}> = ({ listing, onSelect, isSelected }) => (
  <div
    onClick={() => onSelect(listing)}
    className={`p-4 rounded-xl border cursor-pointer transition-all ${
      isSelected
        ? 'bg-sky-950/40 border-sky-500/50 ring-1 ring-sky-500/30'
        : 'bg-slate-900/60 border-slate-800 hover:border-slate-600 hover:bg-slate-900/80'
    }`}
  >
    <div className="flex items-start justify-between mb-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-semibold text-white text-sm truncate">{listing.name}</h3>
          {listing.featured && <FeaturedBadge />}
          <PriceBadge price={listing.priceRange} />
        </div>
        <p className="text-xs text-slate-400 mt-0.5">{listing.subcategory}</p>
      </div>
    </div>

    <p className="text-xs text-slate-400 line-clamp-2 mb-2">{listing.description}</p>

    <div className="flex items-center justify-between">
      {listing.rating && (
        <StarRating rating={listing.rating} count={listing.reviewCount} />
      )}
      <div className="flex gap-1 flex-wrap justify-end">
        {listing.tags.slice(0, 2).map((tag) => (
          <span key={tag} className="text-[10px] bg-slate-800/80 text-slate-500 px-1.5 py-0.5 rounded">
            {tag}
          </span>
        ))}
      </div>
    </div>
  </div>
);

// ============================================================================
// CATEGORY PILL
// ============================================================================

const CategoryPill: React.FC<{
  category: DirectoryCategory;
  isActive: boolean;
  count: number;
  onClick: () => void;
}> = ({ category, isActive, count, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
      isActive
        ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
        : 'bg-slate-800/60 text-slate-300 hover:bg-slate-700/60 border border-slate-700/50'
    }`}
  >
    <span>{CATEGORY_ICONS[category.id] || '\u{1F4CD}'}</span>
    <span>{category.name}</span>
    <span className={`text-xs ${isActive ? 'text-sky-200' : 'text-slate-500'}`}>
      {count}
    </span>
  </button>
);

// ============================================================================
// DETAIL PANEL
// ============================================================================

const ListingDetail: React.FC<{ listing: DirectoryListing }> = ({ listing }) => (
  <div className="space-y-4">
    <div>
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-lg font-bold text-white">{listing.name}</h2>
        {listing.featured && <FeaturedBadge />}
      </div>
      <p className="text-sm text-sky-400">{listing.subcategory}</p>
    </div>

    <p className="text-sm text-slate-300">{listing.description}</p>

    {listing.rating && (
      <StarRating rating={listing.rating} count={listing.reviewCount} />
    )}

    <div className="space-y-2 text-sm">
      <div className="flex items-start gap-2">
        <span className="text-slate-500 w-16 shrink-0">Address</span>
        <span className="text-slate-200">{listing.address}</span>
      </div>
      {listing.phone && (
        <div className="flex items-start gap-2">
          <span className="text-slate-500 w-16 shrink-0">Phone</span>
          <span className="text-slate-200">{listing.phone}</span>
        </div>
      )}
      {listing.website && (
        <div className="flex items-start gap-2">
          <span className="text-slate-500 w-16 shrink-0">Web</span>
          <a
            href={listing.website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-400 hover:text-sky-300 truncate"
          >
            {listing.website.replace(/^https?:\/\//, '')}
          </a>
        </div>
      )}
      {listing.hours && (
        <div className="flex items-start gap-2">
          <span className="text-slate-500 w-16 shrink-0">Hours</span>
          <span className="text-slate-200">{listing.hours}</span>
        </div>
      )}
      {listing.priceRange && (
        <div className="flex items-start gap-2">
          <span className="text-slate-500 w-16 shrink-0">Price</span>
          <PriceBadge price={listing.priceRange} />
        </div>
      )}
    </div>

    {listing.amenities && listing.amenities.length > 0 && (
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Amenities</p>
        <div className="flex flex-wrap gap-1.5">
          {listing.amenities.map((a) => (
            <span key={a} className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">
              {a}
            </span>
          ))}
        </div>
      </div>
    )}

    {listing.serviceArea && listing.serviceArea.length > 0 && (
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Service Area</p>
        <div className="flex flex-wrap gap-1.5">
          {listing.serviceArea.map((area) => (
            <span key={area} className="text-xs bg-sky-900/30 text-sky-300 px-2 py-1 rounded border border-sky-800/30">
              {area}
            </span>
          ))}
        </div>
      </div>
    )}

    <div>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Tags</p>
      <div className="flex flex-wrap gap-1.5">
        {listing.tags.map((tag) => (
          <Tag key={tag} label={tag} />
        ))}
      </div>
    </div>
  </div>
);

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const NavigateNewburyport: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedListing, setSelectedListing] = useState<DirectoryListing | null>(null);
  const [activeTab, setActiveTab] = useState<'directory' | 'events' | 'areas' | 'history' | 'about'>('directory');

  // Stephanie.ai Assistant State
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantQuery, setAssistantQuery] = useState('');
  const [assistantMessages, setAssistantMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string; listings?: DirectoryListing[] }>>([]);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [agent] = useState<StephanieDirectoryAgent>(() => createStephanieDirectoryAgent({ personality: 'FRIENDLY_LOCAL' }));

  const handleAssistantSubmit = useCallback(async () => {
    const q = assistantQuery.trim();
    if (!q) return;

    setAssistantMessages((prev) => [...prev, { role: 'user', text: q }]);
    setAssistantQuery('');
    setAssistantLoading(true);

    try {
      const response = await agent.processQuery(q);
      setAssistantMessages((prev) => [
        ...prev,
        { role: 'assistant', text: response.text, listings: response.listings },
      ]);
    } finally {
      setAssistantLoading(false);
    }
  }, [assistantQuery, agent]);

  // Filtered listings
  const filteredListings = useMemo(() => {
    let results = [...DIRECTORY_LISTINGS];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (l) =>
          l.name.toLowerCase().includes(q) ||
          l.description.toLowerCase().includes(q) ||
          l.tags.some((t) => t.toLowerCase().includes(q)) ||
          l.subcategory.toLowerCase().includes(q)
      );
    }

    if (activeCategory) {
      results = results.filter((l) => l.categoryId === activeCategory);
    }

    // Sort: featured first, then by rating
    results.sort((a, b) => {
      if (a.featured !== b.featured) return a.featured ? -1 : 1;
      return (b.rating || 0) - (a.rating || 0);
    });

    return results;
  }, [searchQuery, activeCategory]);

  // Category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    const base = searchQuery
      ? DIRECTORY_LISTINGS.filter((l) => {
          const q = searchQuery.toLowerCase();
          return (
            l.name.toLowerCase().includes(q) ||
            l.description.toLowerCase().includes(q) ||
            l.tags.some((t) => t.toLowerCase().includes(q))
          );
        })
      : DIRECTORY_LISTINGS;

    DIRECTORY_CATEGORIES.forEach((c) => {
      counts[c.id] = base.filter((l) => l.categoryId === c.id).length;
    });
    return counts;
  }, [searchQuery]);

  // Stats
  const stats = useMemo(() => {
    const rated = DIRECTORY_LISTINGS.filter((l) => l.rating);
    return {
      total: DIRECTORY_LISTINGS.length,
      categories: DIRECTORY_CATEGORIES.length,
      featured: DIRECTORY_LISTINGS.filter((l) => l.featured).length,
      avgRating: rated.length > 0
        ? (rated.reduce((s, l) => s + (l.rating || 0), 0) / rated.length).toFixed(1)
        : '0',
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 via-sky-950 to-slate-900 border-b border-sky-800/30">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">
                Navigate <span className="text-sky-400">Newburyport</span>
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Your guide to the Clipper City &mdash; dining, shopping, services, recreation & more
              </p>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div className="text-right">
                <p className="text-xs text-slate-500">Listings</p>
                <p className="text-xl font-bold text-white">{stats.total}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Categories</p>
                <p className="text-xl font-bold text-white">{stats.categories}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Avg Rating</p>
                <p className="text-xl font-bold text-amber-400">{stats.avgRating}</p>
              </div>
            </div>
          </div>

          {/* Search Bar */}
          <div className="mt-6">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search businesses, services, restaurants, activities..."
              className="w-full px-5 py-3 bg-slate-800/80 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/50"
            />
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-slate-900/50 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            {(['directory', 'events', 'areas', 'history', 'about'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-sm font-medium transition-all capitalize ${
                  activeTab === tab
                    ? 'text-sky-400 border-b-2 border-sky-400 bg-sky-500/5'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* ===== DIRECTORY TAB ===== */}
        {activeTab === 'directory' && (
          <>
            {/* Category Pills */}
            <div className="flex gap-2 overflow-x-auto pb-4 scrollbar-hide">
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                  !activeCategory
                    ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
                    : 'bg-slate-800/60 text-slate-300 hover:bg-slate-700/60 border border-slate-700/50'
                }`}
              >
                All ({DIRECTORY_LISTINGS.length})
              </button>
              {DIRECTORY_CATEGORIES.map((cat) => (
                <CategoryPill
                  key={cat.id}
                  category={cat}
                  isActive={activeCategory === cat.id}
                  count={categoryCounts[cat.id] || 0}
                  onClick={() =>
                    setActiveCategory(activeCategory === cat.id ? null : cat.id)
                  }
                />
              ))}
            </div>

            {/* Listings Grid + Detail Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Listings */}
              <div className="lg:col-span-2">
                <p className="text-xs text-slate-500 mb-3">
                  {filteredListings.length} result{filteredListings.length !== 1 ? 's' : ''}
                  {activeCategory && (
                    <>
                      {' '}
                      in{' '}
                      <span className="text-sky-400">
                        {DIRECTORY_CATEGORIES.find((c) => c.id === activeCategory)?.name}
                      </span>
                    </>
                  )}
                  {searchQuery && (
                    <>
                      {' '}
                      for &ldquo;<span className="text-sky-400">{searchQuery}</span>&rdquo;
                    </>
                  )}
                </p>

                {filteredListings.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {filteredListings.map((listing) => (
                      <ListingCard
                        key={listing.id}
                        listing={listing}
                        onSelect={setSelectedListing}
                        isSelected={selectedListing?.id === listing.id}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <p className="text-lg mb-2">No listings found</p>
                    <p className="text-sm">Try adjusting your search or category filter</p>
                  </div>
                )}
              </div>

              {/* Detail Panel */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 h-fit sticky top-6">
                {selectedListing ? (
                  <ListingDetail listing={selectedListing} />
                ) : (
                  <div className="text-center py-8">
                    <p className="text-slate-500 text-sm">Select a listing to view details</p>
                    <p className="text-slate-600 text-xs mt-2">
                      Click any business card on the left
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* ===== EVENTS TAB ===== */}
        {activeTab === 'events' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Community Events</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {COMMUNITY_EVENTS.map((event) => (
                <div
                  key={event.id}
                  className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-sky-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-white">{event.name}</h3>
                    {event.recurring && (
                      <span className="text-[10px] bg-sky-900/30 text-sky-300 px-2 py-0.5 rounded-full border border-sky-800/30">
                        Recurring
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-sky-400 mb-1">{event.date}</p>
                  <p className="text-xs text-slate-500 mb-3">{event.location}</p>
                  <p className="text-sm text-slate-300">{event.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== AREAS TAB ===== */}
        {activeTab === 'areas' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Newburyport Neighborhoods</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {NEWBURYPORT_AREAS.map((area) => (
                <div
                  key={area.id}
                  className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-sky-700/50 transition-colors"
                >
                  <h3 className="font-semibold text-white mb-2">{area.name}</h3>
                  <p className="text-sm text-slate-300 mb-3">{area.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {area.highlights.map((h) => (
                      <span
                        key={h}
                        className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded"
                      >
                        {h}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== HISTORY TAB ===== */}
        {activeTab === 'history' && (
          <div className="space-y-6 max-w-4xl">
            <h2 className="text-xl font-bold text-white">Historic Facts & Trivia</h2>
            <p className="text-sm text-slate-400">
              Discover the rich history behind Newburyport &mdash; from clipper ships and the Underground Railroad
              to eccentric businessmen and presidential visits.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {HISTORIC_FACTS.map((fact) => (
                <div
                  key={fact.id}
                  className={`rounded-xl p-5 border ${FACT_CATEGORY_COLORS[fact.category] || 'border-slate-800 bg-slate-900/60'}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-white">{fact.title}</h3>
                    {fact.year && (
                      <span className="text-[10px] bg-white/10 text-slate-300 px-2 py-0.5 rounded-full shrink-0 ml-2">
                        {fact.year}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-300">{fact.description}</p>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-3">
                    {fact.category}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== ABOUT TAB ===== */}
        {activeTab === 'about' && (
          <div className="space-y-6 max-w-3xl">
            <h2 className="text-xl font-bold text-white">About Newburyport</h2>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Population</p>
                  <p className="text-lg font-bold text-white">
                    {NEWBURYPORT_STATS.population.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Founded</p>
                  <p className="text-lg font-bold text-white">{NEWBURYPORT_STATS.founded}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Area</p>
                  <p className="text-lg font-bold text-white">{NEWBURYPORT_STATS.area}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Nickname</p>
                  <p className="text-lg font-bold text-sky-400">{NEWBURYPORT_STATS.nickname}</p>
                </div>
              </div>

              <p className="text-sm text-slate-400 italic mb-4">
                &ldquo;{NEWBURYPORT_STATS.motto}&rdquo;
              </p>

              <div className="space-y-2">
                {NEWBURYPORT_STATS.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-sky-400 mt-0.5">*</span>
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-3">Quick Facts</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">County</span>
                  <span className="text-slate-200">{NEWBURYPORT_STATS.county}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">State</span>
                  <span className="text-slate-200">{NEWBURYPORT_STATS.state}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">ZIP Code</span>
                  <span className="text-slate-200 font-mono">{NEWBURYPORT_STATS.zipCode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Elevation</span>
                  <span className="text-slate-200">{NEWBURYPORT_STATS.elevation}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Timezone</span>
                  <span className="text-slate-200">{NEWBURYPORT_STATS.timezone}</span>
                </div>
              </div>
            </div>

            <div className="bg-sky-950/30 border border-sky-800/30 rounded-xl p-6">
              <h3 className="font-semibold text-sky-400 mb-2">NoblePort ETF Integration</h3>
              <p className="text-sm text-slate-300">
                Navigate Newburyport is part of the NoblePort.eth ecosystem, connecting
                local business discovery with blockchain-verified real estate listings
                and decentralized identity verification. Real estate listings feature
                smart contract verification and DID-based authentication via
                did:ens:nobleport.eth.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Stephanie.ai Assistant Floating Button */}
      <button
        onClick={() => setAssistantOpen(!assistantOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-br from-purple-600 to-sky-600 text-white shadow-lg shadow-purple-600/30 hover:shadow-purple-600/50 transition-all flex items-center justify-center z-50"
        title="Ask Stephanie.ai"
      >
        <span className="text-2xl">{assistantOpen ? '\u2715' : '\u2728'}</span>
      </button>

      {/* Stephanie.ai Assistant Panel */}
      {assistantOpen && (
        <div className="fixed bottom-24 right-6 w-96 max-h-[32rem] bg-slate-900 border border-purple-500/30 rounded-2xl shadow-2xl shadow-purple-900/30 z-50 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-900/80 to-sky-900/80 px-4 py-3 border-b border-purple-500/20">
            <div className="flex items-center gap-2">
              <span className="text-lg">{'\u2728'}</span>
              <div>
                <h3 className="text-sm font-semibold text-white">Stephanie<span className="text-purple-400">.ai</span></h3>
                <p className="text-[10px] text-purple-300">Your Newburyport Guide</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[20rem]">
            {assistantMessages.length === 0 && (
              <div className="text-center py-6">
                <p className="text-sm text-slate-400">{agent.greeting}</p>
                <div className="mt-3 space-y-1">
                  {['Best restaurants for dinner?', 'What to do this weekend?', 'Tell me about Newburyport history'].map((q) => (
                    <button
                      key={q}
                      onClick={() => {
                        setAssistantQuery(q);
                      }}
                      className="block w-full text-left text-xs text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {assistantMessages.map((msg, i) => (
              <div
                key={i}
                className={`text-sm ${
                  msg.role === 'user'
                    ? 'text-right'
                    : 'text-left'
                }`}
              >
                <div
                  className={`inline-block max-w-[85%] px-3 py-2 rounded-xl ${
                    msg.role === 'user'
                      ? 'bg-sky-600 text-white rounded-br-sm'
                      : 'bg-slate-800 text-slate-200 rounded-bl-sm'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-xs">{msg.text}</div>
                </div>
                {msg.role === 'assistant' && msg.listings && msg.listings.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {msg.listings.slice(0, 3).map((l) => (
                      <button
                        key={l.id}
                        onClick={() => {
                          setSelectedListing(l);
                          setActiveTab('directory');
                        }}
                        className="block w-full text-left text-[10px] bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 px-2 py-1 rounded transition-colors"
                      >
                        <span className="text-white font-medium">{l.name}</span>
                        <span className="text-slate-500 ml-1">({l.subcategory})</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {assistantLoading && (
              <div className="flex items-center gap-2 text-xs text-purple-400">
                <div className="w-3 h-3 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                Stephanie is thinking...
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-slate-800 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={assistantQuery}
                onChange={(e) => setAssistantQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAssistantSubmit()}
                placeholder="Ask about Newburyport..."
                className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={handleAssistantSubmit}
                disabled={!assistantQuery.trim() || assistantLoading}
                className="px-3 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs text-white transition-colors"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-900/50 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className="text-slate-400 text-sm">
                Navigate Newburyport &mdash; A NoblePort.eth Directory
              </p>
              <p className="text-slate-600 text-xs mt-1">
                Powered by NoblePort ETF | ENS Identity: did:ens:nobleport.eth
              </p>
            </div>
            <div className="flex gap-4 text-sm">
              <span className="text-sky-400">nobleport.eth</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">Newburyport, MA 01950</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default NavigateNewburyport;
