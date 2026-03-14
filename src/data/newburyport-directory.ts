/**
 * Navigate Newburyport - Directory Data
 *
 * Comprehensive local business and services directory for Newburyport, MA.
 * Curated listings across dining, shopping, services, recreation, and real estate.
 */

// ============================================================================
// TYPES
// ============================================================================

export interface DirectoryCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  subcategories: string[];
}

export interface DirectoryListing {
  id: string;
  name: string;
  categoryId: string;
  subcategory: string;
  description: string;
  address: string;
  phone?: string;
  website?: string;
  hours?: string;
  priceRange?: '$' | '$$' | '$$$' | '$$$$';
  tags: string[];
  featured: boolean;
  rating?: number;
  reviewCount?: number;
  coordinates?: { lat: number; lng: number };
  imageUrl?: string;
  amenities?: string[];
  serviceArea?: string[];
}

export interface DirectoryEvent {
  id: string;
  name: string;
  date: string;
  location: string;
  description: string;
  category: string;
  recurring: boolean;
}

// ============================================================================
// CATEGORIES
// ============================================================================

export const DIRECTORY_CATEGORIES: DirectoryCategory[] = [
  {
    id: 'dining',
    name: 'Dining & Restaurants',
    description: 'Restaurants, cafes, bakeries, and bars in Newburyport',
    icon: 'utensils',
    subcategories: ['Fine Dining', 'Casual Dining', 'Seafood', 'Cafes & Coffee', 'Bakeries', 'Bars & Pubs', 'Takeout & Delivery'],
  },
  {
    id: 'shopping',
    name: 'Shopping & Retail',
    description: 'Boutiques, galleries, and specialty shops downtown and beyond',
    icon: 'shopping-bag',
    subcategories: ['Boutiques & Clothing', 'Art Galleries', 'Antiques', 'Gift Shops', 'Books & Media', 'Home & Garden', 'Specialty Foods'],
  },
  {
    id: 'services',
    name: 'Professional Services',
    description: 'Local professionals and service providers',
    icon: 'briefcase',
    subcategories: ['Legal', 'Financial & Accounting', 'Insurance', 'Real Estate', 'Medical & Dental', 'Veterinary', 'Home Services'],
  },
  {
    id: 'recreation',
    name: 'Recreation & Outdoors',
    description: 'Parks, trails, beaches, and outdoor activities',
    icon: 'sun',
    subcategories: ['Beaches', 'Parks & Trails', 'Boating & Marina', 'Fitness & Yoga', 'Sports', 'Wildlife & Nature'],
  },
  {
    id: 'arts',
    name: 'Arts & Culture',
    description: 'Theaters, museums, music venues, and cultural organizations',
    icon: 'palette',
    subcategories: ['Theaters & Performing Arts', 'Museums', 'Live Music', 'Art Studios', 'Historical Sites', 'Libraries'],
  },
  {
    id: 'lodging',
    name: 'Lodging & Accommodations',
    description: 'Hotels, B&Bs, inns, and vacation rentals',
    icon: 'bed',
    subcategories: ['Hotels', 'Bed & Breakfasts', 'Inns', 'Vacation Rentals'],
  },
  {
    id: 'community',
    name: 'Community & Government',
    description: 'City services, schools, churches, and community organizations',
    icon: 'landmark',
    subcategories: ['City Government', 'Schools & Education', 'Houses of Worship', 'Nonprofits', 'Senior Services'],
  },
  {
    id: 'realestate',
    name: 'Real Estate & Development',
    description: 'Property listings, developers, and construction services',
    icon: 'home',
    subcategories: ['Residential Sales', 'Commercial Properties', 'Property Management', 'Construction & Renovation', 'Architecture & Design'],
  },
];

// ============================================================================
// LISTINGS
// ============================================================================

export const DIRECTORY_LISTINGS: DirectoryListing[] = [
  // ===== DINING =====
  {
    id: 'brine',
    name: 'Brine',
    categoryId: 'dining',
    subcategory: 'Seafood',
    description: 'Upscale oyster bar and seafood restaurant featuring locally sourced New England seafood with creative preparations.',
    address: '25 State St, Newburyport, MA 01950',
    phone: '(978) 358-8479',
    website: 'https://brineoyster.com',
    hours: 'Tue-Sun 11:30am-9pm',
    priceRange: '$$$',
    tags: ['seafood', 'oysters', 'craft cocktails', 'waterfront dining'],
    featured: true,
    rating: 4.6,
    reviewCount: 342,
    coordinates: { lat: 42.8126, lng: -70.8773 },
    amenities: ['Outdoor Seating', 'Full Bar', 'Reservations', 'Private Dining'],
  },
  {
    id: 'mission-oak-grill',
    name: 'Mission Oak Grill',
    categoryId: 'dining',
    subcategory: 'Fine Dining',
    description: 'Contemporary American cuisine in a stylish setting with seasonal menus and an extensive wine list.',
    address: '26 Market Sq, Newburyport, MA 01950',
    phone: '(978) 499-8900',
    website: 'https://missionoakgrill.com',
    hours: 'Mon-Sun 11am-10pm',
    priceRange: '$$$',
    tags: ['american', 'fine dining', 'wine', 'seasonal menu'],
    featured: true,
    rating: 4.5,
    reviewCount: 287,
    coordinates: { lat: 42.8128, lng: -70.8770 },
    amenities: ['Full Bar', 'Reservations', 'Private Events'],
  },
  {
    id: 'abraham-lincoln',
    name: 'Abraham Lincoln',
    categoryId: 'dining',
    subcategory: 'Bars & Pubs',
    description: 'Neighborhood pub with craft beer selection, comfort food, and live entertainment on weekends.',
    address: '1 Market Sq, Newburyport, MA 01950',
    phone: '(978) 462-1138',
    hours: 'Mon-Sun 11am-1am',
    priceRange: '$$',
    tags: ['pub', 'craft beer', 'live music', 'comfort food'],
    featured: false,
    rating: 4.3,
    reviewCount: 198,
    coordinates: { lat: 42.8127, lng: -70.8769 },
    amenities: ['Full Bar', 'Live Entertainment', 'Late Night'],
  },
  {
    id: 'port-tavern',
    name: 'Port Tavern',
    categoryId: 'dining',
    subcategory: 'Casual Dining',
    description: 'Classic New England tavern with hearty comfort food, local brews, and a warm atmosphere.',
    address: '20 State St, Newburyport, MA 01950',
    phone: '(978) 462-2222',
    hours: 'Mon-Sun 11:30am-11pm',
    priceRange: '$$',
    tags: ['tavern', 'burgers', 'new england', 'casual'],
    featured: false,
    rating: 4.2,
    reviewCount: 156,
    coordinates: { lat: 42.8125, lng: -70.8774 },
    amenities: ['Full Bar', 'TV Sports', 'Outdoor Seating'],
  },
  {
    id: 'szechuan-taste',
    name: 'Szechuan Taste',
    categoryId: 'dining',
    subcategory: 'Takeout & Delivery',
    description: 'Authentic Szechuan and Chinese cuisine with spicy specialties and generous portions.',
    address: '19 Pleasant St, Newburyport, MA 01950',
    phone: '(978) 463-0686',
    hours: 'Mon-Sun 11am-9:30pm',
    priceRange: '$$',
    tags: ['chinese', 'szechuan', 'takeout', 'delivery'],
    featured: false,
    rating: 4.1,
    reviewCount: 203,
    coordinates: { lat: 42.8118, lng: -70.8777 },
    amenities: ['Takeout', 'Delivery', 'Dine-In'],
  },
  {
    id: 'jolie-tea-company',
    name: 'Jolie Tea Company',
    categoryId: 'dining',
    subcategory: 'Cafes & Coffee',
    description: 'Charming tea room offering an extensive selection of loose leaf teas, pastries, and light lunch fare.',
    address: '2 Harris St, Newburyport, MA 01950',
    phone: '(978) 462-7010',
    hours: 'Tue-Sat 10am-5pm',
    priceRange: '$$',
    tags: ['tea', 'pastries', 'afternoon tea', 'cozy'],
    featured: false,
    rating: 4.7,
    reviewCount: 124,
    coordinates: { lat: 42.8132, lng: -70.8762 },
    amenities: ['Afternoon Tea Service', 'Private Parties', 'Gift Shop'],
  },
  {
    id: 'abe-and-louies-bakery',
    name: "Abe & Louie's Bakery",
    categoryId: 'dining',
    subcategory: 'Bakeries',
    description: 'Artisan bakery known for sourdough breads, pastries, and custom cakes using local ingredients.',
    address: '58 State St, Newburyport, MA 01950',
    phone: '(978) 465-9700',
    hours: 'Wed-Sun 7am-3pm',
    priceRange: '$$',
    tags: ['bakery', 'sourdough', 'pastries', 'custom cakes'],
    featured: false,
    rating: 4.8,
    reviewCount: 89,
    coordinates: { lat: 42.8121, lng: -70.8781 },
    amenities: ['Custom Orders', 'Catering'],
  },

  // ===== SHOPPING =====
  {
    id: 'leenas-shoes',
    name: "Leena's Shoe Boutique",
    categoryId: 'shopping',
    subcategory: 'Boutiques & Clothing',
    description: 'Curated selection of designer shoes and accessories for women in a welcoming boutique setting.',
    address: '1 Liberty St, Newburyport, MA 01950',
    phone: '(978) 462-7200',
    hours: 'Mon-Sat 10am-6pm, Sun 11am-5pm',
    priceRange: '$$$',
    tags: ['shoes', 'boutique', 'designer', 'accessories'],
    featured: false,
    rating: 4.6,
    reviewCount: 67,
    coordinates: { lat: 42.8130, lng: -70.8765 },
  },
  {
    id: 'lepages-gallery',
    name: "LePage's Gallery & Framing",
    categoryId: 'shopping',
    subcategory: 'Art Galleries',
    description: 'Fine art gallery showcasing regional and national artists with professional custom framing services.',
    address: '16 State St, Newburyport, MA 01950',
    phone: '(978) 462-0637',
    hours: 'Tue-Sat 10am-5:30pm',
    priceRange: '$$$',
    tags: ['art', 'gallery', 'framing', 'local artists'],
    featured: true,
    rating: 4.8,
    reviewCount: 56,
    coordinates: { lat: 42.8124, lng: -70.8775 },
  },
  {
    id: 'oldies-marketplace',
    name: 'Oldies Marketplace',
    categoryId: 'shopping',
    subcategory: 'Antiques',
    description: 'Multi-dealer antique center featuring vintage furniture, collectibles, jewelry, and Americana.',
    address: '3 Market Sq, Newburyport, MA 01950',
    phone: '(978) 465-0643',
    hours: 'Mon-Sat 10am-5pm, Sun 12pm-5pm',
    priceRange: '$$',
    tags: ['antiques', 'vintage', 'collectibles', 'furniture'],
    featured: false,
    rating: 4.4,
    reviewCount: 98,
    coordinates: { lat: 42.8129, lng: -70.8768 },
  },
  {
    id: 'jabberwocky-bookshop',
    name: 'Jabberwocky Bookshop',
    categoryId: 'shopping',
    subcategory: 'Books & Media',
    description: 'Independent bookstore with carefully curated selections, author events, and knowledgeable staff.',
    address: '50 Water St, Newburyport, MA 01950',
    phone: '(978) 465-9359',
    hours: 'Mon-Sat 10am-6pm, Sun 11am-5pm',
    priceRange: '$$',
    tags: ['books', 'independent bookstore', 'author events', 'community'],
    featured: true,
    rating: 4.9,
    reviewCount: 214,
    coordinates: { lat: 42.8119, lng: -70.8749 },
    amenities: ['Author Events', 'Book Clubs', 'Special Orders', 'Gift Wrapping'],
  },

  // ===== SERVICES =====
  {
    id: 'nbpt-law',
    name: 'Newburyport Law Group',
    categoryId: 'services',
    subcategory: 'Legal',
    description: 'Full-service law firm specializing in real estate, estate planning, and small business law.',
    address: '35 Merrimac St, Newburyport, MA 01950',
    phone: '(978) 462-1112',
    hours: 'Mon-Fri 9am-5pm',
    priceRange: '$$$',
    tags: ['legal', 'real estate law', 'estate planning', 'business law'],
    featured: false,
    rating: 4.5,
    reviewCount: 34,
    coordinates: { lat: 42.8133, lng: -70.8780 },
  },
  {
    id: 'harbor-financial',
    name: 'Harbor Financial Advisors',
    categoryId: 'services',
    subcategory: 'Financial & Accounting',
    description: 'Independent financial advisory firm offering wealth management, retirement planning, and tax services.',
    address: '20 Inn St, Newburyport, MA 01950',
    phone: '(978) 465-5550',
    hours: 'Mon-Fri 8:30am-5pm',
    priceRange: '$$$',
    tags: ['financial advisor', 'wealth management', 'retirement', 'tax planning'],
    featured: true,
    rating: 4.7,
    reviewCount: 42,
    coordinates: { lat: 42.8126, lng: -70.8760 },
  },
  {
    id: 'anna-jacques-hospital',
    name: 'Anna Jaques Hospital',
    categoryId: 'services',
    subcategory: 'Medical & Dental',
    description: 'Community hospital providing comprehensive healthcare services to the greater Newburyport area since 1884.',
    address: '25 Highland Ave, Newburyport, MA 01950',
    phone: '(978) 463-1000',
    website: 'https://www.ajh.org',
    hours: '24/7 Emergency, Mon-Fri 8am-5pm offices',
    tags: ['hospital', 'healthcare', 'emergency', 'community health'],
    featured: true,
    rating: 4.0,
    reviewCount: 312,
    coordinates: { lat: 42.8095, lng: -70.8810 },
    amenities: ['Emergency Room', 'Outpatient Services', 'Imaging', 'Lab Services'],
  },

  // ===== RECREATION =====
  {
    id: 'plum-island-beach',
    name: 'Plum Island Beach',
    categoryId: 'recreation',
    subcategory: 'Beaches',
    description: 'Pristine barrier beach with miles of sand dunes, wildlife refuge access, and stunning ocean views.',
    address: 'Plum Island, Newburyport, MA 01950',
    hours: 'Dawn to dusk, seasonal parking',
    tags: ['beach', 'ocean', 'sand dunes', 'wildlife', 'swimming'],
    featured: true,
    rating: 4.8,
    reviewCount: 523,
    coordinates: { lat: 42.7770, lng: -70.8100 },
    amenities: ['Parking', 'Restrooms', 'Lifeguards (seasonal)', 'Accessible Boardwalk'],
    serviceArea: ['Newburyport', 'Newbury', 'Rowley'],
  },
  {
    id: 'parker-river-nwr',
    name: 'Parker River National Wildlife Refuge',
    categoryId: 'recreation',
    subcategory: 'Wildlife & Nature',
    description: 'Over 4,700-acre wildlife sanctuary on Plum Island with birding trails, beach access, and nature programs.',
    address: '6 Plum Island Turnpike, Newburyport, MA 01950',
    phone: '(978) 465-5753',
    website: 'https://www.fws.gov/refuge/parker-river',
    hours: 'Sunrise to sunset daily',
    priceRange: '$',
    tags: ['wildlife refuge', 'birding', 'nature', 'hiking', 'photography'],
    featured: true,
    rating: 4.7,
    reviewCount: 478,
    coordinates: { lat: 42.7680, lng: -70.8050 },
    amenities: ['Trails', 'Observation Platforms', 'Visitor Center', 'Parking'],
  },
  {
    id: 'clipper-city-rail-trail',
    name: 'Clipper City Rail Trail',
    categoryId: 'recreation',
    subcategory: 'Parks & Trails',
    description: 'Paved multi-use trail along the former Eastern Railroad corridor, great for biking and walking.',
    address: 'Parker St to Merrimac St, Newburyport, MA 01950',
    hours: 'Dawn to dusk',
    tags: ['trail', 'biking', 'walking', 'rail trail'],
    featured: false,
    rating: 4.5,
    reviewCount: 167,
    coordinates: { lat: 42.8090, lng: -70.8820 },
    amenities: ['Paved Path', 'Bike Friendly', 'Dog Friendly', 'Wheelchair Accessible'],
  },
  {
    id: 'hiltons-fishing-dock',
    name: "Hilton's Fishing Dock",
    categoryId: 'recreation',
    subcategory: 'Boating & Marina',
    description: 'Deep-sea fishing charters and whale watching excursions departing from Newburyport Harbor.',
    address: '54 Merrimac St, Newburyport, MA 01950',
    phone: '(978) 465-9885',
    hours: 'Seasonal, Apr-Oct',
    priceRange: '$$$',
    tags: ['fishing', 'whale watching', 'charter', 'harbor', 'boating'],
    featured: false,
    rating: 4.4,
    reviewCount: 201,
    coordinates: { lat: 42.8155, lng: -70.8720 },
    amenities: ['Charter Boats', 'Whale Watching', 'Bait Shop', 'Parking'],
  },

  // ===== ARTS & CULTURE =====
  {
    id: 'firehouse-center',
    name: 'Firehouse Center for the Arts',
    categoryId: 'arts',
    subcategory: 'Theaters & Performing Arts',
    description: 'Premier performing arts venue in a converted 1823 firehouse hosting theater, music, comedy, and film.',
    address: '1 Market Sq, Newburyport, MA 01950',
    phone: '(978) 462-7336',
    website: 'https://firehouse.org',
    hours: 'Box office: Tue-Sat 12pm-5pm',
    priceRange: '$$',
    tags: ['theater', 'performing arts', 'live music', 'comedy', 'film'],
    featured: true,
    rating: 4.6,
    reviewCount: 189,
    coordinates: { lat: 42.8128, lng: -70.8758 },
    amenities: ['Box Office', 'Gallery', 'Waterfront Deck', 'Accessible'],
  },
  {
    id: 'custom-house-museum',
    name: 'Custom House Maritime Museum',
    categoryId: 'arts',
    subcategory: 'Museums',
    description: 'Maritime history museum in the 1835 Custom House showcasing Newburyport\'s seafaring heritage.',
    address: '25 Water St, Newburyport, MA 01950',
    phone: '(978) 462-8681',
    website: 'https://customhousemaritimemuseum.org',
    hours: 'Wed-Sun 10am-4pm (seasonal)',
    priceRange: '$',
    tags: ['museum', 'maritime', 'history', 'custom house', 'ship models'],
    featured: true,
    rating: 4.5,
    reviewCount: 145,
    coordinates: { lat: 42.8120, lng: -70.8745 },
    amenities: ['Gift Shop', 'Guided Tours', 'Research Library', 'Children Programs'],
  },
  {
    id: 'newburyport-public-library',
    name: 'Newburyport Public Library',
    categoryId: 'arts',
    subcategory: 'Libraries',
    description: 'Historic public library built in 1771 with extensive collections, community programs, and digital resources.',
    address: '94 State St, Newburyport, MA 01950',
    phone: '(978) 465-4428',
    website: 'https://newburyportpl.org',
    hours: 'Mon-Thu 9am-9pm, Fri-Sat 9am-5pm',
    tags: ['library', 'books', 'community', 'programs', 'historic'],
    featured: false,
    rating: 4.7,
    reviewCount: 98,
    coordinates: { lat: 42.8115, lng: -70.8790 },
    amenities: ['WiFi', 'Meeting Rooms', 'Children Area', 'Digital Resources'],
  },

  // ===== LODGING =====
  {
    id: 'garrison-inn',
    name: 'The Garrison Inn',
    categoryId: 'lodging',
    subcategory: 'Hotels',
    description: 'Boutique hotel in a restored 1809 building in the heart of downtown with modern amenities and historic charm.',
    address: '11 Brown Sq, Newburyport, MA 01950',
    phone: '(978) 499-8500',
    website: 'https://garrisoninn.com',
    priceRange: '$$$',
    tags: ['boutique hotel', 'historic', 'downtown', 'luxury'],
    featured: true,
    rating: 4.4,
    reviewCount: 276,
    coordinates: { lat: 42.8131, lng: -70.8778 },
    amenities: ['Restaurant', 'Rooftop Bar', 'Fitness Center', 'Concierge'],
  },
  {
    id: 'clark-currier-inn',
    name: 'Clark Currier Inn',
    categoryId: 'lodging',
    subcategory: 'Bed & Breakfasts',
    description: 'Elegant 1803 Federal-style B&B with period furnishings, gardens, and gourmet breakfast.',
    address: '45 Green St, Newburyport, MA 01950',
    phone: '(978) 465-8363',
    priceRange: '$$$',
    tags: ['bed and breakfast', 'historic', 'gardens', 'federal style'],
    featured: false,
    rating: 4.8,
    reviewCount: 92,
    coordinates: { lat: 42.8108, lng: -70.8785 },
    amenities: ['Gardens', 'Gourmet Breakfast', 'Parlor', 'Free Parking'],
  },

  // ===== COMMUNITY =====
  {
    id: 'nbpt-city-hall',
    name: 'Newburyport City Hall',
    categoryId: 'community',
    subcategory: 'City Government',
    description: 'Municipal government offices including the Mayor, City Council, and city department services.',
    address: '60 Pleasant St, Newburyport, MA 01950',
    phone: '(978) 465-4413',
    website: 'https://www.cityofnewburyport.com',
    hours: 'Mon-Fri 8am-4:30pm',
    tags: ['city government', 'permits', 'city services', 'municipal'],
    featured: false,
    rating: 3.8,
    reviewCount: 45,
    coordinates: { lat: 42.8112, lng: -70.8795 },
  },
  {
    id: 'nock-molin-school',
    name: 'Nock-Molin Elementary School',
    categoryId: 'community',
    subcategory: 'Schools & Education',
    description: 'Public elementary school serving the Newburyport community with strong academics and arts programs.',
    address: '70 Low St, Newburyport, MA 01950',
    phone: '(978) 465-4440',
    hours: 'School year: Mon-Fri 8:30am-3pm',
    tags: ['school', 'elementary', 'public school', 'education'],
    featured: false,
    rating: 4.3,
    reviewCount: 28,
    coordinates: { lat: 42.8080, lng: -70.8830 },
  },

  // ===== REAL ESTATE =====
  {
    id: 'noble-port-realty',
    name: 'Noble Port Realty',
    categoryId: 'realestate',
    subcategory: 'Residential Sales',
    description: 'Innovative real estate brokerage leveraging blockchain technology for transparent property transactions in the Newburyport area.',
    address: '10 State St, Newburyport, MA 01950',
    phone: '(978) 462-0100',
    website: 'https://nobleport.etf',
    hours: 'Mon-Sat 9am-6pm',
    priceRange: '$$$$',
    tags: ['real estate', 'blockchain', 'tokenized property', 'residential', 'commercial'],
    featured: true,
    rating: 4.9,
    reviewCount: 76,
    coordinates: { lat: 42.8123, lng: -70.8776 },
    amenities: ['Virtual Tours', 'Blockchain Verification', 'Smart Contracts', 'DID Authentication'],
    serviceArea: ['Newburyport', 'Newbury', 'West Newbury', 'Salisbury', 'Amesbury', 'Plum Island'],
  },
  {
    id: 'merrimack-valley-builders',
    name: 'Merrimack Valley Builders',
    categoryId: 'realestate',
    subcategory: 'Construction & Renovation',
    description: 'Licensed general contractor specializing in historic home renovations and new construction in the Merrimack Valley.',
    address: '75 Storey Ave, Newburyport, MA 01950',
    phone: '(978) 463-8800',
    hours: 'Mon-Fri 7am-5pm',
    priceRange: '$$$$',
    tags: ['construction', 'renovation', 'historic homes', 'general contractor'],
    featured: false,
    rating: 4.6,
    reviewCount: 53,
    coordinates: { lat: 42.8075, lng: -70.8850 },
    serviceArea: ['Newburyport', 'Newbury', 'Salisbury', 'Amesbury', 'Georgetown'],
  },
];

// ============================================================================
// COMMUNITY EVENTS
// ============================================================================

export const COMMUNITY_EVENTS: DirectoryEvent[] = [
  {
    id: 'yankee-homecoming',
    name: 'Yankee Homecoming',
    date: 'Late July - Early August (annual)',
    location: 'Downtown Newburyport & Waterfront',
    description: 'Newburyport\'s signature 9-day summer festival featuring concerts, fireworks, road races, craft fairs, and community events since 1958.',
    category: 'festival',
    recurring: true,
  },
  {
    id: 'farmers-market',
    name: 'Newburyport Farmers Market',
    date: 'Sundays, June-October',
    location: 'Tannery Marketplace, 12 Federal St',
    description: 'Weekly outdoor market featuring local produce, artisan goods, baked items, and prepared foods from regional farms and makers.',
    category: 'market',
    recurring: true,
  },
  {
    id: 'art-walk',
    name: 'First Friday Art Walk',
    date: 'First Friday of each month',
    location: 'Downtown galleries and studios',
    description: 'Monthly evening art event where galleries open their doors for new exhibitions, artist receptions, and cultural experiences.',
    category: 'arts',
    recurring: true,
  },
  {
    id: 'holiday-stroll',
    name: 'Annual Holiday Stroll',
    date: 'First weekend of December',
    location: 'Downtown Newburyport',
    description: 'Holiday celebration with festive lights, carolers, horse-drawn carriages, Santa visits, and special shop events.',
    category: 'holiday',
    recurring: true,
  },
  {
    id: 'nbpt-literary-festival',
    name: 'Newburyport Literary Festival',
    date: 'April (annual)',
    location: 'Various downtown venues',
    description: 'Annual celebration of books and authors featuring readings, panels, workshops, and book signings with nationally recognized writers.',
    category: 'arts',
    recurring: true,
  },
  {
    id: 'waterfront-concerts',
    name: 'Waterfront Summer Concert Series',
    date: 'Thursdays, July-August',
    location: 'Waterfront Park, Newburyport',
    description: 'Free outdoor concert series on the Merrimack River waterfront featuring local and regional bands.',
    category: 'music',
    recurring: true,
  },
];

// ============================================================================
// NEIGHBORHOOD / AREA DATA
// ============================================================================

export const NEWBURYPORT_AREAS = [
  {
    id: 'downtown',
    name: 'Downtown / Market Square',
    description: 'Historic commercial center with brick-lined streets, boutiques, restaurants, and the iconic Market Square.',
    highlights: ['Shopping', 'Dining', 'Nightlife', 'Arts'],
  },
  {
    id: 'waterfront',
    name: 'Waterfront & Boardwalk',
    description: 'Scenic Merrimack River waterfront with parks, boardwalk, marina, and harborside dining.',
    highlights: ['River Views', 'Boardwalk', 'Boating', 'Dining'],
  },
  {
    id: 'plum-island',
    name: 'Plum Island',
    description: 'Barrier beach island known for stunning beaches, wildlife refuge, and a tight-knit beach community.',
    highlights: ['Beaches', 'Wildlife', 'Surfing', 'Nature'],
  },
  {
    id: 'south-end',
    name: 'South End',
    description: 'Residential neighborhood with tree-lined streets, historic homes, and proximity to parks.',
    highlights: ['Historic Homes', 'Quiet Streets', 'Parks', 'Schools'],
  },
  {
    id: 'west-side',
    name: 'West Newburyport',
    description: 'Growing area with newer developments, retail centers, and easy highway access.',
    highlights: ['Shopping', 'Highway Access', 'New Development', 'Dining'],
  },
];

// ============================================================================
// QUICK STATS
// ============================================================================

export const NEWBURYPORT_STATS = {
  population: 18_994,
  founded: 1764,
  area: '10.6 sq mi',
  county: 'Essex County',
  state: 'Massachusetts',
  zipCode: '01950',
  elevation: '37 ft',
  timezone: 'Eastern (ET)',
  nickname: 'The Clipper City',
  motto: 'Where the River Meets the Sea',
  highlights: [
    'Historic seaport city on the Merrimack River',
    'Home to Plum Island and Parker River National Wildlife Refuge',
    'Vibrant downtown with 200+ independent shops and restaurants',
    'Rich maritime heritage dating to colonial era',
    'Named one of America\'s best small cities',
  ],
};
