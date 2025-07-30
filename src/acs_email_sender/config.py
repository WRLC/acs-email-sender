""" Configuration for Azure Function """
import os


def _get_required_env(var_name: str) -> str:
    """Gets a required environment variable or raises a ValueError."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: '{var_name}'")
    return value


ACS_CONNECTION_STRING = _get_required_env("ACS_CONNECTION_STRING")
ACS_ENDPOINT = _get_required_env("ACS_ENDPOINT")
SENDER_EMAIL = _get_required_env("SENDER_EMAIL")
INPUT_BLOB_CONTAINER = _get_required_env("INPUT_BLOB_CONTAINER")
