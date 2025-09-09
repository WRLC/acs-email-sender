""" Configuration for Azure Function """
import os


def _get_required_env(var_name: str) -> str:
    """Gets a required environment variable or raises a ValueError."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: '{var_name}'")
    return value

ACS_CONNECTION_STRING_SETTING_NAME = "AzureWebJobsStorage"
ACS_CONNECTION_STRING = _get_required_env(ACS_CONNECTION_STRING_SETTING_NAME)
ACS_ENDPOINT = _get_required_env("ACS_ENDPOINT")
SENDER_EMAIL = _get_required_env("SENDER_EMAIL")
INPUT_MESSAGE_QUEUE = os.getenv("INPUT_MESSAGE_QUEUE", "")
INPUT_BLOB_CONTAINER = os.getenv("INPUT_BLOB_CONTAINER", "")
