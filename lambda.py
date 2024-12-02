import os
import json
import pg8000
from datetime import datetime
import requests  # For sending email via SendGrid
import boto3



def get_secret(secret_name, region_name):
    """
    Retrieve the secret value from AWS Secrets Manager.
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = response["SecretString"]
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        raise e


def lambda_handler(event, context):
    """
    Lambda handler function to send a verification email and update the database timestamp.
    """
    try:
        # Parse the SNS message
        
        



        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        email = sns_message['email']
        token = sns_message['token']
        secret_name = sns_message['secret_name']
        region = sns_message['Region']
        secrets = get_secret(secret_name, region)
        base_url = secrets['domain']
        sendgridapi = secrets['sendgridapi']
        print(f"Email: {email}, Token: {token}, Base URL: {base_url}, sndgrid:{sendgridapi}")

        # Construct the verification URL
        verification_url = f"{base_url}/verify?user={email}&token={token}"

        # Construct the email details
        email_subject = "Verify Your Email"
        email_body = f"Please verify your email by clicking the link: {verification_url}"
        email_html = f"""
            <p>Please verify your email by clicking 
            <a href="{verification_url}">this link</a>. The link will expire in 2 minutes.</p>
        """
        msg = {
            "personalizations": [
                {
                    "to": [{"email": email}],
                    "subject": email_subject
                }
            ],
            "from": {"email": f"no-reply@{base_url}"},
            "content": [
                {"type": "text/plain", "value": email_body},
                {"type": "text/html", "value": email_html}
            ]
        }

        # Send the email using SendGrid
        sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {sendgridapi}",
            "Content-Type": "application/json"
        }

        response = requests.post(sendgrid_url, headers=headers, json=msg)
        if response.status_code != 202:
            print(f"SendGrid response: {response.status_code}, {response.text}")
            raise Exception(f"Failed to send email: {response.status_code}, {response.text}")
        print(f"Verification email sent to {email} successfully.")


        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Verification email sent to {email} and timestamp updated."})
        }

    except Exception as e:
        print(f"Error: {e}")
        # Return error response
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to send verification email or log it in the database", "error": str(e)})
        }
