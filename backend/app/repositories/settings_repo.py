# app/repositories/settings_repo.py
from sqlalchemy.orm import Session
from app.models.settings import SystemSetting
from app.core.settings_schema import SETTINGS_SCHEMA
from app.core import config

ADMIN_EMAILS_KEY = "admin_emails"


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default_value: str = None) -> str:
        """Fetch a setting value by key."""
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            return setting.value
        return default_value

    def set_setting(self, key: str, value: str, description: str = None):
        """Create or Update a setting."""
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSetting(key=key, value=str(value), description=description)
            self.db.add(setting)
        self.db.commit()
        return setting

    def initialize_defaults(self):
        """Seeds every schema-defined tunable, plus the admin email allowlist
        (from .env ADMIN_EMAILS), if they don't already exist."""
        for s in SETTINGS_SCHEMA:
            if not self.get_setting(s["key"]):
                self.set_setting(s["key"], s["default"], s["description"])

        if not self.get_setting(ADMIN_EMAILS_KEY):
            self.set_setting(
                ADMIN_EMAILS_KEY,
                ",".join(config.ADMIN_EMAILS),
                "Admin allowlist — seeded once from .env ADMIN_EMAILS, managed live from here after.",
            )

    # --- Admin email allowlist (the live source of truth; .env is only the first-run seed) ---

    def get_admin_emails(self) -> list:
        raw = self.get_setting(ADMIN_EMAILS_KEY, "")
        return [e.strip().lower() for e in raw.split(",") if e.strip()]

    def add_admin_email(self, email: str) -> list:
        email = email.strip().lower()
        emails = self.get_admin_emails()
        if email not in emails:
            emails.append(email)
            self.set_setting(ADMIN_EMAILS_KEY, ",".join(emails))
        return emails

    def remove_admin_email(self, email: str) -> list:
        email = email.strip().lower()
        emails = self.get_admin_emails()
        if email in emails and len(emails) <= 1:
            raise ValueError("Can't remove the last admin email — at least one must remain so the panel stays claimable.")
        emails = [e for e in emails if e != email]
        self.set_setting(ADMIN_EMAILS_KEY, ",".join(emails))
        return emails
