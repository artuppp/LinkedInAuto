import time
import my_secrets
import requests

# LinkedIn API credentials and endpoints
access_token = my_secrets.linkedin_access_token
author_urn = my_secrets.linkedin_user_urn
url = "https://api.linkedin.com/rest/posts"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202601",  # Usa la versión actual
    "X-Restli-Protocol-Version": "2.0.0"
}


def upload_image_to_linkedin(image, author_urn, access_token):
    url_image = "https://api.linkedin.com/rest/images?action=initializeUpload"
    payload_image = {
        "initializeUploadRequest": {
            "owner": author_urn,
        }
    }

    response_image = requests.post(
        url_image, headers=headers, json=payload_image)
    url_upload = response_image.json().get("value", {}).get("uploadUrl", "")
    urn = response_image.json().get("value", {}).get("image", "")

    if response_image.status_code != 200:
        print(f"Error initializing image upload: {response_image.status_code}")
        print(response_image.text)
        return None

    print("Load URL:", url_upload)
    print("Image URN:", urn)
    print(f"Uploading image {image} to LinkedIn...")

    # Upload of the image
    with open(image, "rb") as image_file:
        upload_response = requests.put(url_upload, data=image_file, headers={
                                       "Authorization": f"Bearer {access_token}"})
        if upload_response.status_code != 201:
            print(f"Error uploading image: {upload_response.status_code}")
            print(upload_response.text)
            return None
    return urn


def upload_video_to_linkedin(video_path, author_urn, access_token):
    url_video = "https://api.linkedin.com/rest/videos?action=initializeUpload"
    fileSizeBytes = os.path.getsize(video_path)

    payload_video = {
        "initializeUploadRequest": {
            "owner": author_urn,
            "fileSizeBytes": fileSizeBytes,
            "uploadCaptions": False,
            "uploadThumbnail": False
        }
    }

    response_video = requests.post(
        url_video, headers=headers, json=payload_video)
    url_upload = response_video.json().get("value", {}).get(
        "uploadInstructions", {})[0].get("uploadUrl", "")
    urn = response_video.json().get("value", {}).get("video", "")

    if response_video.status_code != 200:
        print(f"Error initializing video upload: {response_video.status_code}")
        print(response_video.reason)

    print("Load URL:", url_upload)
    print("Video URN:", urn)

    # Upload video file
    with open(video_path, "rb") as video_file:
        upload_response = requests.put(url_upload, data=video_file, headers={
                                       "Authorization": f"Bearer {access_token}"})
        if upload_response.status_code != 200:
            print(f"Error uploading video: {upload_response.status_code}")
            print(upload_response.text)
        etag = upload_response.headers.get("etag", "")
        print("ETag of uploaded video:", etag)

    # Finalize video upload
    url_finalize = f"https://api.linkedin.com/rest/videos?action=finalizeUpload"
    payload_finalize = {
        "finalizeUploadRequest": {
            "video": urn,
            "uploadToken": "",
            "uploadedPartIds": [
                etag
            ]
        }
    }
    response_finalize = requests.post(
        url_finalize, headers=headers, json=payload_finalize)
    if response_finalize.status_code != 200:
        print(
            f"Error al finalizar la carga del video: {response_finalize.status_code}")
        print(response_finalize.text)
        return None
    print("Video upload finalized successfully.")
    return urn


def upload_all_media_to_linkedin(media):
    # If there is a video, post JUST that video, else post all images (LinkedIn doesn't allow videos + images in the same post)
    video = next((m for m in media if m[1] == "video"), None)
    if video:
        urn = upload_video_to_linkedin(video[2], author_urn, access_token)
        return [urn], True
    else:
        images_urns = []
        for m in media:
            if m[1] == "photo":
                urn = upload_image_to_linkedin(m[2], author_urn, access_token)
                images_urns.append(urn)
        return images_urns, False


def post_to_linkedin(text, media):
    # Upload media to LinkedIn and get asset URNs
    if len(media) > 0:
        print(f"Uploading media...")
        print(f"Media to upload: {media}")
        urns, is_video = upload_all_media_to_linkedin(media)
        print(f"Media uploaded, got URNs: {urns}")
        # Wait a few seconds to ensure media is processed by LinkedIn
        print("Waiting for media to be processed by LinkedIn...")
        time.sleep(5)
    # Create the LinkedIn post with the generated content and attached media
    # if urns is empty, post without media
    if len(media) == 0:  # Just post text
        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    elif is_video:  # Post video
        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "media": {
                    "id": urns[0]
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    elif len(urns) > 1:  # Post images
        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "multiImage": {
                    "images": [{"id": urn} for urn in urns],
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    else:  # Just one image
        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
                "media": {
                    "id": urns[0]
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.status_code
    else:
        return None
