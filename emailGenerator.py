import json
import os
import random
from datetime import datetime

import boto3
import pytz
from bs4 import BeautifulSoup


def lambda_handler(event, context):
    ### GET TODAYS DATE
    current_date_time = datetime.utcnow().astimezone(pytz.timezone("US/Eastern"))
    formatted_date = current_date_time.strftime("%m_%d_%Y")
    interests_file, bucket_name, region_name = (
        os.environ["INTERESTS_FILE_NAME"],
        os.environ["BUCKET_NAME"],
        os.environ["REGION_NAME"],
    )
    ### ESTABLISH CONNECTION TO S3
    s3 = boto3.resource(service_name="s3", region_name=region_name)

    ### GET THE DICTIONARY OF INTEREST FROM THE INTEREST JSON FILE
    temp_file_store = f"/tmp/{interests_file}"
    response = s3.Bucket(bucket_name).download_file(interests_file, temp_file_store)
    interest_storage_file = json.load(open(temp_file_store))[0]
    interest_dict = interest_storage_file["InterestWebsites"]
    interest_list = list(interest_dict.keys())
    html_output = "<html><body><header>Good morning!</header>"
    for interest in interest_list:
        tags = []
        for website in interest_dict[interest]:
            file_name = rf"{website}/feed_{formatted_date}.json"
            temp_file_store_website = rf"/tmp/{file_name}".replace(f"/{website}", "")
            response = s3.Bucket(bucket_name).download_file(
                file_name, temp_file_store_website
            )
            object_from_s3 = json.load(open(temp_file_store_website))
            for article in object_from_s3:
                a_tag_template = (
                    f"<a href = {article['Link']}>{article['Title']}, {website}</a><br>"
                )
                tags.append(a_tag_template)
        random_indexes = random.sample(range(len(tags)), 15)
        for i in random_indexes:
            html_output += random_indexes[i]
        html_output += "</body></html>"
        soup = BeautifulSoup(html_output, "html.parser").prettify()
        s3.Bucket(bucket_name).put_object(
            Key=f"GeneratedEmailTemplates/feed_{interest}_{formatted_date}.html",
            Body=soup,
        )
    return {"statusCode": 200, "body": f"Succesfully uploaded htmls to S3."}
