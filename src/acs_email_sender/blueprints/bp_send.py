""" Blueprints for queue trigger to send an email """
import logging

import azure.functions as func
from pydantic import ValidationError

from src.acs_email_sender.services.email_service import EmailService
from src.acs_email_sender.models.email_message import EmailMessage

logger = logging.getLogger(__name__)

bp = func.Blueprint()


@bp.queue_trigger(
    arg_name="msg",
    queue_name="%INPUT_QUEUE_NAME%",
    connection="AzureWebJobsStorage"
)
def acs_email_sender(msg: func.QueueMessage):
    """ Queue trigger to send an email """
    try:
        email_data = msg.get_json()
        email_message = EmailMessage.model_validate(email_data)
        logger.info(f"Received valid email request for: {email_message.to}")

    except ValidationError as e:
        logger.error(f"Invalid email message received. Validation errors: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to parse queue message: {e}")
        return

    email_service = EmailService()
    email_service.send_email(email=email_message)
