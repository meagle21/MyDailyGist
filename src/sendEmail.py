import json
import os
from datetime import datetime

import boto3
import pytz


def lambda_handler(event, context):
    bucket_name = os.environ["BUCKET_NAME"]
    interests_file = os.environ["INTERESTS_FILE_NAME"]
    region_name = os.environ["REGION_NAME"]
    interest_file_for_store = os.environ["INTEREST_TEMP_FILE_PATH"]
    email_templates_folder = os.environ["EMAIL_TEMPLATES_FOLDER"]
    current_date_time = datetime.utcnow().astimezone(pytz.timezone("US/Eastern"))
    formatted_date = current_date_time.strftime("%m_%d_%Y")
    s3_client = boto3.resource(service_name="s3", region_name=region_name)
    interest_response = s3_client.Bucket(bucket_name).download_file(
        interests_file, interest_file_for_store
    )
    interests_file = json.load(open(interest_file_for_store))[0]
    emails_and_interests = interests_file["UserInterests"]
    interests_list = list(emails_and_interests.keys())
    date_for_subject = current_date_time.strftime("%B %dth, %Y")
    if "1th" in date_for_subject and "11th" not in date_for_subject:
        date_for_subject = date_for_subject.replace("1th", "1st")
    elif "2th" in date_for_subject:
        date_for_subject = date_for_subject.replace("2th", "2nd")
    elif "3th" in date_for_subject:
        date_for_subject = date_for_subject.replace("3th", "3rd")
    for interest in interests_list:
        gist_interest_dict = {
            "Technology": "Technological",
            "Finance": "Financial",
            "Politics": "Political",
            "Science": "Scientific",
        }
        re_expressed_interest = gist_interest_dict[interest]
        in_mail_content = re_expressed_interest.lower()
        formatted_subject = f"My {re_expressed_interest} Digest - {date_for_subject}"
        user_emails = emails_and_interests[interest]
        file_name = rf"{email_templates_folder}/feed_{interest}_{formatted_date}.html"

        feed_response = s3_client.Bucket(bucket_name).download_file(
            file_name, rf"/tmp/feed_{interest}_{formatted_date}.html"
        )
        object_from_s3 = open(
            rf"/tmp/feed_{interest}_{formatted_date}.html", encoding="utf-8"
        ).read()
        html_content = str(object_from_s3)
        ses_client = boto3.client(service_name="ses", region_name=region_name)
        ses_client.send_email(
            Source=f"My{re_expressed_interest}Digest@www.mydailygist.com",
            Destination={"BccAddresses": user_emails},
            Message={
                "Subject": {"Data": formatted_subject},
                "Body": {
                    "Text": {"Charset": "UTF-8", "Data": "test"},
                    "Html": {"Charset": "UTF-8", "Data": html_content},
                },
            },
        )
    return {"statusCode": 200, "body": f"Successfully sent out emails."}
