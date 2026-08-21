"""
Pro tier's own Products limits. See tiers/__init__.py's own docstring
for the Cloudinary-economics reasoning behind these specific numbers.
"""
from src.domains.supplier.products.tiers import ProductsTierLimits

LIMITS = ProductsTierLimits(
    photos_per_product=3,
    max_image_upload_bytes=5 * 1024 * 1024,       # 5MB
    stored_max_dimension_px=1600,
    bulk_max_images_per_job=100,
    bulk_max_rows_per_job=3000,
)
