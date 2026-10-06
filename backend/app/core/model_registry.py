"""Imports every module's models so `Base.metadata` is complete.

Alembic's `migrations/env.py` imports this module. Add a line here when a
feature gets its first `<feature>_model.py`.
"""

from app.modules.auth import auth_model  # noqa: F401
from app.modules.authorization import authorization_model  # noqa: F401
from app.modules.categories import category_model  # noqa: F401
from app.modules.products import product_model  # noqa: F401
from app.modules.sellers import seller_model  # noqa: F401
