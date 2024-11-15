# lambda_functions/verify_email.py
import os
import json
import boto3
import psycopg2
from datetime import datetime, timedelta
import uuid

ses_client = boto3.client('ses')

RDS_HOST = os.getenv("RDS_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    user_id = message['user_id']
    email = message['email']
    token = str(uuid.uuid4())
    expiry_time = datetime.utcnow() + timedelta(minutes=2)

    # Database Connection
    conn = psycopg2.connect(host=RDS_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO email_verifications (user_id, token, expires_at) VALUES (%s, %s, %s)", (user_id, token, expiry_time))
    conn.commit()
    cursor.close()
    conn.close()

    # Send Email
    verification_link = f"https://yourapp.com/verify?token={token}"
    email_subject = "Verify Your Email"
    email_body = f"Click this link to verify your email: {verification_link}. This link expires in 2 minutes."

    ses_client.send_email(
        Source="no-reply@harshshahjigar.me",
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': email_subject},
            'Body': {'Text': {'Data': email_body}}
        }
    )

    return {"statusCode": 200, "body": "Verification email sent."}
