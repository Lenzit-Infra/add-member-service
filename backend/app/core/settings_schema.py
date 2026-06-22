# app/core/settings_schema.py
"""
Single declarative source of truth for every runtime-tunable constant.
SettingsRepository.initialize_defaults() seeds these into SystemSetting,
and GET /analytics/settings enriches each value with this metadata so the
frontend can group/render the Settings page without duplicating it.
"""

WORKER = "Worker & Throughput"
ANTI_BAN = "Anti-Ban / Telegram Safety"
SECURITY = "Security & Login"

SETTINGS_SCHEMA = [
    # --- Worker & Throughput ---
    {
        "key": "batch_size", "category": WORKER, "label": "Batch Size",
        "description": "How many users the worker tries to add per cycle.",
        "type": "int", "default": 5, "min": 1, "max": 50,
    },
    {
        "key": "sleep_delay_min", "category": WORKER, "label": "Min Delay Between Attempts (seconds)",
        "description": "Minimum randomized wait after every add attempt (success or failure).",
        "type": "int", "default": 10, "min": 5, "max": 600,
    },
    {
        "key": "sleep_delay_max", "category": WORKER, "label": "Max Delay Between Attempts (seconds)",
        "description": "Maximum randomized wait after every add attempt (success or failure).",
        "type": "int", "default": 30, "min": 5, "max": 1200,
    },
    {
        "key": "worker_check_interval", "category": WORKER, "label": "Worker Check Interval (seconds)",
        "description": "How often the scheduler checks for active orders. Requires a worker restart to take effect.",
        "type": "int", "default": 10, "min": 5, "max": 3600,
    },
    {
        "key": "movement_monitor_interval_minutes", "category": WORKER, "label": "Member Movement Check Interval (minutes)",
        "description": "How often the Member Movement Monitor scans target groups for joins/leaves. Requires a worker restart to take effect.",
        "type": "int", "default": 5, "min": 1, "max": 1440,
    },

    # --- Anti-Ban / Telegram Safety ---
    {
        "key": "daily_limit_per_agent", "category": ANTI_BAN, "label": "Steady-State Daily Limit per Agent",
        "description": "Max successful adds/day for a fully warmed-up agent. Telegram does not publish exact thresholds — this is a conservative operator-set ceiling, not a guarantee against bans.",
        "type": "int", "default": 30, "min": 1, "max": 500,
    },
    {
        "key": "new_agent_daily_limit", "category": ANTI_BAN, "label": "New Agent Daily Limit",
        "description": "Daily limit for a brand-new agent (day 0 of warm-up).",
        "type": "int", "default": 5, "min": 1, "max": 500,
    },
    {
        "key": "new_agent_warmup_days", "category": ANTI_BAN, "label": "Warm-up Period (days)",
        "description": "Days over which an agent's daily limit ramps linearly from the New Agent limit up to the steady-state limit.",
        "type": "int", "default": 14, "min": 0, "max": 90,
    },
    {
        "key": "needs_review_failure_ratio", "category": ANTI_BAN, "label": "\"Needs Review\" Failure Ratio",
        "description": "If this fraction of an agent's recent attempts fail, it's flagged for review in the UI (soft warning, agent keeps working).",
        "type": "float", "default": 0.7, "min": 0.1, "max": 1.0,
    },
    {
        "key": "auto_pause_failure_ratio", "category": ANTI_BAN, "label": "Auto-Pause Failure Ratio",
        "description": "If this fraction of an agent's recent attempts fail, it's automatically set to Idle until a human re-activates it (hard circuit breaker).",
        "type": "float", "default": 0.9, "min": 0.1, "max": 1.0,
    },

    # --- Security & Login ---
    {
        "key": "login_max_failed_attempts", "category": SECURITY, "label": "Max Failed Login Attempts",
        "description": "Number of consecutive wrong passwords before an account is temporarily locked.",
        "type": "int", "default": 5, "min": 3, "max": 20,
    },
    {
        "key": "login_lockout_minutes", "category": SECURITY, "label": "Lockout Duration (minutes)",
        "description": "How long an account stays locked after too many failed attempts.",
        "type": "int", "default": 15, "min": 1, "max": 1440,
    },
    {
        "key": "access_token_expire_minutes", "category": SECURITY, "label": "Access Token Lifetime (minutes)",
        "description": "How long a login session's access token is valid before it's silently refreshed.",
        "type": "int", "default": 15, "min": 5, "max": 1440,
    },
    {
        "key": "refresh_token_expire_days", "category": SECURITY, "label": "Refresh Token Lifetime (days)",
        "description": "How long you can stay logged in without re-entering your password.",
        "type": "int", "default": 7, "min": 1, "max": 90,
    },
    {
        "key": "claim_token_expire_minutes", "category": SECURITY, "label": "Admin Claim Link Lifetime (minutes)",
        "description": "How long an emailed admin-claim link stays valid.",
        "type": "int", "default": 30, "min": 5, "max": 1440,
    },
    {
        "key": "reset_token_expire_minutes", "category": SECURITY, "label": "Password Reset Link Lifetime (minutes)",
        "description": "How long an emailed password-reset link stays valid.",
        "type": "int", "default": 30, "min": 5, "max": 1440,
    },
]

SETTINGS_BY_KEY = {s["key"]: s for s in SETTINGS_SCHEMA}
