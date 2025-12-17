import yt_dlp
import csv

# =====================
# Configuration
# =====================

URL = "https://www.youtube.com/watch?v=KAgzgYYYcCQ"

ydl_opts = {
    'skip_download': True,      # don’t download media
    'quiet': True,              # minimize logs
    'no_warnings': True,        # suppress warnings
    'ignore_errors': True,      # skip problems
}

output_csv_file = "yt_metadata.csv"

# =====================
# Scrape & Save
# =====================

def extract_metadata(url):
    data = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # If playlist / channel
        videos = info.get('entries') or [info]

        for video in videos:
            if not video:
                continue
            data.append({
                'id': video.get('id'),
                'title': video.get('title'),
                'uploader': video.get('uploader'),
                'channel_id': video.get('channel_id'),
                'upload_date': video.get('upload_date'),
                'duration': video.get('duration'),
                'view_count': video.get('view_count'),
                'like_count': video.get('like_count'),
                'comment_count': video.get('comment_count'),
                'url': video.get('webpage_url'),
            })
    return data

if __name__ == "__main__":
    rows = extract_metadata(URL)

    # Save to CSV
    with open(output_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} items to {output_csv_file}")
