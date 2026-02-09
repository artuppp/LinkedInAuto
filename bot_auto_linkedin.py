#!/usr/bin/env python
import asyncio
import logging
import sqlite3
import mimetypes
import time
from google import genai
import os
import my_secrets
import urllib.parse

client = genai.Client(api_key=my_secrets.gemini_key)

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import requests

# LINKEDIN API CREDENTIALS
access_token = my_secrets.linkedin_access_token
author_urn = my_secrets.linkedin_user_urn
url = "https://api.linkedin.com/rest/posts"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202601", # Usa la versión actual
    "X-Restli-Protocol-Version": "2.0.0"
}

# Save idea to the database
def save_idea(idea):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ideas (texto) VALUES (?)", (idea,))
    conn.commit()
    idea_id = cursor.lastrowid
    conn.close()
    return idea_id

# Retrieve all ideas from the database
def get_ideas():
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto, alredy_posted, final_post, created_at FROM ideas ORDER BY created_at ASC")
    ideas = cursor.fetchall()
    conn.close()
    return ideas

# Remove idea from the database by ID
def remove_ideas(idea_id):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()

def show_idea(idea_id):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto, final_post, created_at FROM ideas WHERE id = ?", (idea_id,))
    idea = cursor.fetchone()
    conn.close()
    return idea

def save_media(idea_id, tipo, path, original_file_id):
    conn = sqlite3.connect("media.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO idea_media (idea_id, type, path, original_file_id) VALUES (?, ?, ?, ?)", (idea_id, tipo, path, original_file_id))
    conn.commit()
    media_id = cursor.lastrowid
    conn.close()
    return media_id

def get_first_not_posted_idea():
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto, final_post FROM ideas WHERE alredy_posted = 0 ORDER BY created_at ASC LIMIT 1")
    idea = cursor.fetchone()
    conn.close()
    return idea

def get_media_for_idea(idea_id):
    conn = sqlite3.connect("media.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, path FROM idea_media WHERE idea_id = ?", (idea_id,))
    media = cursor.fetchall()
    conn.close()
    return media

def update_idea_generate(idea_id, final_post):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE ideas SET alredy_posted = 0, final_post = ? WHERE id = ?", (final_post, idea_id))
    conn.commit()
    conn.close()

def update_idea_as_posted(idea_id):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE ideas SET alredy_posted = 1 WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()

def remove_media_for_idea(idea_id):
    conn = sqlite3.connect("media.db")
    # First, delete the media files from storage
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM idea_media WHERE idea_id = ?", (idea_id,))
    media_files = cursor.fetchall()
    for media_file in media_files:
        path = media_file[0]
        if os.path.exists(path):
            os.remove(path)
    # Then, delete the media records from the database
    cursor.execute("DELETE FROM idea_media WHERE idea_id = ?", (idea_id,))
    conn.commit()
    conn.close()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def isAutorized(user_id):
    # Define a list of authorized user IDs
    authorized_users = [953853270] # Just me! 
    # Check if the user_id is in the list of authorized users
    return user_id in authorized_users

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the user idea to the database."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    idea_text = update.message.text
    idea_id = save_idea(idea_text)
    context.user_data["attach_to_idea"] = idea_id
    await update.message.reply_text(f"Idea saved with ID: {idea_id}. You can upload images or videos to attach to this idea. Generation will be ready in a few seconds, and then you can post to LinkedIn with /post command.")
    # Run generation of LinkedIn post in the background
    asyncio.create_task(generate_linkedin_post(idea_id))

async def list_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all ideas from the database."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    ideas = get_ideas()
    if not ideas:
        await update.message.reply_text("No ideas found.")
        return
    response = "Ideas:\n"
    for idea in ideas:
        response += f"{idea[0]}: {idea[1]} ([{idea[3]}]) (Posted: {'Yes' if idea[2] else 'No'}, Created at: {idea[4]})\n"
        
    await update.message.reply_text(response)

async def list_media_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all media for an idea."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    ideas = get_ideas()
    if not ideas:
        await update.message.reply_text("No ideas found.")
        return
    for idea in ideas:
        media = get_media_for_idea(idea_id=idea[0])
        response = f"Idea {idea[0]}: {idea[1]} ([{idea[3]}])\nMedia:\n"
        for m in media:
            response += f"- {m[1]}: {m[2]}\n"
        await update.message.reply_text(response)

async def remove_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove an idea from the database by ID."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    idea_id = int(context.args[0])
    if not show_idea(idea_id):
        await update.message.reply_text("Idea not found.")
        return
    remove_ideas(idea_id)
    remove_media_for_idea(idea_id)
    await update.message.reply_text(f"Idea with ID {idea_id} removed!")

async def search_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for an idea in the database by ID."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    idea_id = int(context.args[0])
    idea = show_idea(idea_id)
    if idea:
        response = f"Idea found: {idea[1]} ([{idea[2]}]) (created at {idea[3]})"
        context.user_data["attach_to_idea"] = idea_id
    else:
        response = "Idea not found."
    await update.message.reply_text(response)

async def handle_photo(update, context):
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    
    # Just upload 4 photos per idea (and NO videos)
    media = get_media_for_idea(context.user_data.get("attach_to_idea"))
    if any(m for m in media if m[1] == "video"):
        await update.message.reply_text("You have already attached a video to this idea, so you cannot attach photos.")
        return
    if len(media) >= 4:
        await update.message.reply_text("You have already attached 4 media items to this idea, which is the maximum allowed.")
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    idea_id = context.user_data.get("attach_to_idea")
    path = f"storage/photos/idea_{idea_id}_{photo.file_unique_id}.jpg"

    await file.download_to_drive(path)

    save_media(
        idea_id=idea_id,
        tipo="photo",
        path=path,
        original_file_id=photo.file_id
    )

    await update.message.reply_text("📸 Stored photo")

async def handle_video(update, context):
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    
    # Just upload 1 video per idea (and NO photos)
    media = get_media_for_idea(context.user_data.get("attach_to_idea"))
    if any(m for m in media if m[1] == "photo"):
        await update.message.reply_text("You have already attached a photo to this idea, so you cannot attach a video.")
        return
    if len(media) >= 1:
        await update.message.reply_text("You have already attached a media item to this idea, which is the maximum allowed.")
        return

    video = update.message.video
    file = await context.bot.get_file(video.file_id)

    idea_id = context.user_data.get("attach_to_idea")
    path = f"storage/videos/idea_{idea_id}_{video.file_unique_id}.mp4"

    await file.download_to_drive(path)

    save_media(
        idea_id=idea_id,
        tipo="video",
        path=path,
        original_file_id=video.file_id
    )

    await update.message.reply_text("🎥 Vídeo guardado")

def upload_image_to_linkedin(image, author_urn, access_token):
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
        print(f"Error initializing image upload: {response_image.status_code}")
        print(response_image.text)
        return None

    print("Load URL:", url_upload)
    print("Image URN:", urn)
    print(f"Uploading image {image} to LinkedIn...")

    # Upload of the image
    with open(image, "rb") as image_file:
        upload_response = requests.put(url_upload, data=image_file, headers={"Authorization": f"Bearer {access_token}"})
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

    response_video = requests.post(url_video, headers=headers, json=payload_video)
    url_upload = response_video.json().get("value", {}).get("uploadInstructions", {})[0].get("uploadUrl", "")
    urn = response_video.json().get("value", {}).get("video", "")

    if response_video.status_code != 200:
        print(f"Error initializing video upload: {response_video.status_code}")
        print(response_video.text)

    print("Load URL:", url_upload)
    print("Video URN:", urn)

    # Upload video file
    with open(video_path, "rb") as video_file:
        upload_response = requests.put(url_upload, data=video_file, headers={"Authorization": f"Bearer {access_token}"})
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
    response_finalize = requests.post(url_finalize, headers=headers, json=payload_finalize)
    if response_finalize.status_code != 200:
        print(f"Error al finalizar la carga del video: {response_finalize.status_code}")
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
    
    
def generate_linkedin_post(idea_id):
    # Get the first not already posted idea
    idea = get_first_not_posted_idea()
    if not idea:
        print("No unposted ideas found.")
    # Generate LinkedIn post content using Gemini API
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=(
                "Write a concise LinkedIn post in English for a tech-savvy and business-oriented audience. "
                "The tone should be professional, thoughtful, and practical, avoiding hype and marketing buzzwords. "
                "Use short paragraphs and a clear structure suitable for LinkedIn. "
                "You may include up to two relevant emojis, used sparingly. "
                "You may include a small number of relevant hashtags (maximum 3), placed at the end of the post. "
                "Do not include titles, explanations, or meta commentary. "
                "Return only the final post text.\n"
                "Topic: " + idea[1]
        ))
    except Exception as e:
        print(f"Error generating LinkedIn post: {str(e)}")
        return
    # Update the idea in the database as already posted and save the generated post
    update_idea_generate(idea_id=idea[0], final_post=response.text)

async def post_to_linkedin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    # Get media for the idea
    idea = get_first_not_posted_idea()
    media = get_media_for_idea(idea_id=idea[0])
    # Upload media to LinkedIn and get asset URNs
    if len(media) > 0:
        print(f"Uploading media for idea {idea[0]}...")
        print(f"Media to upload: {media}")
        urns, is_video = upload_all_media_to_linkedin(media)
        print(f"Media uploaded, got URNs: {urns}")
        # Wait a few seconds to ensure media is processed by LinkedIn
        print("Waiting for media to be processed by LinkedIn...")
        time.sleep(5)
    # Create the LinkedIn post with the generated content and attached media
    # if urns is empty, post without media
    if len(urns) == 0: # Just post text
        payload = { 
            "author": author_urn,
            "commentary": idea[2],
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    elif is_video: # Post video
        payload = {
            "author": author_urn,
            "commentary": idea[2],
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
    elif len(urns) > 1: # Post images
        payload = {
            "author": author_urn,
            "commentary": idea[2],
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
    else: # Just one image
        payload = {
            "author": author_urn,
            "commentary": idea[2],
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
        await update.message.reply_text("Post published successfully on your profile!")
        # Update the idea as posted in the database
        update_idea_as_posted(idea_id=idea[0])
    else:
       print(f"Error posting to LinkedIn: {response.status_code} - {response.text}")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(my_secrets.telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("idea", idea))
    application.add_handler(CommandHandler("list", list_ideas))
    application.add_handler(CommandHandler("list_media", list_media_all))
    application.add_handler(CommandHandler("remove", remove_idea))
    application.add_handler(CommandHandler("search", search_idea))
    application.add_handler(CommandHandler("post", post_to_linkedin))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()