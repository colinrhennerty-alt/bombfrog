import os


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def env_flag(name, default=False):
    """Parse a boolean-ish environment variable ("1"/"true"/"yes"/"on")."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")
