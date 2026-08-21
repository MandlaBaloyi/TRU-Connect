"""
Products' own per-tier limits -- everything about "how many / how big"
for product media and bulk import, tier-gated, living right next to
the code that enforces it. Deliberately NOT in shared/media -- see
that module's own config.py docstring for the full reasoning on why
these numbers leaked there originally and don't belong there.

NUMBERS ARE DELIBERATELY CONSERVATIVE, MATCHING TODAY'S REAL
CLOUDINARY PLAN -- this account is currently on Cloudinary's Free
plan: 25 monthly credits total, shared across storage + bandwidth +
transformations combined (confirmed directly against Cloudinary's own
published pricing). A single bulk import at generous limits could
exhaust an entire month's budget in one request. These numbers are
sized for that reality, not guessed at in isolation -- raise them
later purely through this file once the account is on a paid plan; no
other file needs to change.

STORED_MAX_DIMENSION_PX is the ingest-time compression target -- see
providers/cloudinary_provider.py's own docstring on why capping what
Cloudinary actually STORES matters more than capping what a client is
allowed to upload. Same value across all tiers today (display quality
doesn't really need to differ by plan); only the volume/size ceilings
that map to real cost differ per tier.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domains.supplier.tiers.tier import Tier


@dataclass(frozen=True)
class ProductsTierLimits:
    photos_per_product: int
    max_image_upload_bytes: int
    stored_max_dimension_px: int
    bulk_max_images_per_job: int
    bulk_max_rows_per_job: int


def get_products_limits(tier: Tier) -> ProductsTierLimits:
    from src.domains.supplier.products.tiers import free, max, pro

    return {
        Tier.FREE: free.LIMITS,
        Tier.PRO: pro.LIMITS,
        Tier.MAX: max.LIMITS,
    }[tier]
