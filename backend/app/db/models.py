"""Central model registry.

Import every module's models here so `Base.metadata` is fully populated for
Alembic autogenerate. Add one import per new model — nothing else needs to
change (not env.py, not this file's structure).
"""

from app.modules.auth.models import (  # noqa: F401
    Account,
    AccountPermission,
    AccountRole,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    VerificationCode,
)
from app.modules.addresses.models import ShippingAddress  # noqa: F401
from app.modules.carts.models import CartItem  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.orders.models import (  # noqa: F401
    Order,
    OrderItem,
    SellerOrder,
    Shipment,
    ShippingInfo,
)
from app.modules.payments.models import Payment  # noqa: F401
from app.modules.premium.models import PremiumPlan, SellerSubscription  # noqa: F401
from app.modules.products.models import (  # noqa: F401
    Attribute,
    Brand,
    CategoryAttribute,
    ListingImage,
    Product,
    ProductImage,
    ProductVariant,
    SellerListing,
    VariantAttributeValue,
)
from app.modules.revenue.models import RevenueTransaction  # noqa: F401
from app.modules.sellers.models import Seller, SellerDocument  # noqa: F401
from app.modules.users.models import Profile  # noqa: F401
