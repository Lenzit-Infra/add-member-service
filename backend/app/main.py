from app.core.logging_config import setup_logging
setup_logging("api")  # backend/logs/api.log — must run before anything else logs/prints

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.core.migrations import run_lightweight_migrations
from app.core import config
from app.modules.account.dependencies import get_current_user

# Import Routers (Controllers)
from app.modules.account.router import router as account_router
from app.modules.auth.router import router as auth_router
from app.modules.orders.router import router as orders_router
from app.modules.analytics.router import router as analytics_router
from app.modules.agents.router import router as agents_router
from app.modules.health.router import router as health_router

# Initialize DB Tables + apply lightweight migrations (new columns on pre-existing tables)
Base.metadata.create_all(bind=engine)
run_lightweight_migrations(engine)

app = FastAPI(title="Lenzit Automation API", version="4.0 Modular")

# CORS Setup — restricted to known frontend origins (required for cookie-based auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Modules
# /account is the public dashboard-login surface (login/refresh/claim-admin/forgot-password).
app.include_router(account_router, prefix="/api/v1/account", tags=["Account"])
# /health is public too — the dashboard's status indicator needs to work even before login.
app.include_router(health_router, prefix="/api/v1", tags=["Health"])

# Everything below requires a logged-in dashboard user — including Telegram-agent
# onboarding (/auth), since adding an agent is itself an admin action.
authed = [Depends(get_current_user)]
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"], dependencies=authed)
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"], dependencies=authed)
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"], dependencies=authed)
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"], dependencies=authed)

@app.get("/")
def health_check():
    return {"status": "System Operational", "mode": "Modular API"}
