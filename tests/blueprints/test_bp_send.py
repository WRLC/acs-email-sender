import unittest
from unittest.mock import patch, MagicMock

# The function we are testing
from src.acs_email_sender.blueprints.bp_send import acs_email_sender
from src.acs_email_sender.models.email_message import EmailMessage


class TestAcsEmailSenderBlueprint(unittest.TestCase):
    """Unit tests for the acs_email_sender function trigger."""

    def setUp(self):
        """Set up a reusable valid payload for tests."""
        self.valid_payload = {
            "to": ["test@example.com"],
            "subject": "Hello World",
            "html": "<h1>Test</h1>",
            "plaintext": "Test"
        }

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_happy_path_sends_email(self, mock_email_service_class):
        """
        Verify that a valid queue message results in a call to EmailService.send_email.
        """
        # Arrange
        # Mock the EmailService instance that will be created
        mock_service_instance = mock_email_service_class.return_value

        # Create a mock QueueMessage that returns our valid payload
        mock_msg = MagicMock()
        mock_msg.get_json.return_value = self.valid_payload

        # Act
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='INFO') as cm:
            acs_email_sender(mock_msg)
            # Assert that an info log was created for the valid request
            self.assertIn("Received valid email request for: ['test@example.com']", cm.output[0])

        # Assert
        # 1. EmailService was instantiated
        mock_email_service_class.assert_called_once()

        # 2. send_email was called on the instance
        mock_service_instance.send_email.assert_called_once()

        # 3. The 'email' keyword argument passed to send_email is an EmailMessage instance
        #    with the correct data.
        called_with_arg = mock_service_instance.send_email.call_args.kwargs['email']
        self.assertIsInstance(called_with_arg, EmailMessage)
        self.assertEqual(called_with_arg.to, self.valid_payload['to'])
        self.assertEqual(called_with_arg.subject, self.valid_payload['subject'])

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_invalid_json_logs_error_and_returns(self, mock_email_service_class):
        """
        Verify that a message with invalid JSON is caught, logged, and does not call the service.
        """
        # Arrange
        mock_msg = MagicMock()
        # Configure the mock to simulate a JSON parsing error
        mock_msg.get_json.side_effect = ValueError("Invalid JSON format")

        # Act & Assert
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='ERROR') as cm:
            acs_email_sender(mock_msg)
            self.assertIn("Failed to parse queue message: Invalid JSON format", cm.output[0])

        # Ensure the email service was never instantiated or called
        mock_email_service_class.assert_not_called()

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_pydantic_validation_error_logs_and_returns(self, mock_email_service_class):
        """
        Verify that a message failing Pydantic validation is caught, logged, and does not call the service.
        """
        # Arrange
        invalid_payload = {"to": ["test@example.com"]}  # Missing required 'subject' field
        mock_msg = MagicMock()
        mock_msg.get_json.return_value = invalid_payload

        # Act & Assert
        with self.assertLogs('src.acs_email_sender.blueprints.bp_send', level='ERROR') as cm:
            acs_email_sender(mock_msg)
            log_output = cm.output[0]
            self.assertIn("Invalid email message received. Validation errors:", log_output)
            # Check for details from the Pydantic error message
            self.assertIn("subject", log_output)
            self.assertIn("Field required", log_output)

        # Ensure the email service was never instantiated or called
        mock_email_service_class.assert_not_called()

    @patch('src.acs_email_sender.blueprints.bp_send.EmailService')
    def test_email_service_exception_propagates(self, mock_email_service_class):
        """
        Verify that if the EmailService fails, the exception is not caught, allowing for retries.
        """
        # Arrange
        # Mock the EmailService to raise an exception when send_email is called
        mock_service_instance = mock_email_service_class.return_value
        expected_exception = Exception("ACS service is unavailable")
        mock_service_instance.send_email.side_effect = expected_exception

        mock_msg = MagicMock()
        mock_msg.get_json.return_value = self.valid_payload

        # Act & Assert
        # The exception should propagate out of the function call
        with self.assertRaises(Exception) as context:
            acs_email_sender(mock_msg)

        self.assertEqual(context.exception, expected_exception)
        mock_email_service_class.assert_called_once()
        mock_service_instance.send_email.assert_called_once()


if __name__ == '__main__':
    unittest.main()
