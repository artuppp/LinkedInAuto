import os
import requests
import secrets

access_token = secrets.linkedin_access_token
author_urn = secrets.linkedin_user_urn
url = "https://api.linkedin.com/rest/posts"

type = "VIDEO"  # or "IMAGE" or "MULTIIMAGE"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202601",  # Current version in format YYYYMM
    "X-Restli-Protocol-Version": "2.0.0"
}

if type == "MULTIIMAGE":
    urns = []

    url_image = "https://api.linkedin.com/rest/images?action=initializeUpload"

    images = [
        "/Users/loum/Desktop/LinkedIn/storage/photos/idea_1_AQADxwxrG_wvMFB-.jpg",
        "/Users/loum/Desktop/LinkedIn/storage/photos/idea_1_AQADyAxrG_wvMFB-.jpg",
    ]

    payload_image = {
        "initializeUploadRequest": {
            "owner": author_urn,
        }
    }

    for image_path in images:
        response_image = requests.post(
            url_image, headers=headers, json=payload_image)
        url_upload = response_image.json().get("value", {}).get("uploadUrl", "")
        urn = response_image.json().get("value", {}).get("image", "")
        urns.append(urn)

        if response_image.status_code != 200:
            print(
                f"Error initializing image upload: {response_image.status_code}")
            print(response_image.text)

        print("Load URL:", url_upload)
        print("Image URN:", urn)

        # Upload of the image
        with open(image_path, "rb") as image_file:
            upload_response = requests.put(url_upload, data=image_file, headers={
                                           "Authorization": f"Bearer {access_token}"})
            if upload_response.status_code != 201:
                print(f"Error uploading image: {upload_response.status_code}")
                print(upload_response.text)
elif type == "IMAGE":
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

    print("Load URL:", url_upload)
    print("Image URN:", urn)

    # Upload of the image
    with open("/Users/loum/Desktop/LinkedIn/storage/photos/idea_1_AQADxwxrG_wvMFB-.jpg", "rb") as image_file:
        upload_response = requests.put(url_upload, data=image_file, headers={
                                       "Authorization": f"Bearer {access_token}"})
        if upload_response.status_code != 201:
            print(f"Error uploading image: {upload_response.status_code}")
            print(upload_response.text)
elif type == "VIDEO":
    url_video = "https://api.linkedin.com/rest/videos?action=initializeUpload"
    fileSizeBytes = os.path.getsize(
        "/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4")

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
        print(response_video.text)

    print("Load URL:", url_upload)
    print("Video URN:", urn)

    # Upload video file
    with open("/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4", "rb") as video_file:
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
    print("Video upload finalized successfully.")

url = "https://api.linkedin.com/rest/posts"

if type == "MULTIIMAGE":
    payload = {
        "author": author_urn,
        "commentary": "test post con multiple imagenes",
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
else:
    payload = {
        "author": author_urn,
        "commentary": "test post con imagen",
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "id": urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 201:
    print("Post published successfully on your profile!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
