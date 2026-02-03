"""
Cascade Price Provider - Orchestrates multiple price providers.

Tries each provider in order until a price is found, with caching
support and statistics tracking.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Optional

from .base import PriceProvider, PriceResult
from .cache import PriceCache

logger = logging.getLogger(__name__)


class CascadePriceProvider:
    """
    Orchestrates multiple price providers in cascade order.

    Tries each configured provider in sequence until a price is found.
    Results are cached to reduce API calls on subsequent runs.

    Typical cascade order:
    1. Cache (check if we already have a valid price)
    2. Xotelo (free, primary source)
    3. SerpApi (Google Hotels, 250/month free)
    4. Apify (Booking.com, $5/month free tier)
    """

    def __init__(
        self,
        providers: List[PriceProvider],
        cache: Optional[PriceCache] = None
    ) -> None:
        """
        Initialize the cascade provider.

        Args:
            providers: List of providers to try in order
            cache: Optional cache instance (creates default if None)
        """
        self.providers = providers
        self.cache = cache or PriceCache()
        self.stats: Dict[str, int] = defaultdict(int)
        self._reset_stats()

    def _reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = defaultdict(int)
        self.stats["total"] = 0
        self.stats["cache"] = 0
        self.stats["not_found"] = 0

    def get_price(
        self,
        hotel_name: str,
        hotel_key: Optional[str],
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        **kwargs
    ) -> Optional[PriceResult]:
        """
        Get hotel price, trying providers in cascade order.

        Args:
            hotel_name: Display name of the hotel
            hotel_key: Provider-specific key (used by Xotelo)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Adults per room
            **kwargs: Additional provider-specific parameters
                - booking_url: Direct Booking.com URL (for ApifyProvider)

        Returns:
            PriceResult if found by any provider, None otherwise
        """
        self.stats["total"] += 1

        # 1. Check cache first
        cached = self.cache.get(hotel_name, check_in)
        if cached:
            self.stats["cache"] += 1
            logger.debug("[%s] Found in cache: $%.2f", hotel_name, cached["price"])
            return cached

        # 2. Try each provider in order
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(
                    "[%s] Skipping %s (not available)",
                    hotel_name, provider.get_name()
                )
                continue

            logger.debug("[%s] Trying %s...", hotel_name, provider.get_name())

            result = provider.get_price(
                hotel_name, hotel_key, check_in, check_out, rooms, adults,
                **kwargs
            )

            if result:
                # Cache the result
                self.cache.set(hotel_name, check_in, result)
                self.stats[provider.get_name()] += 1

                logger.info(
                    "[%s] Found: $%.2f via %s (%s)",
                    hotel_name, result["price"],
                    result["provider"], provider.get_name()
                )
                return result

        # No price found from any provider
        self.stats["not_found"] += 1
        logger.debug("[%s] No price found from any provider", hotel_name)
        return None

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics for current session.

        Returns:
            Dict with counts per source and totals
        """
        return dict(self.stats)

    def get_stats_summary(self) -> str:
        """
        Get a formatted summary of statistics.

        Returns:
            Multi-line string with statistics
        """
        total = self.stats["total"]
        if total == 0:
            return "No hotels processed"

        lines = [
            f"[STATS] Hotels processed: {total}",
            "[STATS] Prices by source:"
        ]

        # Calculate found total
        found = total - self.stats["not_found"]

        # Add cache stats
        cache_count = self.stats["cache"]
        cache_pct = (cache_count / total * 100) if total > 0 else 0
        lines.append(f"   Cache:      {cache_count:3d} ({cache_pct:.1f}%)")

        # Add provider stats
        for provider in self.providers:
            name = provider.get_name()
            count = self.stats.get(name, 0)
            pct = (count / total * 100) if total > 0 else 0
            # Capitalize and pad name for alignment
            display_name = name.capitalize()
            lines.append(f"   {display_name:10s} {count:3d} ({pct:.1f}%)")

        # Add not found stats
        not_found = self.stats["not_found"]
        not_found_pct = (not_found / total * 100) if total > 0 else 0
        lines.append(f"   NOT FOUND:  {not_found:3d} ({not_found_pct:.1f}%)")

        # Add coverage summary
        coverage_pct = (found / total * 100) if total > 0 else 0
        lines.append(f"[STATS] TOTAL COVERAGE: {found}/{total} ({coverage_pct:.1f}%)")

        return "\n".join(lines)

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._reset_stats()

    def get_available_providers(self) -> List[str]:
        """
        Get list of available (configured) providers.

        Returns:
            List of provider names that are available
        """
        return [p.get_name() for p in self.providers if p.is_available()]
