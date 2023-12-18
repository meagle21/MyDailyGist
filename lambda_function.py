import os
from GetRSSFeedClass import GetRSSFeedClass
from datetime import datetime
import boto3
import json

def lambda_handler(event, context):
    rss_feed = GetRSSFeedClass(os.environ["RSS_FEED_URL"])
    feed_entries_as_list = []
    for entry in rss_feed.get_entries():
        entry_info = rss_feed.get_entry_info(entry)
        feed_entries_as_list.append(entry_info)
    lambda_output = [dict(t) for t in {tuple(rss_feed_dict.items()) for rss_feed_dict in feed_entries_as_list}]
    as_json = json.dumps(lambda_output)
    s3 = boto3.resource(service_name = "s3", region_name = os.environ["REGION_NAME"])
    current_date_time = datetime.now()
    formatted_date = current_date_time.strftime('%m_%d_%Y')
    s3.Bucket(os.environ["BUCKET_NAME"]).put_object(Key=f"Gizmodo/feed_{formatted_date}.json", Body=as_json)
    return {'statusCode': 200, 'body': 'Sent email.'}