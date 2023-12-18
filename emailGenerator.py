import boto3
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

def lambda_handler(event, context):
    ### GET TODAYS DATE
    current_date_time = datetime.now()
    formatted_date = current_date_time.strftime('%m_%d_%Y')

    ### ESTABLISH CONNECTION TO S3
    s3 = boto3.resource(service_name = "s3", region_name = "us-east-2")

    ### GET THE DICTIONARY OF INTEREST FROM THE INTEREST JSON FILE 
    associated_files = json.load(open("associatedFiles.json"))[0]
    bucket_name, interests_file = associated_files["BucketName"], associated_files["InterestsFile"]
    temp_file_store = f"/tmp/{interests_file}"
    response = s3.Bucket(bucket_name).download_file(interests_file, temp_file_store)
    interest_storage_file = json.load(open(temp_file_store))[0]
    interest_dict = interest_storage_file["InterestWebsites"]
    interest_list = list(interest_dict.keys())
    html_output = "<html><body>"
    for interest in interest_list:
        sub_interests = interest_storage_file["InterestTags"][interest]
        tags_for_sorting = {}
        for website in interest_dict[interest]:
            file_name = rf"{website}/feed_{interest}_{formatted_date}.json"
            temp_file_store_website = f"/tmp/{file_name}".replace(f"/{website}", "")
            response = s3.Bucket(bucket_name).download_file(file_name, temp_file_store_website)
            object_from_s3 = json.load(open(temp_file_store_website))
            for article in object_from_s3:
                interest_level = 0
                tags = article["tags"].lower()
                for sub_interest in sub_interests:
                    if(sub_interest in tags):
                        interest_level += 1
                if(interest_level > 0):
                    a_tag_template = f"<a href = {article['Link']}>{article['Title']}</a><br>"
                    tags_for_sorting[a_tag_template] = interest_level
        tags_sorted = dict(sorted(tags_for_sorting.items(), key=lambda item: item[1], reverse=True))
        tags_sorted_as_list = list(tags_sorted.keys())
        for tag in tags_sorted_as_list[:15]:
            html_output += tag
        html_output += "</body></html>"
        soup = BeautifulSoup(html_output, "html.parser").prettify()
        s3.Bucket(bucket_name).put_object(Key=f"GeneratedEmailTemplates/feed_{interest}_{formatted_date}.html", Body=soup)
    return {'statusCode': 200, 'body': f"Succesfully uploaded htmls to S3."}