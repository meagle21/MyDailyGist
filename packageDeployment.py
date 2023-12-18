import io
import json
import os
import shutil

import boto3
import botocore.exceptions

SITE_PACKAGES_PATH = r"Lib/site-packages"
AWS_ACCESS_KEY_FILE, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY = (
    "aws_access.json",
    "access_key",
    "secret_access_key",
)
FILE_DEPENDENCY_JSON_FILE = "associatedFiles.json"
RSS_FEED_JSON_FILE, FEED_KEY = "rssFeeds.json", "Feeds"
DEPLOYMENT_FOLDER_NAME = "deployments"
RSS_FEED_CLASS_NAME = "GetRSSFeedClass.py"
MAIN_FUNCTION_NAME = "lambda_function.py"
INTERESTS_FILE_NAME = "user_interests_relations.json"
SUCCESSFUL_STATUS_CODES = [200, 201]
PIPELINE_SCRIPTS = ["emailGenerator", "sendEmail"]
parent_folder = os.getcwd()
feed_dependencies_for_deployment = [
    f"{parent_folder}/{SITE_PACKAGES_PATH}/feedparser",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/sgmllib.py",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/six.py",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/pytz",
]
pipeline_script_dependencies = [
    f"{parent_folder}/{SITE_PACKAGES_PATH}/bs4",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/sgmllib.py",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/six.py",
    f"{parent_folder}/{SITE_PACKAGES_PATH}/pytz",
]

json_file = json.load(open(AWS_ACCESS_KEY_FILE))[0]
associated_files = json.load(open(FILE_DEPENDENCY_JSON_FILE))[0]
rss_feeds = json.load(open(RSS_FEED_JSON_FILE))[0][FEED_KEY]
aws_access_key_value, aws_secret_access_key_value = (
    json_file[AWS_ACCESS_KEY],
    json_file[AWS_SECRET_ACCESS_KEY],
)
drop_location = f"{parent_folder}/{DEPLOYMENT_FOLDER_NAME}"
try:
    os.mkdir(drop_location)
except FileExistsError:
    shutil.rmtree(DEPLOYMENT_FOLDER_NAME)
    os.mkdir(drop_location)
client = boto3.client(
    service_name="lambda",
    region_name="us-east-2",
    aws_access_key_id=aws_access_key_value,
    aws_secret_access_key=aws_secret_access_key_value,
)
for rss_feed in rss_feeds.items():
    rss_feed_name, rss_feed_url = rss_feed[0], rss_feed[1]
    rss_feed_drop_location = f"{drop_location}/{rss_feed_name}"
    lambda_name = f"get{rss_feed_name}Feed"
    os.mkdir(rss_feed_drop_location)
    shutil.copy(
        f"{parent_folder}/{MAIN_FUNCTION_NAME}",
        f"{rss_feed_drop_location}/{MAIN_FUNCTION_NAME}",
    )
    shutil.copy(
        f"{parent_folder}/{RSS_FEED_CLASS_NAME}",
        f"{rss_feed_drop_location}/{RSS_FEED_CLASS_NAME}",
    )
    for feed_dependency in feed_dependencies_for_deployment:
        rss_feed_drop_folder_location = feed_dependency.replace(
            f"{SITE_PACKAGES_PATH}", f"/{DEPLOYMENT_FOLDER_NAME}/{rss_feed_name}"
        )
        if feed_dependency.split(".")[-1] != "py":  # if the python package is a folder
            shutil.copytree(
                feed_dependency, rss_feed_drop_folder_location
            )  # run the copy function that applies to folders
        else:  # if the python package is just a python file
            shutil.copy(
                feed_dependency, rss_feed_drop_folder_location
            )  # run the copy function that applies to files
    shutil.make_archive(rss_feed_drop_location, "zip", rss_feed_drop_location)
    buffer = (
        io.BytesIO()
    )  # have to store the zip file as a buffer object to upload to AWS Lambda via API
    with open(f"{rss_feed_drop_location}.zip", "rb") as existing_zip_file:
        buffer.write(existing_zip_file.read())
    buffer.seek(0)
    try:
        response = client.delete_function(
            FunctionName=lambda_name
        )  # delete the old version so we can add the new one
    except client.exceptions.ResourceNotFoundException:
        pass
    response = client.create_function(
        FunctionName=lambda_name,
        Runtime="python3.9",
        Role="arn:aws:iam::159535920112:role/lambda-newsletter-role",
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": buffer.read()},
        EphemeralStorage={"Size": 2_000},
        Environment={
            "Variables": {
                "RSS_FEED_URL": f"{rss_feed_url}",
                "BUCKET_NAME": associated_files["BucketName"],
                "REGION_NAME": "us-east-2",
                "RSS_FEED_NAME": rss_feed_name,
            }
        },
        Timeout=30,
    )
    responseStatusCode = response["ResponseMetadata"]["HTTPStatusCode"]
    if responseStatusCode not in SUCCESSFUL_STATUS_CODES:
        Exception(f"There was an error in uploading {rss_feed} to AWS Lambda.")
for pipeline_script in PIPELINE_SCRIPTS:
    pipeline_script_location = f"{drop_location}/{pipeline_script}"
    pipeline_script_py = f"{parent_folder}/{pipeline_script}.py"
    os.mkdir(pipeline_script_location)
    shutil.copy(
        f"{pipeline_script_py}", f"{pipeline_script_location}/lambda_function.py"
    )
    for pipeline_dependency in pipeline_script_dependencies:
        pipeline_dependency_location = pipeline_dependency.replace(
            f"{SITE_PACKAGES_PATH}", f"/{DEPLOYMENT_FOLDER_NAME}/{pipeline_script}"
        )
        if (
            pipeline_dependency.split(".")[-1] != "py"
        ):  # if the python package is a folder
            shutil.copytree(
                pipeline_dependency, pipeline_dependency_location
            )  # run the copy function that applies to folders
        else:  # if the python package is just a python file
            shutil.copy(
                pipeline_dependency, pipeline_dependency_location
            )  # run the copy function that applies to files
    shutil.make_archive(pipeline_script_location, "zip", pipeline_script_location)
    buffer = (
        io.BytesIO()
    )  # have to store the zip file as a buffer object to upload to AWS Lambda via API
    with open(f"{pipeline_script_location}.zip", "rb") as existing_zip_file:
        buffer.write(existing_zip_file.read())
    buffer.seek(0)
    try:
        response = client.delete_function(
            FunctionName=pipeline_script
        )  # delete the old version so we can add the new one
    except client.exceptions.ResourceNotFoundException:
        pass
    response = client.create_function(
        FunctionName=pipeline_script,
        Runtime="python3.9",
        Role="arn:aws:iam::159535920112:role/lambda-newsletter-role",
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": buffer.read()},
        EphemeralStorage={"Size": 2_000},
        Environment={
            "Variables": {
                "INTERESTS_FILE_NAME": INTERESTS_FILE_NAME,
                "BUCKET_NAME": associated_files["BucketName"],
                "REGION_NAME": "us-east-2",
                "INTEREST_TEMP_FILE_PATH": "/tmp/interests.json",
                "EMAIL_TEMPLATES_FOLDER": "GeneratedEmailTemplates",
            }
        },
        Timeout=30,
    )
    responseStatusCode = response["ResponseMetadata"]["HTTPStatusCode"]
    if responseStatusCode not in SUCCESSFUL_STATUS_CODES:
        Exception(f"There was an error in uploading {pipeline_script} to AWS Lambda.")
s3_client = boto3.client(
    service_name="s3",
    region_name="us-east-2",
    aws_access_key_id=aws_access_key_value,
    aws_secret_access_key=aws_secret_access_key_value,
)
s3_client.upload_file(
    INTERESTS_FILE_NAME, associated_files["BucketName"], INTERESTS_FILE_NAME
)
