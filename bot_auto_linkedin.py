#!/usr/bin/env python
import logging
import sqlite3
import mimetypes
from google import genai
import os
import secrets

# Set GEMINI_API_KEY environment variable
os.environ["GEMINI_API_KEY"] = secrets.gemini_key
client = genai.Client()

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import requests

# LINKEDIN API CREDENTIALS
access_token = secrets.linkedin_access_token
author_urn = secrets.linkedin_user_urn
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
    cursor.execute("SELECT id, texto, created_at FROM ideas WHERE id = ?", (idea_id,))
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
    cursor.execute("SELECT id, texto FROM ideas WHERE alredy_posted = 0 ORDER BY created_at ASC LIMIT 1")
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

def update_idea_as_posted(idea_id, final_post):
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE ideas SET alredy_posted = 1, final_post = ? WHERE id = ?", (final_post, idea_id))
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
    await update.message.reply_text(f"Idea saved with ID: {idea_id}. You can upload images or videos to attach to this idea.")

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
        response += f"{idea[0]}: {idea[1]} (Posted: {'Yes' if idea[2] else 'No'}, Created at: {idea[4]})\n"
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
    await update.message.reply_text(f"Idea with ID {idea_id} removed!")

async def search_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for an idea in the database by ID."""
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    idea_id = int(context.args[0])
    idea = show_idea(idea_id)
    if idea:
        response = f"Idea found: {idea[1]} (created at {idea[2]})"
        context.user_data["attach_to_idea"] = idea_id
    else:
        response = "Idea not found."
    await update.message.reply_text(response)

async def handle_photo(update, context):
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

    await update.message.reply_text("📸 Foto guardada")

async def handle_video(update, context):
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

def upload_image_to_linkedin(image_path, author_urn, access_token):
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    mime_type, _ = mimetypes.guess_type(image_path)

    register_payload = {
        "registerUploadRequest": {
            "owner": author_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }

    r = requests.post(register_url, headers=headers, json=register_payload)
    r.raise_for_status()
    data = r.json()

    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = data["value"]["asset"]

    with open(image_path, "rb") as f:
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": mime_type or "image/jpeg"
        }
        upload_response = requests.put(upload_url, headers=upload_headers, data=f)

    upload_response.raise_for_status()
    return asset_urn

def upload_video_to_linkedin(video_path, author_urn, access_token):
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    register_payload = {
        "registerUploadRequest": {
            "owner": author_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }

    r = requests.post(register_url, headers=headers, json=register_payload)
    r.raise_for_status()
    data = r.json()

    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = data["value"]["asset"]

    with open(video_path, "rb") as f:
        upload_response = requests.put(upload_url, data=f)

    upload_response.raise_for_status()
    return asset_urn


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
    
    
def generate_linkedin_post():
    # Get the first not already posted idea
    idea = get_first_not_posted_idea()
    if not idea:
        logger.info("No new ideas to post.")
        return None
    # Generate LinkedIn post content using Gemini API
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
    # Update the idea in the database as already posted and save the generated post
    update_idea_as_posted(idea_id=idea[0], final_post=response.text)
    # Get media for the idea
    media = get_media_for_idea(idea_id=idea[0])
    # Upload media to LinkedIn and get asset URNs
    urns, is_video = upload_all_media_to_linkedin(media)
    # Create the LinkedIn post with the generated content and attached media
    if is_video:
        payload = {
            "author": author_urn,
            "commentary": response.text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
            "content": {
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": idea[1]
                        },
                        "mediaType": "VIDEO",
                        "mediaUrn": urns[0],
                        "title": {
                            "text": f"Video for idea {idea[0]}"
                        }
                    }
                ]
            }
        }
    else:
        payload = {
            "author": author_urn,
            "commentary": response.text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
            "content": {
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": idea[1]
                        },
                        "mediaType": "IMAGE",
                        "mediaUrn": urn,
                        "title": {
                            "text": f"Image for idea {idea[0]}"
                        }
                    } for urn in urns
                ]
            }
        }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print("¡Post publicado con éxito en tu perfil!")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(secrets.telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("idea", idea))
    application.add_handler(CommandHandler("list", list_ideas))
    application.add_handler(CommandHandler("remove", remove_idea))
    application.add_handler(CommandHandler("search", search_idea))
    application.add_handler(CommandHandler("post", lambda update, context: generate_linkedin_post()))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()