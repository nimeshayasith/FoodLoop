"""Business rules and validation shared by the handlers."""
import re
from decimal import Decimal, InvalidOperation

from common import util
from common.util import Forbidden, ValidationError

# ------------------------------------------------------------- constants
DISTRICTS = [
    "Ampara", "Anuradhapura", "Badulla", "Batticaloa", "Colombo", "Galle", "Gampaha",
    "Hambantota", "Jaffna", "Kalutara", "Kandy", "Kegalle", "Kilinochchi", "Kurunegala",
    "Mannar", "Matale", "Matara", "Monaragala", "Mullaitivu", "Nuwara Eliya",
    "Polonnaruwa", "Puttalam", "Ratnapura", "Trincomalee", "Vavuniya",
]
CATEGORIES = ["Bakery", "Cooked meals", "Fruits & vegetables", "Dairy", "Groceries", "Beverages", "Other"]
BUSINESS_TYPES = ["Supermarket", "Bakery", "Restaurant", "Hotel", "Food producer", "Other"]
ROLES = ["CUSTOMER", "BUSINESS", "CHARITY"]
LISTING_TYPES = ["DISCOUNTED", "DONATION"]
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_IMAGE_BYTES = 3 * 1024 * 1024
MAX_HORIZON_DAYS = 14
MIN_LEAD_SECONDS = 30


# ------------------------------------------------------------ validation
def text(body, field, *, min_len=0, max_len=100, required=True, default=""):
    value = body.get(field)
    if value is None or value == "":
        if required:
            raise ValidationError(f"{field} is required", f"{field}_required")
        return default
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be text", f"{field}_invalid")
    value = value.strip()
    if len(value) < min_len or len(value) > max_len:
        raise ValidationError(f"{field} must be {min_len}-{max_len} characters", f"{field}_invalid")
    return value


def integer(body, field, *, minimum, maximum, default=None):
    value = body.get(field, default)
    if value is None:
        raise ValidationError(f"{field} is required", f"{field}_required")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValidationError(f"{field} must be a whole number", f"{field}_invalid")
    try:
        number = int(str(value))
    except ValueError:
        raise ValidationError(f"{field} must be a whole number", f"{field}_invalid")
    if number < minimum or number > maximum:
        raise ValidationError(f"{field} must be between {minimum} and {maximum}", f"{field}_invalid")
    return number


def price(body, field):
    value = body.get(field)
    try:
        number = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field} must be a number", f"{field}_invalid")
    if number <= 0 or number > Decimal("1000000"):
        raise ValidationError(f"{field} must be greater than 0 (LKR)", f"{field}_invalid")
    return number


def choice(body, field, options):
    value = body.get(field)
    if value not in options:
        raise ValidationError(f"{field} must be one of: {', '.join(options)}", f"{field}_invalid")
    return value


def phone(value, required=True):
    """Normalise Sri Lankan numbers to 94XXXXXXXXX (what wa.me links need)."""
    if value in (None, ""):
        if required:
            raise ValidationError("phone is required", "phone_required")
        return ""
    digits = re.sub(r"[\s\-()+]", "", str(value))
    if re.fullmatch(r"0\d{9}", digits):
        digits = "94" + digits[1:]
    if not re.fullmatch(r"94\d{9}", digits):
        raise ValidationError("Enter a Sri Lankan number like 0771234567", "phone_invalid")
    return digits


# -------------------------------------------------------------- listings
def reserve_by(item):
    """Last moment a listing can still be reserved."""
    return item["saleDeadline"] if item["listingType"] == "DISCOUNTED" else item["collectionDeadline"]


def is_reservable(item, now_iso=None):
    now_iso = now_iso or util.now_iso()
    return item.get("status") == "ACTIVE" and int(item.get("availableQuantity", 0)) > 0 and now_iso < reserve_by(item)


PUBLIC_FIELDS = [
    "listingId", "productName", "description", "category", "unit", "listingType",
    "originalPrice", "discountedPrice", "totalQuantity", "availableQuantity", "saleDeadline",
    "collectionDeadline", "donationDeadline", "bestBeforeDate", "autoDonateRemaining", "status",
    "imageKey", "pickupInstructions", "convertedFromDiscount", "maxPerCustomer", "orgName",
    "orgDistrict", "orgAddress", "orgWhatsapp", "createdAt",
]
OWNER_FIELDS = PUBLIC_FIELDS + ["collectedQuantity", "unclaimedQuantity", "sfnExecutionArn"]


def listing_view(item, owner=False):
    fields = OWNER_FIELDS if owner else PUBLIC_FIELDS
    view = {k: item[k] for k in fields if k in item}
    view["reserveBy"] = reserve_by(item)
    view["reservable"] = is_reservable(item)
    view["state"] = listing_state(item)
    return view


def listing_state(item):
    """Human-friendly phase, computed from the stored status + the clock."""
    if item.get("status") != "ACTIVE":
        return "EXPIRED"
    now = util.now_iso()
    if item["listingType"] == "DONATION":
        if now >= item["collectionDeadline"]:
            return "EXPIRING"
        return "DONATION_CONVERTED" if item.get("convertedFromDiscount") else "DONATION_OPEN"
    if now >= item["saleDeadline"]:
        return "SALE_ENDED"
    return "SALE_OPEN"


# --------------------------------------------------------------- profiles
def require_profile(user_id, *, roles, approved=True):
    from common import db  # local import keeps this module importable without boto3 env

    profile = db.get_profile(user_id)
    if not profile:
        raise Forbidden("Complete your profile first", "profile_required")
    if profile["role"] not in roles:
        raise Forbidden("Your account type cannot do this", "wrong_role")
    if approved and profile.get("status") not in ("ACTIVE", "APPROVED"):
        raise Forbidden("Your organisation is waiting for verification", "pending_verification")
    return profile
