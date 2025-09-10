""" Blueprints for blob trigger to send an email """
import logging
import json

import azure.functions as func
from pydantic import ValidationError
from wrlc_azure_storage_service import StorageService  # type: ignore

from acs_email_sender.config import INPUT_MESSAGE_QUEUE, STORAGE_CONNECTION_STRING_SETTING_NAME, INPUT_BLOB_CONTAINER
from acs_email_sender.services.email_service import EmailService
from acs_email_sender.models.email_message import EmailMessage

logger = logging.getLogger(__name__)

bp = func.Blueprint()


@bp.queue_trigger(
    arg_name="inputmsg",
    queue_name=INPUT_MESSAGE_QUEUE,
    connection=STORAGE_CONNECTION_STRING_SETTING_NAME
)
def acs_email_sender(inputmsg: func.QueueMessage):
    """ Queue trigger to send an email """
    message_data = json.loads(inputmsg.get_body())

    blob_name = message_data.get("blob_name")

    storage_service = StorageService()

    try:
        blob_content: dict | list = storage_service.download_blob_as_json(
            container_name=INPUT_BLOB_CONTAINER,
            blob_name=blob_name
        )
        email_message = EmailMessage.model_validate(blob_content)
        logger.info(f"Received valid email request for: {email_message.to}")

    except ValidationError as e:
        logger.error(f"Invalid email message in blob '{blob_name}'. Validation errors: {e}")
        # A validation error means the data is bad, so we should not retry.
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in blob '{blob_name}': {e}")
        # Bad JSON also should not be retried.
        return
    except Exception as e:
        logger.error(f"Failed to process blob '{blob_name}': {e}")
        # Re-raise the exception to allow the Functions runtime to handle retries for transient errors.
        raise

    email_service = EmailService()
    email_service.send_email(email=email_message)
