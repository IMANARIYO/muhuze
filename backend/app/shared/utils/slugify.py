import re


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated, URL-safe. 'Samsung Galaxy A15!' ->
    'samsung-galaxy-a15'. Doesn't guarantee uniqueness — callers append a
    numeric suffix on collision (see ProductRepository/CategoryRepository/
    BrandRepository's create methods)."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-")
