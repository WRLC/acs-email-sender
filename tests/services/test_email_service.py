""" Unit tests for the EmailService class. """
import unittest
from unittest.mock import patch, MagicMock

from azure.core.exceptions import HttpResponseError

from acs_email_sender.services.email_service import EmailService
from acs_email_sender.models.email_message import EmailMessage


# noinspection PyUnusedLocal
class TestEmailService(unittest.TestCase):
    """Unit tests for the EmailService class."""

    def setUp(self):
        """Set up a reusable Pydantic email message for all tests."""
        self.email_message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Subject",
            html="<h1>Test HTML</h1>",
            plaintext="Test Plaintext",
            cc=["cc.recipient@example.com"]
        )

    @patch('src.acs_email_sender.services.email_service.DefaultAzureCredential')
    @patch('src.acs_email_sender.services.email_service.EmailClient')
    @patch('src.acs_email_sender.services.email_service.config')
    def test_create_client_with_connection_string(self, mock_config, mock_email_client, mock_credential):
        """
        Verify EmailClient is created using a connection string when provided.
        """
        # Arrange
        mock_config.ACS_CONNECTION_STRING = "test_connection_string"
        mock_config.ACS_ENDPOINT = None  # Ensure endpoint is not used

        service = EmailService()

        # Act
        client = service.create_email_client()

        # Assert
        mock_email_client.from_connection_string.assert_called_once_with("test_connection_string")
        # Ensure the constructor wasn't called directly with an endpoint
        mock_email_client.assert_not_called()
        self.assertEqual(client, mock_email_client.from_connection_string.return_value)

    @patch('src.acs_email_sender.services.email_service.DefaultAzureCredential')
    @patch('src.acs_email_sender.services.email_service.EmailClient')
    @patch('src.acs_email_sender.services.email_service.config')
    def test_create_client_with_endpoint(self, mock_config, mock_email_client, mock_credential):
        """
        Verify EmailClient is created using an endpoint and credential when no connection string is present.
        """
        # Arrange
        mock_config.ACS_CONNECTION_STRING = None
        mock_config.ACS_ENDPOINT = "test_endpoint"

        # Mock the credential instance that will be created
        mock_cred_instance = mock_credential.return_value
        service = EmailService()

        # Act
        client = service.create_email_client()

        # Assert
        mock_email_client.from_connection_string.assert_not_called()
        mock_email_client.assert_called_once_with(endpoint="test_endpoint", credential=mock_cred_instance)
        self.assertEqual(client, mock_email_client.return_value)

    @patch('src.acs_email_sender.services.email_service.EmailService.create_email_client')
    @patch('src.acs_email_sender.services.email_service.config')
    def test_send_email_success(self, mock_config, mock_create_client):
        """
        Test the successful path of sending an email.
        """
        # Arrange
        mock_config.SENDER_EMAIL = "sender@example.com"

        # Mock the poller and its result for a successful operation
        mock_poller = MagicMock()
        mock_poller.result.return_value = {"status": "Succeeded", "id": "test-message-id"}

        # Mock the client instance and its begin_send method
        mock_client_instance = MagicMock()
        mock_client_instance.begin_send.return_value = mock_poller
        mock_create_client.return_value = mock_client_instance

        service = EmailService()

        # Act
        service.send_email(self.email_message)

        # Assert
        # 1. Check that the client was created
        mock_create_client.assert_called_once()

        # 2. Check that begin_send was called with the correctly structured message
        expected_message = {
            "content": {
                "subject": "Test Subject",
                "html": "<h1>Test HTML</h1>",
                "plainText": "Test Plaintext"
            },
            "recipients": {
                "to": [{"address": "recipient@example.com"}],
                "cc": [{"address": "cc.recipient@example.com"}]
            },
            "senderAddress": "sender@example.com",
        }
        mock_client_instance.begin_send.assert_called_once_with(expected_message)

        # 3. Check that the poller's result was retrieved
        mock_poller.result.assert_called_once()

    @patch('src.acs_email_sender.services.email_service.EmailService.create_email_client')
    @patch('src.acs_email_sender.services.email_service.config')
    def test_send_email_acs_failure_status(self, mock_config, mock_create_client):
        """
        Test the failure path where ACS returns a non-successful status.
        """
        # Arrange
        mock_config.SENDER_EMAIL = "sender@example.com"

        mock_poller = MagicMock()
        mock_poller.result.return_value = {"status": "Failed", "id": "failed-id", "error": "Invalid recipient"}

        mock_client_instance = MagicMock()
        mock_client_instance.begin_send.return_value = mock_poller
        mock_create_client.return_value = mock_client_instance

        service = EmailService()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            service.send_email(self.email_message)

        self.assertIn("ACS Email send failed with status: Failed", str(context.exception))
        mock_client_instance.begin_send.assert_called_once()
        mock_poller.result.assert_called_once()

    @patch('src.acs_email_sender.services.email_service.EmailService.create_email_client')
    @patch('src.acs_email_sender.services.email_service.config')
    def test_send_email_sdk_exception(self, mock_config, mock_create_client):
        """
        Test the failure path where the Azure SDK itself raises an exception.
        """
        # Arrange
        mock_config.SENDER_EMAIL = "sender@example.com"

        mock_client_instance = MagicMock()
        # Configure the mock to raise an Azure-specific error on begin_send
        mock_client_instance.begin_send.side_effect = HttpResponseError("SDK network error")
        mock_create_client.return_value = mock_client_instance

        service = EmailService()

        # Act & Assert
        with self.assertRaises(HttpResponseError):
            service.send_email(self.email_message)

        mock_client_instance.begin_send.assert_called_once()


if __name__ == '__main__':
    unittest.main()
