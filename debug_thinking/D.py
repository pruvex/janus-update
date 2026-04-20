# D.py - Shared Config Module (breaks the circular dependency)
# This module holds shared configuration/data that A, B, C can all import
# without creating circular dependencies

SHARED_CONFIG = {
    "app_name": "Diamond-OS",
    "version": "3.3",
    "debug_mode": True
}

def get_config(key):
    return SHARED_CONFIG.get(key)

def set_config(key, value):
    SHARED_CONFIG[key] = value
