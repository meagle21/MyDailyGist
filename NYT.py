import feedparser
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    nytFeedUrl = r"https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
    feed = feedparser.parse(nytFeedUrl).entries #get the entries in the feed
    nytFeed = []
    for entry in feed:
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
        try:
            for tag in entry["tags"]:
                cleanedTags += f"{tag['term']},"
        except KeyError:
            pass
        templateDict["tags"] = cleanedTags
        nytFeed.append(templateDict) #append the filled out dictionary to the list of dictionaries
    lambdaOutput = [dict(t) for t in {tuple(gizmodoFeedDict.items()) for gizmodoFeedDict in nytFeed}] #remove all duplicates
    asJson = json.dumps(lambdaOutput)
    s3 = boto3.resource(service_name = "s3", region_name = "us-east-1")
    currentDateTime = datetime.now()
    formattedDate = currentDateTime.strftime('%m_%d_%Y')
    s3.Bucket("my-daily-gist-raw-data-warehouse-ohio").put_object(Key=f"NYT/feed_{formattedDate}.json", Body=asJson)
    return {'statusCode': 200, 'body': f"Succesfully uploaded feed_{formattedDate}.json to S3."}