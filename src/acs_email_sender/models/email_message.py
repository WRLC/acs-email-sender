"""Pydantic models for data validation and schema definition."""
from pydantic import BaseModel, Field

class EmailMessage(BaseModel):
    """
    Represents the structure of an email message from the queue.
    """
    to: list[str]
    subject: str
    html: str | None = None
    # The incoming JSON might use 'plaintext', but the ACS SDK expects 'plainText'.
    # We'll define our model with 'plaintext' and handle the mapping in the service.
    plaintext: str | None = None
    cc: list[str] | None = None
