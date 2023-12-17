import feedparser
import json
import boto3
from datetime import datetime


def lambda_handler(event, context):
    gizmodoFeedUrl = r"https://gizmodo.com/rss"
    feed = feedparser.parse(gizmodoFeedUrl).entries #get the entries in the feed
    gizmodoFeed = []
    for entry in feed: #iterate over the feed
        templateDict = {"Title" : "", "Author" : "", "Link" : "", "Published_Parsed" : "", "Summary" : "", "Tags" : ""} #template dict to store all the entry info
        templateDict['Title'] = entry["title"] #put title in dictionary
        authors_as_string = '' #empty string to store a more well formatted author list
        try:
            for author in entry["authors"]: #for each author name in the list of authors
                authors_as_string += f"{author['name']}, " #get name from dictionary storing authors and create comma deliminated 
                templateDict["Author"] = authors_as_string[:-2] #get the well formatted list and remove the ending comma
        except KeyError:
            pass
        templateDict["Link"] = entry["link"]  #set link to the template dictionary
        templateDict["Published_Parsed"] = entry["published_parsed"] #get the published date parsed
        templateDict["Summary"] = entry["summary"]
        cleanedTags = ""
        for tag in entry["tags"]:
            cleanedTags += f"{tag['term']},"
        templateDict["tags"] = cleanedTags
        gizmodoFeed.append(templateDict) #append the filled out dictionary to the list of dictionaries
    lambdaOutput = [dict(t) for t in {tuple(gizmodoFeedDict.items()) for gizmodoFeedDict in gizmodoFeed}] #remove all duplicates
    asJson = json.dumps(lambdaOutput)
    s3 = boto3.resource(service_name = "s3", region_name = "us-east-1")
    currentDateTime = datetime.now()
    formattedDate = currentDateTime.strftime('%m_%d_%Y')
    s3.Bucket("my-daily-gist-raw-data-warehouse-ohio").put_object(Key=f"Gizmodo/feed_{formattedDate}.json", Body=asJson)
    return {'statusCode': 200, 'body': "Succesfully uploaded file to S3."}
