"""
Pytest configuration file.

This file defines fixtures and hooks that are available to all tests in the project.
"""
import os


def pytest_configure(config):
    """
    Sets up the environment variables before test collection begins.
    This hook is called by pytest after command line options have been parsed
    and before any test collection is performed.
    """
    os.environ["ACS_CONNECTION_STRING"] = "mock_connection_string"
    os.environ["ACS_ENDPOINT"] = "https://mock.endpoint.azure.com"
    os.environ["SENDER_EMAIL"] = "sender@mock.com"
    os.environ["INPUT_BLOB_CONTAINER"] = "mock-input-container"
