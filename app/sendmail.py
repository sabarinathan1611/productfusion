from __future__ import print_function
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import os
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_mail(subject, message, to_email):
    html_content = "<html><body><h1>{}</h1></body></html>".format(message)
    sender = {"name": "sabari", "email": os.getenv("EMAIL_SENDER")} 

    to = [{"email": to_email}]

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        html_content=html_content,
        sender=sender,
        subject=subject
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print(f"Exception when calling SMTPApi->send_transac_email: {e}\n")


send_mail("Test Subject", "This is a test message", "vsabarinathan1611@gmail.com")
