import requests
import secrets

# 1. PEGA TU TOKEN AQUÍ
access_token = secrets.linkedin_access_token
author_urn = secrets.linkedin_user_urn
url = "https://api.linkedin.com/rest/posts"

type = "VIDEO" # O "IMAGE" o "VIDEO"  

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202601", # Usa la versión actual
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
        response_image = requests.post(url_image, headers=headers, json=payload_image)
        url_upload = response_image.json().get("value", {}).get("uploadUrl", "")
        urn = response_image.json().get("value", {}).get("image", "")
        urns.append(urn)

        if response_image.status_code != 200:
            print(f"Error al inicializar la carga de la imagen: {response_image.status_code}")
            print(response_image.text)

        print("URL de carga:", url_upload)
        print("URN de la imagen:", urn)

        # upload de la imagen
        with open(image_path, "rb") as image_file:
            upload_response = requests.put(url_upload, data=image_file, headers={"Authorization": f"Bearer {access_token}"})
            if upload_response.status_code != 201:
                print(f"Error al subir la imagen: {upload_response.status_code}")
                print(upload_response.text)
elif type == "IMAGE":
    url_image = "https://api.linkedin.com/rest/images?action=initializeUpload"

    payload_image = {
        "initializeUploadRequest": {
                "owner": author_urn,
        }
    }

    response_image = requests.post(url_image, headers=headers, json=payload_image)
    url_upload = response_image.json().get("value", {}).get("uploadUrl", "")
    urn = response_image.json().get("value", {}).get("image", "")

    if response_image.status_code != 200:
        print(f"Error al inicializar la carga de la imagen: {response_image.status_code}")
        print(response_image.text)

    print("URL de carga:", url_upload)
    print("URN de la imagen:", urn)

    # upload de la imagen
    with open("/Users/loum/Desktop/LinkedIn/storage/photos/idea_1_AQADxwxrG_wvMFB-.jpg", "rb") as image_file:
        upload_response = requests.put(url_upload, data=image_file, headers={"Authorization": f"Bearer {access_token}"})
        if upload_response.status_code != 201:
            print(f"Error al subir la imagen: {upload_response.status_code}")
            print(upload_response.text)
elif type == "VIDEO":
    url_video = "https://api.linkedin.com/rest/videos?action=initializeUpload"
    with open("/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4", "rb") as video_file:
        fileSizeBytes = len(video_file.read())

    # Generate caption of the video in the same directory with the same name but with .srt extension
    caption_path = "/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.srt"
    with open(caption_path, "w") as caption_file:
        caption_file.write("1\n00:00:00,000 --> 00:00:05,000\nThis is a test caption for the video.\n")
    print("Caption file created at:", caption_path)

    payload_video = {
        "initializeUploadRequest": {
       "owner": author_urn,
       "fileSizeBytes": fileSizeBytes,
       "uploadCaptions": False,
       "uploadThumbnail": False
        }
    }

    response_video = requests.post(url_video, headers=headers, json=payload_video)
    url_upload = response_video.json().get("value", {}).get("uploadInstructions", {})[0].get("uploadUrl", "")
    urn = response_video.json().get("value", {}).get("video", "")

    if response_video.status_code != 200:
        print(f"Error al inicializar la carga del video: {response_video.status_code}")
        print(response_video.text)

    print("URL de carga:", url_upload)
    print("URN del video:", urn)

    # upload del video
    with open("/Users/loum/Desktop/LinkedIn/storage/videos/file_example_MP4_640_3MG.mp4", "rb") as video_file:
        upload_response = requests.put(url_upload, data=video_file, headers={"Authorization": f"Bearer {access_token}"})
        if upload_response.status_code != 200:
            print(f"Error al subir el video: {upload_response.status_code}")
            print(upload_response.text)
        etag = upload_response.headers.get("etag", "")
        print("ETag del video subido:", etag)

    # finalize video upload
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
    response_finalize = requests.post(url_finalize, headers=headers, json=payload_finalize)
    if response_finalize.status_code != 200:
        print(f"Error al finalizar la carga del video: {response_finalize.status_code}")
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
    print("¡Post publicado con éxito en tu perfil!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Telegram ID 8317541333:AAGT2qi0stCKgv9fjQTf76LX-njqtIroNis