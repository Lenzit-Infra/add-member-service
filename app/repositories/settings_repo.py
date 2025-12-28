# app/repositories/settings_repo.py
from sqlalchemy.orm import Session
from app.models.settings import SystemSetting

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
        """Sets default values if they don't exist."""
        defaults = {
            "worker_check_interval": "10",
            "batch_size": "5",
            "sleep_delay_min": "10",
            "sleep_delay_max": "30",
            "daily_limit_per_agent": "50"
        }
        for k, v in defaults.items():
            if not self.get_setting(k):
                self.set_setting(k, v, "System Default")