/**
 * Navigate Newburyport - Directory Service
 *
 * Business logic for searching, filtering, and managing
 * the Newburyport local directory. Integrates with the
 * NoblePort ecosystem for real estate listings.
 */

import {
  DirectoryListing,
  DirectoryCategory,
  DirectoryEvent,
  HistoricFact,
  DIRECTORY_CATEGORIES,
  DIRECTORY_LISTINGS,
  COMMUNITY_EVENTS,
  HISTORIC_FACTS,
  NEWBURYPORT_AREAS,
  NEWBURYPORT_STATS,
} from '../data/newburyport-directory';

// ============================================================================
// TYPES
// ============================================================================

export interface SearchFilters {
  query?: string;
  categoryId?: string;
  subcategory?: string;
  priceRange?: string;
  tags?: string[];
  featured?: boolean;
  minRating?: number;
  serviceArea?: string;
}

export interface SearchResult {
  listings: DirectoryListing[];
  total: number;
  filters: SearchFilters;
}

export interface DirectoryStats {
  totalListings: number;
  totalCategories: number;
  featuredListings: number;
  averageRating: number;
  totalReviews: number;
}

// ============================================================================
// DIRECTORY SERVICE
// ============================================================================

export class NewburyportDirectory {
  private listings: DirectoryListing[];
  private categories: DirectoryCategory[];
  private events: DirectoryEvent[];

  constructor() {
    this.listings = DIRECTORY_LISTINGS;
    this.categories = DIRECTORY_CATEGORIES;
    this.events = COMMUNITY_EVENTS;
  }

  // ========== SEARCH & FILTER ==========

  search(filters: SearchFilters): SearchResult {
    let results = [...this.listings];

    if (filters.query) {
      const q = filters.query.toLowerCase();
      results = results.filter(
        (l) =>
          l.name.toLowerCase().includes(q) ||
          l.description.toLowerCase().includes(q) ||
          l.tags.some((t) => t.toLowerCase().includes(q)) ||
          l.address.toLowerCase().includes(q)
      );
    }

    if (filters.categoryId) {
      results = results.filter((l) => l.categoryId === filters.categoryId);
    }

    if (filters.subcategory) {
      results = results.filter((l) => l.subcategory === filters.subcategory);
    }

    if (filters.priceRange) {
      results = results.filter((l) => l.priceRange === filters.priceRange);
    }

    if (filters.tags && filters.tags.length > 0) {
      results = results.filter((l) =>
        filters.tags!.some((tag) => l.tags.includes(tag))
      );
    }

    if (filters.featured !== undefined) {
      results = results.filter((l) => l.featured === filters.featured);
    }

    if (filters.minRating) {
      results = results.filter(
        (l) => l.rating !== undefined && l.rating >= filters.minRating!
      );
    }

    if (filters.serviceArea) {
      results = results.filter(
        (l) =>
          l.serviceArea && l.serviceArea.includes(filters.serviceArea!)
      );
    }

    return {
      listings: results,
      total: results.length,
      filters,
    };
  }

  // ========== GETTERS ==========

  getAllListings(): DirectoryListing[] {
    return this.listings;
  }

  getListingById(id: string): DirectoryListing | undefined {
    return this.listings.find((l) => l.id === id);
  }

  getFeaturedListings(): DirectoryListing[] {
    return this.listings.filter((l) => l.featured);
  }

  getListingsByCategory(categoryId: string): DirectoryListing[] {
    return this.listings.filter((l) => l.categoryId === categoryId);
  }

  getCategories(): DirectoryCategory[] {
    return this.categories;
  }

  getCategoryById(id: string): DirectoryCategory | undefined {
    return this.categories.find((c) => c.id === id);
  }

  getEvents(): DirectoryEvent[] {
    return this.events;
  }

  getHistoricFacts(): HistoricFact[] {
    return HISTORIC_FACTS;
  }

  getAreas() {
    return NEWBURYPORT_AREAS;
  }

  getCityStats() {
    return NEWBURYPORT_STATS;
  }

  // ========== ANALYTICS ==========

  getDirectoryStats(): DirectoryStats {
    const rated = this.listings.filter((l) => l.rating !== undefined);
    const avgRating =
      rated.length > 0
        ? rated.reduce((sum, l) => sum + (l.rating || 0), 0) / rated.length
        : 0;
    const totalReviews = this.listings.reduce(
      (sum, l) => sum + (l.reviewCount || 0),
      0
    );

    return {
      totalListings: this.listings.length,
      totalCategories: this.categories.length,
      featuredListings: this.listings.filter((l) => l.featured).length,
      averageRating: Math.round(avgRating * 10) / 10,
      totalReviews,
    };
  }

  getAllTags(): string[] {
    const tagSet = new Set<string>();
    this.listings.forEach((l) => l.tags.forEach((t) => tagSet.add(t)));
    return Array.from(tagSet).sort();
  }

  getSubcategories(categoryId: string): string[] {
    const category = this.categories.find((c) => c.id === categoryId);
    return category ? category.subcategories : [];
  }
}

// ============================================================================
// FACTORY
// ============================================================================

export function createNewburyportDirectory(): NewburyportDirectory {
  return new NewburyportDirectory();
}

export default NewburyportDirectory;
