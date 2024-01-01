import json
import os
import random
from datetime import datetime

import boto3
import pytz
from bs4 import BeautifulSoup


def summarize_summary(summary):
    """Get the article's summary, parse out HTML tags/content so the summary is legible text."""
    article_summary = summary
    html_content = BeautifulSoup(article_summary, "html.parser").findAll(text=True)
    combine_html = " ".join(t.strip() for t in html_content)
    combine_html = combine_html.replace("Read more...", "")
    return combine_html


def get_paywall_site_check(website, PayWallSites):
    """Check if the inputted website has a paywall, checks against a list of websites that are known to have pay walls."""
    has_paywall = False
    for paywall_site in PayWallSites:
        if paywall_site in website:
            has_paywall = True
            break
    return has_paywall


def get_interest_info(s3, bucket_name):
    """Get the interest list from S3."""
    interests_file = os.environ["INTERESTS_FILE_NAME"].replace("Non Public Info/", "")
    temp_file_store = f"/tmp/{interests_file}"
    response = s3.Bucket(bucket_name).download_file(interests_file, temp_file_store)
    interest_storage_file = json.load(open(temp_file_store))[0]
    interest_dict = interest_storage_file["InterestWebsites"]
    interest_tag_dict = interest_storage_file["InterestTags"]
    paywall_sites = interest_storage_file["PayWallSites"]
    interest_list = list(interest_dict.keys())
    return interest_dict, interest_list, paywall_sites


def get_rss_data_from_s3(website, bucket_name, s3, formatted_date):
    website_no_spaces = website.replace(" ", "")
    file_name = rf"{website_no_spaces}/feed_{formatted_date}.json"
    remove_website = file_name.replace(f"/{website_no_spaces}", "").replace("/", "_")
    temp_file_store_website = rf"/tmp/{remove_website}"
    response = s3.Bucket(bucket_name).download_file(file_name, temp_file_store_website)
    return json.load(open(temp_file_store_website))


def get_random_indices(number_articles, num_articles_to_display_in_email):
    random_indices = []
    for i in range(num_articles_to_display_in_email):
        rand_index = random.randrange(0, number_articles)
        if rand_index not in random_indices:
            random_indices.append(rand_index)
    return random_indices


def format_data(
    s3,
    bucket_name,
    interest_dict,
    interest,
    formatted_date,
    paywall_sites,
    paywall_icon,
):
    num_articles_to_display_in_email = 10
    email_div_background_color = "#bfe5bf"
    gist_interest_dict = {
        "Technology": "Technological",
        "Finance": "Financial",
        "Politics": "Political",
        "Science": "Scientific",
    }
    re_expressed_interest = gist_interest_dict[interest]
    in_mail_content = re_expressed_interest.lower()
    html_output = f"<html><body><h1 style='color:#000000;'>Good morning!</h1><h3 style='color:#000000;'>Here's the gist on the latest {in_mail_content} news.</h3><div 'max-width: 600px; margin: 0 auto; padding: 20px;background-color: {email_div_background_color};'>"
    html_entries = []
    num_articles = 0
    for counting_website in interest_dict[interest]:
        num_articles += len(counting_website)
    random_indexes = get_random_indices(num_articles, num_articles_to_display_in_email)
    for website in interest_dict[interest]:
        object_from_s3 = get_rss_data_from_s3(website, bucket_name, s3, formatted_date)
        paywall_site_check = get_paywall_site_check(website, paywall_sites)
        for article in object_from_s3:
            article_summary = article["Summary"]
            if article_summary != "":
                article_title = article["Title"]
                article_summarized = summarize_summary(article_summary)
                if (
                    article_summarized.lower() == "comments"
                    or len(article_summarized) == 0
                ):
                    article_summarized = "No Description."
                if len(article["Author"]) == 0:
                    credit = website
                else:
                    credit = f"{article['Author']} ({website})"
                a_tag_template = f"<p style='color:#000000;'><a href = {article['Link']}>{article_title}</a>, {credit}<br>{article_summarized}</p><hr style='border: 1px solid #ccc; margin: 20px 0;'>"
                if paywall_site_check == True:
                    a_tag_template = f"<p style='color:#000000;'><img src='{paywall_icon}' alt='Image showing link has a paywall' width='15' height = '15'><a href = {article['Link']}>{article_title}</a>, {credit}<br>{article_summarized}</p><hr style='border: 1px solid #ccc; margin: 20px 0;'>"
                html_entries.append(a_tag_template)
    for i in range(len(html_entries)):
        if i in random_indexes:
            html_output += html_entries[i]
    html_output += f"<p style='color:#000000;'><img src='{paywall_icon}' alt='Image showing link has a paywall' width='15' height = '15'>: Newspaper has a paywall</p></div></body></html>"
    return BeautifulSoup(html_output, "html.parser").prettify()


def send_data(s3, bucket_name, interest, formatted_date, html):
    s3.Bucket(bucket_name).put_object(
        Key=f"GeneratedEmailTemplates/feed_{interest}_{formatted_date}.html",
        Body=html,
    )


def download_paywall_icon_from_s3(s3, bucket_name, paywall_icon):
    response = s3.Bucket(bucket_name).download_file(paywall_icon, "/tmp/image.png")


def lambda_handler(event, context):
    ### GET SOME ENVIRONMENTAL VARIABLES
    bucket_name, region_name, paywall_icon = (
        os.environ["BUCKET_NAME"],
        os.environ["REGION_NAME"],
        os.environ["PAYWALL_ICON"],
    )

    ### GET TODAYS DATE
    current_date_time = datetime.utcnow().astimezone(pytz.timezone("US/Eastern"))
    formatted_date = current_date_time.strftime("%m_%d_%Y")

    ### ESTABLISH CONNECTION TO S3
    s3 = boto3.resource(service_name="s3", region_name=region_name)
    interest_dict, interest_list, paywall_sites = get_interest_info(s3, bucket_name)

    ### GENERATE HTMLS BASED ON INTEREST AND SEND THE HTML FILE TO S3
    for interest in interest_list:
        html_file = format_data(
            s3,
            bucket_name,
            interest_dict,
            interest,
            formatted_date,
            paywall_sites,
            paywall_icon,
        )
        send_data(s3, bucket_name, interest, formatted_date, html_file)
    return {"statusCode": 200, "body": f"Succesfully uploaded htmls to S3."}
