import feedparser


class GetRSSFeedClass:
    def __init__(self, feed_url):
        self.rss_feed_url = feed_url
        self.rss_entries = self.set_entries()

    def get_rss_feed_url(self):
        return self.rss_feed_url

    def set_entries(self):
        return feedparser.parse(self.get_rss_feed_url()).entries

    def get_entries(self):
        return self.rss_entries

    def clean_tags(self, tags):
        if tags != "":
            cleaned_tags = ""
            for tag in tags:
                cleaned_tags += f"{tag['term']},"
        else:
            cleaned_tags = ""
        return cleaned_tags

    def clean_authors(self, authors):
        authors_as_string = (
            ""  # empty string to store a more well formatted author list
        )
        if isinstance(authors, list):
            for author in authors:  # for each author name in the list of authors
                authors_as_string += f"{author['name']}, "  # get name from dictionary storing authors and create comma deliminated
        else:
            authors_as_string = authors
        return authors_as_string[
            :-2
        ]  # get the well formatted list and remove the ending comma

    def get_entry_info(self, entry):
        try:
            tags = entry["tags"]
        except KeyError:
            tags = ""
        try:
            authors = self.clean_authors(entry["authors"])
        except KeyError:
            authors = ""
        try:
            summary = entry["summary"]
        except KeyError:
            summary = ""
        try:
            parsed_publish_date = entry["published_parsed"]
        except KeyError:
            parsed_publish_date = ""
        try:
            title = entry["title"]
        except:
            title = ""
        try:
            link = entry["link"]
        except:
            link = ""
        return {
            "Title": title,
            "Author": authors,
            "Link": link,
            "Published_Parsed": parsed_publish_date,
            "Tags": self.clean_tags(tags),
            "Summary": summary,
        }
