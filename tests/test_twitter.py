import tweepy
import my_secrets

# 1. Your credentials (replace with your actual credentials)
api_key = my_secrets.twitter_api_key
api_secret = my_secrets.twitter_api_key_secret
access_token = my_secrets.twitter_access_token
access_token_secret = my_secrets.twitter_access_token_secret

# CAMBIA ESTO: "texto", "imagen" o "video"
TIPO_POST = "video"
# Nombre de tu archivo con extensión
RUTA_ARCHIVO = "/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4"

# --- AUTHENTICATION ---
# v1.1 (Needed for uploading media)
auth = tweepy.OAuth1UserHandler(
    api_key, api_secret, access_token, access_token_secret)
api_v1 = tweepy.API(auth)

# v2 (Needed for posting tweets with media)
client_v2 = tweepy.Client(
    consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_token_secret)


def publish():
    # This checks if your credentials are valid for API v1.1
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

        if TIPO_POST in ["imagen", "video"]:
            print(f"Uploading {TIPO_POST}...")
            # Uploading the file to v1.1
            media = api_v1.media_upload(filename=RUTA_ARCHIVO)
            media_ids.append(media.media_id)
            texto_tuit = f"Tweet with {TIPO_POST} from Python 🐍"
        else:
            texto_tuit = "Text-only tweet from Python 🐍"

        # Posting on v2 linking the media_id if it exists
        if media_ids:
            response = client_v2.create_tweet(
                text=texto_tuit, media_ids=media_ids)
        else:
            response = client_v2.create_tweet(text=texto_tuit)

        print(f"Success! Tweet published with ID: {response.data['id']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    publish()  # In API v2 we use tweepy.Client
