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

# Set the scopes
scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]

# Be sure to replace the text with the text you wish to Tweet. 
# You can also add parameters to post polls, quote Tweets, Tweet with reply settings, and Tweet to Super Followers in addition to other features.
payload = {"text": "Hello world!"}

type = "VIDEO" # or "IMAGE" or "MULTIIMAGE" or "TEXT"

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
        with open("/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4", "rb") as video_file:
            fileSizeBytes = len(video_file.read())

        # 1. INIT (video/mp4, amplify_video)
        resp = client.media.init_upload(media_type="video/mp4", total_bytes=fileSizeBytes, media_category="amplify_video")
        media_id = resp.data.id

        # 2. APPEND chunks
        with open("/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4", "rb") as f:
            chunk_size = 5*1024*1024  # 5MB
            for i, chunk in enumerate(iter(lambda: f.read(chunk_size), b"")):
                client.media.append_upload(media_id=media_id, segment_index=i, media=chunk)

        # 3. FINALIZE
        resp = client.media.finalize_upload(media_id=media_id)

        # 4. Wait for processing
        while resp.data.processing_info.state != "succeeded":
            time.sleep(resp.data.processing_info.check_after_secs)
            resp = client.media.get_status(media_id=media_id)

        # 5. Post with video
        post = client.posts.create(text="Video post!", media={"media_ids": [media_id]})
        print(f"Posted: {post.data.id}")
    elif type == "TEXT":
        # Step 6: Create the tweet
        response = client.posts.create(body=payload)
        
        print("Response code: 201")
        print(json.dumps(response.data, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()