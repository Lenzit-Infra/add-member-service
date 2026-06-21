import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list:
    return [v.strip().lower() for v in value.split(",") if v.strip()]


# Dashboard admin allowlist — only these emails may ever self-claim an admin account.
ADMIN_EMAILS = _split_csv(os.getenv("ADMIN_EMAILS", ""))

# JWT signing secret. Auto-generates one on first run if missing so local dev
# always works, but production should pin this in .env (rotating it logs
# everyone out, since all tokens are signed with it).
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
CLAIM_TOKEN_EXPIRE_MINUTES = int(os.getenv("CLAIM_TOKEN_EXPIRE_MINUTES", "30"))
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))

# Used to build links inside emails (claim-admin / reset-password).
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Cookie domain for the refresh-token cookie. Leave unset for local dev
# (browser defaults to the API host); set to ".lenzit.ir" in production so the
# cookie is shared between lenzit.ir (frontend) and api.lenzit.ir (backend).
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") or None
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173"))

# SMTP for claim-admin / forgot-password emails. Works with a free Gmail
# account + an App Password — no paid email API needed.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
