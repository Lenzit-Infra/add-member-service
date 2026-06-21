from pydantic import BaseModel

class SettingUpdate(BaseModel):
    key: str
    value: str
