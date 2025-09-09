""" Azure Function """
import azure.functions as func

from acs_email_sender.blueprints.bp_send import bp as bp_send

app = func.FunctionApp()

app.register_blueprint(bp_send)
