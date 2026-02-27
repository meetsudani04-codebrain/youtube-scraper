import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not set")

youtube = build("youtube", "v3", developerKey=API_KEY)

# --------------------------
# GET CHANNEL METADATA USING yt-dlp
# --------------------------
def get_channel_info_ytdlp(channel_url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
    except Exception as e:
        print(f"❌ yt-dlp failed for {channel_url}: {e}")
        return None

    return {
        "Channel Name": info.get("channel"),
        "Channel URL": channel_url,
        "Subscribers": info.get("channel_follower_count", 0),
        "Total Views": info.get("view_count", 0),
        "Total Videos": info.get("playlist_count", 0),
        "Description": info.get("description"),
        "Thumbnail URL": info.get("thumbnail"),
    }

# --------------------------
# SEARCH CHANNELS (API ONLY FOR URL)
# --------------------------
def search_channels(keyword, max_channels, min_subs, max_subs):
    results = []
    next_page_token = None

    while len(results) < max_channels:
        request = youtube.search().list(
            q=keyword,
            type="channel",
            part="snippet",
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            channel_url = f"https://www.youtube.com/channel/{channel_id}"

            info = get_channel_info_ytdlp(channel_url)
            if not info:
                continue

            subs = info["Subscribers"]
            if min_subs <= subs <= max_subs:
                results.append(info)
                print(f"✅ {info['Channel Name']} ({subs} subs)")

            if len(results) >= max_channels:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return results

# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    keyword = input("Enter keyword: ").strip()
    max_channels = int(input("Max channels: "))
    min_subs = int(input("Min subscribers: "))
    max_subs = int(input("Max subscribers: "))

    print(f"\n🔍 Searching channels for '{keyword}'...\n")

    channels = search_channels(keyword, max_channels, min_subs, max_subs)

    if channels:
        df = pd.DataFrame(channels)
        filename = f"youtube_channels_{keyword}.xlsx"
        df.to_excel(filename, index=False)
        print(f"\n📁 Saved {len(channels)} channels to {filename}")
    else:
        print("❌ No channels found")
