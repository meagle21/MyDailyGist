import boto3
from bs4 import BeautifulSoup
import json
from datetime import datetime

### GET TODAYS DATE
current_date_time = datetime.now()
formatted_date = current_date_time.strftime('%m_%d_%Y')

### ESTABLISH CONNECTION TO S3
json_file = json.load(open("aws_access.json"))[0]
s3_client = boto3.client(service_name = "s3", region_name = "us-east-2", 
                        aws_access_key_id = json_file["access_key"], aws_secret_access_key = json_file["secret_access_key"])

### GET THE DICTIONARY OF INTEREST FROM THE INTEREST JSON FILE 
parent_folder = "my-daily-gist-raw-data-warehouse-ohio"
interest_dict = json.load(open("interests_user_config.json"))[0]["InterestWebsites"]
interest_list = list(interest_dict.keys())
html_output = "<html>\n"
for interest in interest_list:
    for website in interest_dict[interest]:
        file_name = rf"{website}/feed_{formatted_date}.json"
        response = s3_client.get_object(Bucket = parent_folder, Key = file_name)
        if response["ResponseMetadata"]["HTTPStatusCode"] in [200, 201]:
            object_from_s3 = json.loads(response["Body"].read())
            for article in object_from_s3:
                tag_template = f"<a href = {article['Link']}>{article['Title']} ({article['tags']})</a><br>"
                html_output += tag_template
html_output += "</html>"
soup = BeautifulSoup(html_output, "html.parser").prettify()
s3_client.put_object(Bucket = "my-daily-gist-raw-data-warehouse-ohio", Key=f"GeneratedEmailTemplates/feed_{formatted_date}.html", Body=soup)

            

        

