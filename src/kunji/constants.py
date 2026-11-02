"""Project-wide constants. Nothing secret lives here — this file is public."""

APP_NAME = "kunji"
KEYRING_SERVICE = "kunji"

REPO_URL = "https://github.com/testwithsuraj/kunji"
PYPI_JSON_URL = "https://pypi.org/pypi/kunji/json"

# Curated price overrides maintained in this repo. Old versions pick up new prices
# without upgrading because the file is fetched at runtime (and cached for 24h).
CATALOG_URL = "https://raw.githubusercontent.com/testwithsuraj/kunji/main/catalog/pricing.json"

# Public model list with per-token prices. No key needed; nothing about the user is sent.
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Ed25519 PUBLIC keys (base64, raw 32 bytes) used to verify responses signed by the
# kunji cloud server. Public keys are safe to publish. The matching private key must
# only ever exist on the server. Empty until the cloud server is deployed.
CHECKIN_PUBLIC_KEYS: tuple[str, ...] = ()

CACHE_TTL_SECONDS = 24 * 60 * 60
ENTITLEMENT_GRACE_SECONDS = 7 * 24 * 60 * 60
