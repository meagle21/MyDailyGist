import feedparser
import json
import boto3
from datetime import datetime
import os

def lambda_handler(event, context):
    nyt_feed_url = r"https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
    feed = feedparser.parse(nyt_feed_url).entries #get the entries in the feed
    associated_file_name = os.environ['ASSOCIATED_FILES']
    associated_files = json.load(open(associated_file_name))[0]
    bucket_name = associated_files["BucketName"]
    nyt_feed = []
    for entry in feed:
        template_dict = {"Title" : "", "Author" : "", "Link" : "", "Published_Parsed" : "", "Summary" : "", "Thumbnail" : ""} #template dict to store all the entry info
        template_dict['Title'] = entry["title"] #put title in dictionary
        authors_as_string = '' #empty string to store a more well formatted author list
        try:
            for author in entry["authors"]: #for each author name in the list of authors
                authors_as_string += f"{author['name']}, " #get name from dictionary storing authors and create comma deliminated 
                template_dict["Author"] = authors_as_string[:-2] #get the well formatted list and remove the ending comma
        except KeyError:
            pass
        template_dict["Link"] = entry["link"]  #set link to the template dictionary
        template_dict["Published_Parsed"] = entry["published_parsed"] #get the published date parsed
        template_dict["Summary"] = entry["summary"]
        cleaned_tags = ""
        try:
            for tag in entry["tags"]:
                cleaned_tags += f"{tag['term']},"
        except KeyError:
            pass
        template_dict["tags"] = cleaned_tags
        nyt_feed.append(template_dict) #append the filled out dictionary to the list of dictionaries
    lambda_output = [dict(t) for t in {tuple(nyt_feed_dict.items()) for nyt_feed_dict in nyt_feed}] #remove all duplicates
    as_json = json.dumps(lambda_output)
    s3 = boto3.resource(service_name = "s3", region_name = "us-east-2")
    current_date_time = datetime.now()
    formatted_date = current_date_time.strftime('%m_%d_%Y')
    s3.Bucket(bucket_name).put_object(Key=f"NYT/feed_{formatted_date}.json", Body=as_json)
    return {'statusCode': 200, 'body': f"Succesfully uploaded feed_{formatted_date}.json to S3."}