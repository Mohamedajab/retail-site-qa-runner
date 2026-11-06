"""Independent acceptance contract; fixtures must not supply expected values."""

PRODUCT = {"id": "P1", "title": "Canvas day bag", "price": "24.00", "stock": "In stock"}
SCENARIOS = (
    "healthy",
    "wrong-price",
    "missing-image",
    "broken-basket",
    "malformed-api",
    "javascript-error",
    "repaired",
)
DEFECTS = dict(zip(SCENARIOS[1:6], ("price", "image", "basket", "api", "javascript")))
