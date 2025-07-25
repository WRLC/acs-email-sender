""" Unit tests for the acs_email_sender blob trigger. """
import unittest
import json
from unittest.mock import patch, MagicMock

import azure.functions as func

from src.acs_email_sender.blueprints.bp_send import acs_email_sender
from src.acs_email_sender.models.email_message import EmailMessage


# noinspection PyMethodMayBeStatic
class TestAcsEmailSenderBlueprint(unittest.TestCase):
    """Unit tests for the acs_email_sender blob trigger."""

    def setUp(self):
        """Set up a reusable valid payload for tests."""
        self.valid_payload = {
            "to": ["test@example.com"],
            "subject": "Hello World",
            "html": "<h1>Test</h1>",
            "plaintext": "Test"
        }

    def _create_mock_input_stream(self, data: dict | str) -> MagicMock:
        """Helper to create a mock InputStream from a dict or string."""
        if isinstance(data, dict):
            content_bytes = json.dumps(data).encode()
        else:
            content_bytes = data.encode()

        mock_stream = MagicMock(spec=func.InputStream)
        mock_stream.read.return_value = content_bytes
        mock_stream.name = "test-blob.json"
        return mock_stream

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_happy_path_sends_email(self, mock_email_service_class):
        """
        Verify that a valid blob results in a call to EmailService.send_email.
        """
        # Arrange
        mock_service_instance = mock_email_service_class.return_value
        mock_blob = self._create_mock_input_stream(self.valid_payload)

        # Act
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='INFO') as cm:
            acs_email_sender(mock_blob)
            self.assertIn("Received valid email request for: ['test@example.com']", cm.output[1])

        # Assert
        mock_email_service_class.assert_called_once()
        mock_service_instance.send_email.assert_called_once()
        called_with_arg = mock_service_instance.send_email.call_args.kwargs['email']
        self.assertIsInstance(called_with_arg, EmailMessage)
        self.assertEqual(called_with_arg.to, self.valid_payload['to'])

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_invalid_json_logs_error_and_returns(self, mock_email_service_class):
        """
        Verify that a blob with invalid JSON is caught, logged, and does not call the service.
        """
        # Arrange
        mock_blob = self._create_mock_input_stream("this is not json")

        # Act & Assert
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='ERROR') as cm:
            acs_email_sender(mock_blob)
            self.assertIn("Invalid JSON in blob 'test-blob.json'", cm.output[0])

        mock_email_service_class.assert_not_called()

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_pydantic_validation_error_logs_and_returns(self, mock_email_service_class):
        """
        Verify that a blob failing Pydantic validation is caught, logged, and does not call the service.
        """
        # Arrange
        invalid_payload = {"to": ["test@example.com"]}  # Missing 'subject'
        mock_blob = self._create_mock_input_stream(invalid_payload)

        # Act & Assert
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='ERROR') as cm:
            acs_email_sender(mock_blob)
            log_output = cm.output[0]
            self.assertIn("Invalid email message in blob 'test-blob.json'", log_output)
            self.assertIn("subject", log_output)
            self.assertIn("Field required", log_output)

        mock_email_service_class.assert_not_called()

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_email_service_exception_propagates(self, mock_email_service_class):
        """
        Verify that if the EmailService fails, the exception is propagated.
        """
        # Arrange
        mock_service_instance = mock_email_service_class.return_value
        expected_exception = Exception("ACS service is unavailable")
        mock_service_instance.send_email.side_effect = expected_exception
        mock_blob = self._create_mock_input_stream(self.valid_payload)

        # Act & Assert
        with self.assertRaises(Exception) as context:
            acs_email_sender(mock_blob)

        self.assertEqual(context.exception, expected_exception)
        mock_email_service_class.assert_called_once()
        mock_service_instance.send_email.assert_called_once()


if __name__ == '__main__':
    unittest.main()
