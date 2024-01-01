import json
import os
from datetime import datetime

import boto3
import pytz

from GetRSSFeedClass import GetRSSFeedClass


def lambda_handler(event, context):
    rss_feed_name = os.environ["RSS_FEED_NAME"]
    rss_feed_url = os.environ["RSS_FEED_URL"]
    region_name = os.environ["REGION_NAME"]
    bucket_name = os.environ["BUCKET_NAME"]
    rss_feed = GetRSSFeedClass(rss_feed_url)
    feed_entries_as_list = []
    for entry in rss_feed.get_entries():
        entry_info = rss_feed.get_entry_info(entry)
        feed_entries_as_list.append(entry_info)
    lambda_output = [
        dict(t)
        for t in {
            tuple(rss_feed_dict.items()) for rss_feed_dict in feed_entries_as_list
        }
    ]
    as_json = json.dumps(lambda_output)
    s3 = boto3.resource(service_name="s3", region_name=region_name)
    current_date_time = datetime.utcnow().astimezone(pytz.timezone("US/Eastern"))
    formatted_date = current_date_time.strftime("%m_%d_%Y")
    rss_feed_for_folder_name = rss_feed_name.replace(" ", "")
    s3.Bucket(bucket_name).put_object(
        Key=f"{rss_feed_for_folder_name}/feed_{formatted_date}.json", Body=as_json
    )
    return {"statusCode": 200, "body": f"Uploaded {rss_feed_name}'s RSS feed to S3."}
