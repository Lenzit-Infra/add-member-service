# app/core/permissions.py
"""
Single source of truth for the RBAC model. Three fixed roles:
- admin: implicitly has everything (PERMISSION_CATALOG + FIXED_ADMIN_ONLY).
  Never stored/edited — hardcoded so nobody can lock the system out of itself.
- operator / viewer: their permission sets are configurable (stored in
  SystemSetting via SettingsRepository.get/set_role_permissions), seeded from
  DEFAULT_ROLE_PERMISSIONS below.

Being logged in already implies "view" everything — there are deliberately
no separate view permissions. Only mutating actions are gated.
"""

ROLES = ["admin", "operator", "viewer"]

PERMISSION_CATALOG = [
    {"key": "orders.manage", "label": "Manage Orders", "description": "Pause, resume, cancel, or delete orders."},
    {"key": "agents.manage", "label": "Manage Agents", "description": "Add, activate/deactivate, ban, or delete agents."},
    {"key": "settings.manage", "label": "Manage Settings", "description": "Change Worker/Anti-Ban/Security tunables on the Settings page."},
]
PERMISSION_KEYS = {p["key"] for p in PERMISSION_CATALOG}

# Never editable via the UI, never assignable to operator/viewer — hardcoded
# admin-only to prevent privilege escalation or an accidental self-lockout.
FIXED_ADMIN_ONLY = {"users.manage", "roles.manage", "admin_emails.manage"}

DEFAULT_ROLE_PERMISSIONS = {
    "operator": {"orders.manage", "agents.manage"},
    "viewer": set(),
}


def role_has_permission(role: str, permission: str, granted_permissions: set) -> bool:
    """`granted_permissions` is whatever SettingsRepository.get_role_permissions(role)
    returned — irrelevant for admin, which always passes."""
    if role == "admin":
        return True
    if permission in FIXED_ADMIN_ONLY:
        return False
    return permission in granted_permissions
