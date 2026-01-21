import requests
import os
import pandas as pd
from dotenv import load_dotenv

from datetime import datetime
load_dotenv()


API_KEY = os.getenv("YOUTUBE_API_KEY")

# --------------------------
# HELPER FUNCTIONS
# --------------------------
def get_channel_info(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={API_KEY}"
    response = requests.get(url).json()

    if not response.get("items"):
        return None

    item = response["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]

    published_at = snippet.get("publishedAt", "")
    try:
        published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    except:
        pass

    return {
        "Channel Name": snippet.get("title"),
        "Channel ID": item.get("id"),
        "Channel URL": f"https://www.youtube.com/channel/{item.get('id')}",
        "Subscribers": int(stats.get("subscriberCount", 0)),
        "Total Videos": int(stats.get("videoCount", 0)),
        "Total Views": int(stats.get("viewCount", 0)),
        "Country": snippet.get("country", "N/A"),
        "Joined Date": published_at,
        "Thumbnail URL": snippet.get("thumbnails", {}).get("default", {}).get("url"),
        "About Section": snippet.get("description")
    }

# --------------------------
# SEARCH CHANNELS BY KEYWORD
# --------------------------
def search_channels_by_keyword(keyword, max_channels, min_subs, max_subs):
    channels_data = []
    next_page_token = None

    while True:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={keyword}&maxResults=50&key={API_KEY}"
        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url).json()

        for item in response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            info = get_channel_info(channel_id)

            if not info:
                continue

            subs = info["Subscribers"]

            if min_subs <= subs <= max_subs:
                channels_data.append(info)

                if len(channels_data) >= max_channels:
                    return channels_data

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break  # No more search pages

    return channels_data


# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    keyword = input("Enter keyword: ").strip()
    max_channels = int(input("Max channels: "))
    min_subs = int(input("Min subscribers: "))
    max_subs = int(input("Max subscribers: "))

    print(f"\nSearching channels for '{keyword}' ...")

    channels = search_channels_by_keyword(keyword, max_channels, min_subs, max_subs)

    if channels:
        df = pd.DataFrame(channels)
        filename = f"youtube_channels_{keyword}.xlsx"
        df.to_excel(filename, index=False)
        print(f"Saved {len(channels)} channels to {filename}")
    else:
        print("No channels found")
