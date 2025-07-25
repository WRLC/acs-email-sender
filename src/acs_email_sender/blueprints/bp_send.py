""" Blueprints for blob trigger to send an email """
import logging
import json

import azure.functions as func
from pydantic import ValidationError

from src.acs_email_sender.services.email_service import EmailService
from src.acs_email_sender.models.email_message import EmailMessage

logger = logging.getLogger(__name__)

bp = func.Blueprint()


@bp.blob_trigger(
    arg_name="inputblob",
    # The path should include the container name from settings and a placeholder for the blob name.
    path="%INPUT_BLOB_CONTAINER%/{name}",
    connection="AzureWebJobsStorage"
)
def acs_email_sender(inputblob: func.InputStream):
    """ Blob trigger to send an email """
    logger.info(f"Processing blob: {inputblob.name}")
    try:
        blob_content_bytes = inputblob.read()

        email_data = json.loads(blob_content_bytes)
        email_message = EmailMessage.model_validate(email_data)
        logger.info(f"Received valid email request for: {email_message.to}")

    except ValidationError as e:
        logger.error(f"Invalid email message in blob '{inputblob.name}'. Validation errors: {e}")
        # A validation error means the data is bad, so we should not retry.
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in blob '{inputblob.name}': {e}")
        # Bad JSON also should not be retried.
        return
    except Exception as e:
        logger.error(f"Failed to process blob '{inputblob.name}': {e}")
        # Re-raise the exception to allow the Functions runtime to handle retries for transient errors.
        raise

    email_service = EmailService()
    email_service.send_email(email=email_message)
