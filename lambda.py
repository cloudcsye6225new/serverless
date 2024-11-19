import os
import json
from datetime import datetime
import requests  # For sending email via SendGrid

# Environment Variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DOMAIN = os.getenv("DOMAIN")
RDS_HOST = os.getenv("RDS_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
sender= "demo.harshshahjigar.me"


# def get_db_connection():
#     """
#     Creates and returns a database connection using pg8000.
#     """
#     return pg8000.connect(
#         host=RDS_HOST,
#         port=int(DB_PORT),
#         database=DB_NAME,
#         user=DB_USERNAME,
#         password=DB_PASSWORD
#     )


# def get_current_time():
#     """
#     Returns the current UTC time.
#     """
#     return datetime.utcnow()


# def update_user_verification_timestamp(email):
#     """
#     Update the `expires_at` field for the given email in the database with the current UTC time.
#     """
#     conn = None
#     cursor = None
#     current_time = get_current_time()  # Get the current UTC time

#     try:
#         conn = get_db_connection()  # Connect to the RDS database
#         cursor = conn.cursor()

#         # SQL query to update the expires_at field
#         query = """
#             UPDATE public."AppUsers"
#             SET "expires_at" = %s
#             WHERE email = %s;
#         """
#         cursor.execute(query, (current_time, email))
#         conn.commit()
#         print(f"Expires_at field for {email} updated to {current_time}.")
#     except Exception as e:
#         print(f"Database error while updating expires_at field: {e}")
#         raise
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()


def lambda_handler(event, context):
    """
    Lambda handler function to send a verification email and update the database timestamp.
    """
    try:
        # Parse the SNS message
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        email = sns_message['email']
        token = sns_message['token']
        base_url = DOMAIN
        print(f"Email: {email}, Token: {token}, Base URL: {DOMAIN}")

        # Construct the verification URL
        verification_url = f"{DOMAIN}/verify?user={email}&token={token}"

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
            "from": {"email": f"no-reply@{sender}"},
            "content": [
                {"type": "text/plain", "value": email_body},
                {"type": "text/html", "value": email_html}
            ]
        }

        # Send the email using SendGrid
        sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(sendgrid_url, headers=headers, json=msg)
        if response.status_code != 202:
            print(f"SendGrid response: {response.status_code}, {response.text}")
            raise Exception(f"Failed to send email: {response.status_code}, {response.text}")
        print(f"Verification email sent to {email} successfully.")

        # Update the verification email sent timestamp in the database
        update_user_verification_timestamp(email)

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
