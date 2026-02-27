# from googleapiclient.discovery import build

# API_KEY = "AIzaSyAoyXJXt5U6dtV6mUayxxkzoRDFt6wNp0U"
# youtube = build('youtube', 'v3', developerKey=API_KEY)

# search_query = "traveling"  # keyword
# min_subscribers = 100000    # filter
# channels_list = []

# # Step 1: Search channels by keyword
# request = youtube.search().list(
#     q=search_query,
#     type="channel",
#     part="snippet",
#     maxResults=50  # max per request
# )
# response = request.execute()

# # Step 2: Filter channels by subscriber count
# for item in response['items']:
#     channel_id = item['snippet']['channelId']
    
#     # Get channel stats
#     stats_request = youtube.channels().list(
#         part="statistics,snippet",
#         id=channel_id
#     )
#     stats_response = stats_request.execute()
    
#     for channel in stats_response['items']:
#         subs = int(channel['statistics'].get('subscriberCount', 0))
#         if subs >= min_subscribers:
#             channels_list.append({
#                 "name": channel['snippet']['title'],
#                 "subs": subs,
#                 "url": f"https://www.youtube.com/channel/{channel_id}"
#             })

# # Print results
# for ch in channels_list:
#     print(ch)


from googleapiclient.discovery import build

# --- User Inputs ---
search_query = input("Enter keyword for channels (e.g., traveling): ")
min_subs = int(input("Enter minimum subscribers: "))
max_subs = int(input("Enter maximum subscribers: "))

API_KEY = "AIzaSyAoyXJXt5U6dtV6mUayxxkzoRDFt6wNp0U"  # Replace with your YouTube Data API key
youtube = build('youtube', 'v3', developerKey=API_KEY)

channels_list = []
next_page_token = None

while len(channels_list) < 50:
    # Step 1: Search channels by keyword
    request = youtube.search().list(
        q=search_query,
        type="channel",
        part="snippet",
        maxResults=50,  # max per request
        pageToken=next_page_token
    )
    response = request.execute()

    for item in response['items']:
        channel_id = item['snippet']['channelId']

        # Step 2: Get channel stats
        stats_request = youtube.channels().list(
            part="statistics,snippet",
            id=channel_id
        )
        stats_response = stats_request.execute()

        for channel in stats_response['items']:
            subs = int(channel['statistics'].get('subscriberCount', 0))
            if min_subs <= subs <= max_subs:
                channels_list.append({
                    "name": channel['snippet']['title'],
                    "subs": subs,
                    "url": f"https://www.youtube.com/channel/{channel_id}"
                })
                if len(channels_list) >= 50:
                    break
        if len(channels_list) >= 50:
            break

    # Pagination
    next_page_token = response.get('nextPageToken')
    if not next_page_token:
        break  # No more results

# Step 3: Show results
print(f"\nTotal channels found: {len(channels_list)}\n")
for i, ch in enumerate(channels_list, start=1):
    print(f"{i}. {ch['name']} - {ch['subs']} subs - {ch['url']}")
