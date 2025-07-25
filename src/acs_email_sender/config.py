""" Configuration for Azure Function """
import os

ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_ENDPOINT = os.getenv("ACS_ENDPOINT")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
