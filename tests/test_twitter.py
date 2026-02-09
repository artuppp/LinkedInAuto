"""
Create Tweet - X API v2
=======================
Endpoint: POST https://api.x.com/2/tweets
Docs: https://developer.x.com/en/docs/twitter-api/tweets/manage-tweets/api-reference/post-tweets

Authentication: OAuth 2.0 (User Context)
Required env vars: CLIENT_ID, CLIENT_SECRET
"""

import os
import json
from xdk import Client
from xdk.oauth1_auth import OAuth1
import my_secrets
import time
import requests

# Set the scopes
scopes = ["tweet.read", "tweet.write", "users.read", "offline.access", "media.write"]

MEDIA_ENDPOINT_URL = 'https://api.x.com/1.1/media/upload'

# Be sure to replace the text with the text you wish to Tweet. 
# You can also add parameters to post polls, quote Tweets, Tweet with reply settings, and Tweet to Super Followers in addition to other features.
payload = {"text": "Hello world!"}

type = "VIDEO" # or "IMAGE" or "MULTIIMAGE" or "TEXT"

headers = {
    "Authorization": "Bearer {}".format(my_secrets.twitter_access_token),
    "Content-Type": "application/json",
}

def main():
    # Step 1: Create PKCE instance
    auth = OAuth1(
        api_key=my_secrets.twitter_api_key,
        api_secret=my_secrets.twitter_api_key_secret,
        access_token=my_secrets.twitter_access_token,
        access_token_secret=my_secrets.twitter_access_token_secret,
        callback="http://localhost:8000/callback",
    )

    # Step 5: Create client
    client = Client(auth=auth)
    
    if type == "VIDEO":
        path ="/home/arturo/Desktop/LinkedInAuto/LinkedInAuto/storage/videos/file_example_MP4_1280_10MG.mp4"
        fileSizeBytes = os.path.getsize(path)

        # 1. INIT (video/mp4, amplify_video)
        request_data = {
            "media_type": "video/mp4",
            "total_bytes": fileSizeBytes,
            "media_category": "tweet_video",
        }

        response = client.media.initialize_upload(body=request_data)
        print(json.dumps(response.data, indent=4, sort_keys=True))
        media_id = response.data.get("id")

        # 2. APPEND
        segment_id = 0
        bytes_sent = 0
        with open(path, "rb") as f:
            while bytes_sent < fileSizeBytes:
                chunk = f.read(4 * 1024 * 1024)  # 4MB per chunk
                files = {"media": chunk}
                request_data = {
                    "media_id": media_id,
                    "segment_index": segment_id,
                    "media": chunk,
                }
                req = client.media.append_upload(media_id, request_data)
                print("APPEND response for segment {}: {}".format(segment_id, req.status_code))
                segment_id += 1
                bytes_sent = f.tell()
                print("Uploaded {} bytes".format(bytes_sent))
                
        # 3. FINALIZE
        req = client.media.finalize_upload(media_id=media_id)
        if req.status_code != 200:
            print("FINALIZE request failed: {}".format(req.text))
            return
        processing_info = req.json().get("data", {}).get("processing_info", {})
        # 4. POST TWEET
        payload["media"] = {"media_ids": [media_id]}
        response = client.posts.create(body=payload)
        print(json.dumps(response.data, indent=4, sort_keys=True))

    elif type == "TEXT":
        # Step 6: Create the tweet
        response = client.posts.create(body=payload)
        
        print(json.dumps(response.data, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()