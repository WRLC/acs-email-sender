""" Client functions for ACS """
import logging
from typing import Any, MutableMapping

from azure.communication.email import EmailClient
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.core.polling import LROPoller
from azure.identity import DefaultAzureCredential

import src.acs_email_sender.config as config
from src.acs_email_sender.models.email_message import EmailMessage

logger = logging.getLogger(__name__)


class EmailService:
    """ Client functions for ACS """

    def __init__(self):
        self.connection_string: str | None = config.ACS_CONNECTION_STRING
        self.endpoint: str | None = config.ACS_ENDPOINT
        self.credential: DefaultAzureCredential = DefaultAzureCredential()

    def send_email(self, email: EmailMessage):
        """
        Send an email to the specified recipients using a validated EmailMessage object.

        Args:
            email (EmailMessage): A Pydantic object containing all email details.
        """
        to_recipients = [{"address": addr} for addr in email.to]
        cc_recipients = [{"address": addr} for addr in email.cc] if email.cc else []

        client: EmailClient = self.create_email_client()

        message: dict[str, Any] = {
            "content": {
                "subject": email.subject,
                "html": email.html,
                "plainText": email.plaintext
            },
            "recipients": {
                "to": to_recipients,
                "cc": cc_recipients
            },
            "senderAddress": config.SENDER_EMAIL,
        }
        logger.debug(f"Message: {message}")

        try:
            logger.info("Sending email...")
            poller: LROPoller[MutableMapping[str, Any]] = client.begin_send(message)

            result = poller.result()
            logger.debug(f"Result: {result}")
            logger.info("ACS send poller finished.")

            status: str | None = result.get("status") if isinstance(result, dict) else None
            logger.debug(f"Status: {status}")

            message_id: str | None = result.get("id") if isinstance(result, dict) else None
            logger.debug(f"Message ID: {message_id}")

            if status and status.lower() == "succeeded":
                logger.info(f"Successfully sent email via ACS. Message ID: {message_id}")
            else:
                error_details = result.get("error", {}) if isinstance(result, dict) else result
                logger.error(
                    f"ACS Email send finished with status: {status}. Message ID: {message_id}. Error Details: "
                    f"{error_details}"
                )
                raise Exception(f"ACS Email send failed with status: {status}.")

        except (HttpResponseError, ServiceRequestError) as acs_sdk_err:
            logger.exception(f" Azure SDK Error sending email via ACS: {acs_sdk_err}")
            raise acs_sdk_err
        except Exception as email_err:
            logger.exception(f"Failed to send email via ACS: {email_err}")
            raise email_err

    def create_email_client(self) -> EmailClient:
        """
        Create an email client using the Azure Communication Service (ACS) connection string or endpoint.

        Returns:
            EmailClient: The initialized email client.
        """
        if self.connection_string:
            logger.debug("Using ACS Connection String.")
            email_client: EmailClient = EmailClient.from_connection_string(self.connection_string)
        else:
            logger.debug("Using ACS Endpoint and DefaultAzureCredential.")
            # noinspection PyTypeChecker
            email_client: EmailClient = EmailClient(endpoint=self.endpoint, credential=self.credential)

        return email_client
