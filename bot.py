#!/usr/bin/env python
import asyncio
import my_secrets
import schedule
from database_helper import save_idea, get_ideas, remove_ideas, show_idea, save_media, get_first_not_posted_idea, get_media_for_idea, update_idea_as_posted, update_idea_generate, remove_media_for_idea
from linkedin_helper import post_to_linkedin
from gemini_helper import generate_post
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Days of the week to post scheduled posts
days_to_post = ["tuesday", "thursday"]
# Time of day to post scheduled posts (24-hour format, e.g., "14:30" for 2:30 PM)
post_time = "11:00"


def isAutorized(user_id):
    authorized_users = [int(my_secrets.telegram_chat_id)]  # Just me!
    return user_id in authorized_users


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
    asyncio.create_task(generate_update_post(idea_id))


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
        await update.message.reply_text(f"{idea[0]}: {idea[1]} ([{idea[3]}])")


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
    await update.message.reply_text("📸 Saved photo")


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

    await update.message.reply_text("🎥 Saved video")


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    # Get media for the idea
    idea = get_first_not_posted_idea()
    if not idea:
        await update.message.reply_text("No ideas to post.")
        return
    res = send_post(idea_id=idea[0])
    if res:
        update_idea_as_posted(idea_id=idea[0])
        await update.message.reply_text("Post published successfully on your LinkedIn profile!")
    else:
        await update.message.reply_text("Error posting to LinkedIn.")


async def post_schedule(context: ContextTypes.DEFAULT_TYPE):
    idea = get_first_not_posted_idea()
    if not idea:
        await context.bot.send_message(chat_id=my_secrets.telegram_chat_id, text="No ideas to post.")
        return
    res = send_post(idea_id=idea[0])
    if res:
        update_idea_as_posted(idea_id=idea[0])
        await context.bot.send_message(chat_id=my_secrets.telegram_chat_id, text="Scheduled post published successfully on your LinkedIn profile!")
    else:
        await context.bot.send_message(chat_id=my_secrets.telegram_chat_id, text="Error posting scheduled post to LinkedIn.")


def send_post(idea_id):
    idea = show_idea(idea_id)
    media = get_media_for_idea(idea_id=idea[0])
    res = post_to_linkedin(text=idea[2], media=media)
    return res


async def regenerate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not isAutorized(update.effective_user.id):
        await update.message.reply_text("Unauthorized user.")
        return
    idea_id = int(context.args[0])
    idea = show_idea(idea_id)
    if not idea:
        await update.message.reply_text("Idea not found.")
        return
    while True:
        result = generate_post(idea[1])
        if result:
            break
        print("Generation failed, retrying in 1 minute...")
        await asyncio.sleep(60)
    #  Update the idea in the database with the generated post
    update_idea_generate(idea_id, final_post=result)
    await update.message.reply_text("Post regenerated successfully!")


async def generate_update_post(idea_id):
    idea = show_idea(idea_id)
    while True:
        result = generate_post(idea[1])
        if result:
            break
        print("Generation failed, retrying in 1 minute...")
        await asyncio.sleep(60)
    #  Update the idea in the database with the generated post
    update_idea_generate(idea_id, final_post=result)


async def get_scheduled_post_time_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    days = ", ".join(days_to_post)
    await update.message.reply_text(f"Scheduled posts will be published on {days} at {post_time}.")


async def configure_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_days = context.args[0].split(",")
    new_time = context.args[1]
    global days_to_post, post_time
    days_to_post = [d.strip().lower() for d in new_days]
    post_time = new_time
    await update.message.reply_text(f"Schedule updated! Scheduled posts will now be published on {', '.join(days_to_post)} at {post_time}.")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(
        my_secrets.telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("idea", idea))
    application.add_handler(CommandHandler("list", list_ideas))
    application.add_handler(CommandHandler("list_media", list_media_all))
    application.add_handler(CommandHandler("remove", remove_idea))
    application.add_handler(CommandHandler("search", search_idea))
    application.add_handler(CommandHandler("post", post))
    application.add_handler(CommandHandler("regenerate", regenerate_post))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(CommandHandler(
        "schedule", get_scheduled_post_time_days))
    application.add_handler(CommandHandler(
        "configure_schedule", configure_schedule))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    # Schedule the post_schedule function to run thursdays and tuesdays at 11:00 am


if __name__ == "__main__":
    main()
