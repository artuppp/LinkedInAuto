import os
import my_secrets_env as my_secrets
import tweepy
import requests

# 1. Your credentials (replace with your actual credentials)
api_key = my_secrets.twitter_api_key
api_secret = my_secrets.twitter_api_key_secret
access_token = my_secrets.twitter_access_token
access_token_secret = my_secrets.twitter_access_token_secret

# --- AUTHENTICATION ---
# v1.1 (Needed for uploading media)
auth = tweepy.OAuth1UserHandler(
    api_key, api_secret, access_token, access_token_secret)
api_v1 = tweepy.API(auth)

# v2 (Needed for posting tweets with media)
client_v2 = tweepy.Client(
    consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_token_secret)


def post_to_twitter(text, media):
    try:
        user = api_v1.verify_credentials()
        print(f"Authentication successful: Welcome {user.screen_name}")
    except Exception as e:
        print(f"Authentication error: {e}")
    # Verify credentials for API v2
    try:
        response = client_v2.get_me()
        print(
            f"Authentication v2 successful: Welcome {response.data['username']}")
    except Exception as e:
        print(f"Authentication v2 error: {e}")
    try:
        media_ids = []
        if len(media) > 0:
            video = next((m for m in media if m[1] == "video"), None)
            if video:
                # Uploading the video to v1.1
                print(f"Uploading video {video[0]}...")
                tw_media = api_v1.media_upload(filename=video[0])
                media_ids.append(tw_media.media_id)
            else:
                for m in media:
                    # Uploading the image to v1.1
                    print(f"Uploading {m[1]} {m[0]}...")
                    tw_media = api_v1.media_upload(filename=m[0])
                    media_ids.append(tw_media.media_id)

        # Posting on v2 linking the media_id if it exists
        if media_ids:
            response = client_v2.create_tweet(
                text=text, media_ids=media_ids)
        else:
            response = client_v2.create_tweet(text=text)

        return response.status_code

    except Exception as e:
        print(f"Error: {e}")
        return None
