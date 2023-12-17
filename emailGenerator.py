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
    interest_dict = json.load(open(temp_file_store))[0]["InterestWebsites"]
    interest_list = list(interest_dict.keys())
    html_output = "<html>\n"
    for interest in interest_list:
        for website in interest_dict[interest]:
            file_name = rf"{website}/feed_{formatted_date}.json"
            temp_file_store_website = f"/tmp/{file_name}".replace(f"/{website}", "")
            response = s3.Bucket(bucket_name).download_file(file_name, temp_file_store_website)
            if response["ResponseMetadata"]["HTTPStatusCode"] in [200, 201]:
                list_of_files = os.listdir("tmp")
                '''object_from_s3 = json.loads(open(temp_file_store))[0]
                for article in object_from_s3:
                    tag_template = f"<a href = {article['Link']}>{article['Title']} ({article['tags']})</a><br>"
                    html_output += tag_template
    html_output += "</html>"
    soup = BeautifulSoup(html_output, "html.parser").prettify()
    s3.Bucket(bucket_name).put_object(Key=f"GeneratedEmailTemplates/feed_{formatted_date}.html", Body=soup)'''
    return {'statusCode': 200, 'body': list_of_files}
        
#f"Succesfully uploaded feed_{formatted_date}.html to S3."