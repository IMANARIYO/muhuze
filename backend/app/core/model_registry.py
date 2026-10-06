"""Imports every module's models so `Base.metadata` is complete.

Alembic's `migrations/env.py` imports this module. Add a line here when a
feature gets its first `<feature>_model.py`.
"""

from app.modules.auth import auth_model  # noqa: F401
from app.modules.authorization import authorization_model  # noqa: F401
from app.modules.categories import category_model  # noqa: F401
from app.modules.orders import order_model  # noqa: F401
from app.modules.payments import payment_model  # noqa: F401
from app.modules.products import product_model  # noqa: F401
from app.modules.seller_plans import seller_plan_model  # noqa: F401
from app.modules.sellers import seller_model  # noqa: F401
from app.modules.wallets import wallet_model  # noqa: F401
