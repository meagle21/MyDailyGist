import json
import os
from datetime import datetime

import boto3
from bs4 import BeautifulSoup


def lambda_handler(event, context):
    ### GET TODAYS DATE
    current_date_time = datetime.now()
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
        sub_interests = interest_storage_file["InterestTags"][interest]
        tags_for_sorting = {}
        for website in interest_dict[interest]:
            file_name = rf"{website}/feed_{formatted_date}.json"
            temp_file_store_website = rf"/tmp/{file_name}".replace(f"/{website}", "")
            response = s3.Bucket(bucket_name).download_file(
                file_name, temp_file_store_website
            )
            object_from_s3 = json.load(open(temp_file_store_website))
            for article in object_from_s3:
                interest_level = 0
                tags = article["Tags"].lower()
                for sub_interest in sub_interests:
                    if sub_interest in tags:
                        interest_level += 1
                if interest_level > 0:
                    a_tag_template = (
                        f"<a href = {article['Link']}>{article['Title']}</a><br>"
                    )
                    tags_for_sorting[a_tag_template] = interest_level
        tags_sorted = dict(
            sorted(tags_for_sorting.items(), key=lambda item: item[1], reverse=True)
        )
        tags_sorted_as_list = list(tags_sorted.keys())[:15]
        for i in range(len(tags_sorted_as_list)):
            tag = tags_sorted_as_list[i]
            if i == 0:
                for article in object_from_s3:
                    if article["Title"] in tag:
                        html_output += f"<p>{article['Summary']}</p>"
            else:
                html_output += tag
        html_output += "</body></html>"
        soup = BeautifulSoup(html_output, "html.parser").prettify()
        s3.Bucket(bucket_name).put_object(
            Key=f"GeneratedEmailTemplates/feed_{interest}_{formatted_date}.html",
            Body=soup,
        )
    return {"statusCode": 200, "body": f"Succesfully uploaded htmls to S3."}
