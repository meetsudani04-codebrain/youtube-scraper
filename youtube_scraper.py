# # import yt_dlp
# # import csv

# # # =====================
# # # Configuration
# # # =====================

# # URL = "https://www.youtube.com/watch?v=KAgzgYYYcCQ"

# # ydl_opts = {
# #     'skip_download': True,      # don’t download media
# #     'quiet': True,              # minimize logs
# #     'no_warnings': True,        # suppress warnings
# #     'ignore_errors': True,      # skip problems
# # }

# # output_csv_file = "yt_metadata.csv"

# # # =====================
# # # Scrape & Save
# # # =====================

# # def extract_metadata(url):
# #     data = []
# #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
# #         info = ydl.extract_info(url, download=False)

# #         # If playlist / channel
# #         videos = info.get('entries') or [info]

# #         for video in videos:
# #             if not video:
# #                 continue
# #             data.append({
# #                 'id': video.get('id'),
# #                 'title': video.get('title'),
# #                 'uploader': video.get('uploader'),
# #                 'channel_id': video.get('channel_id'),
# #                 'upload_date': video.get('upload_date'),
# #                 'duration': video.get('duration'),
# #                 'view_count': video.get('view_count'),
# #                 'like_count': video.get('like_count'),
# #                 'comment_count': video.get('comment_count'),
# #                 'url': video.get('webpage_url'),
# #             })
# #     return data

# # if __name__ == "__main__":
# #     rows = extract_metadata(URL)

# #     # Save to CSV
# #     with open(output_csv_file, "w", newline="", encoding="utf-8") as f:
# #         writer = csv.DictWriter(f, fieldnames=rows[0].keys())
# #         writer.writeheader()
# #         writer.writerows(rows)

# #     print(f"Saved {len(rows)} items to {output_csv_file}")


# print("This file has been deprecated. Please refer to the updated scraper implementation.")

# print("rUN.")

# Let me get information about which AWS services are available under the free tier and any current usage.

# Querying Cost Management APIs

# Analyzing Billing and Cost Management data

# Retrieving free tier data

# Operation: GetAccountPlanState | View on AWS console home 

# Retrieving free tier data

# Operation: GetFreeTierUsage | View on Free Tier page 

# Based on your account information, here's your AWS Free Tier status:

# Your Account Type: Free Plan account (created after July 15, 2025)

# Current Free Tier Usage: No active usage detected for any services

# Available Benefits:

# Up to $200 in credits (you have $100 remaining)
# Credits valid until June 18, 2026
# Access to Always Free services
# AWS Free Tier Services Include:

# Compute:
# Amazon EC2 - Virtual servers in the cloud
# AWS Lambda - Serverless computing


# Storage:
# Amazon S3 - Object storage
# Amazon EBS - Block storage for EC2

# Database:
# Amazon RDS - Managed relational databases
# Amazon DynamoDB - NoSQL database

# Networking:
# Amazon CloudFront - Content delivery network
# Amazon VPC - Virtual private cloud


# Analytics:
# Amazon CloudWatch - Monitoring and observability

# Security & Identity:
# AWS IAM - Identity and access management
# AWS Certificate Manager - SSL/TLS certificates

# Developer Tools:
# AWS CodeCommit - Source control service
# AWS CodeBuild - Build service

# Machine Learning:
# Amazon Rekognition - Image and video analysis
# Amazon Comprehend - Natural language processing
# For the most current and complete list of free tier services with specific usage limits for your account type, visit the AWS Free Tier page .

# Since you currently have no active usage, you can start experimenting with these services within the free tier limits without any charges as long as you stay within your $100 remaining credits.




