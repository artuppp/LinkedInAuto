# Telegram → LinkedIn Content Bot

This project is a **Telegram bot** that lets you capture quick ideas, automatically generate an AI-powered post, and publish it directly to **LinkedIn**, including images or video.

Designed for a simple workflow:

1. Write an idea in Telegram
2. The AI generates a LinkedIn-optimized post
3. Optionally attach media (photos or video)
4. Publish directly to your LinkedIn profile

---

## ✨ Features

- 🤖 Telegram bot (python-telegram-bot v20+)
- 🧠 Automatic post generation using **Gemini / LLM**
- 🗂️ SQLite persistence (ideas + media)
- 🖼️ Attach up to:
  - 4 photos **or**
  - 1 video per idea
- 🚀 Direct publishing to LinkedIn
- 🔁 Post regeneration
- 🔐 Authorized user control

---

## 🧩 Architecture

```
Telegram
   ↓
Bot (async handlers)
   ↓
SQLite (ideas / media)
   ↓
LLM (Gemini)
   ↓
LinkedIn API
```

Post generation runs **in the background** using `asyncio.create_task` to avoid blocking the bot.

---

## 📂 Project Structure

```
.
├── bot.py                  # Main entry point
├── database_helper.py      # SQLite access layer
├── linkedin_helper.py      # LinkedIn publishing logic
├── gemini_helper.py        # AI text generation
├── my_secrets.py           # Tokens and secrets (DO NOT COMMIT)
├── database/
│   ├── ideas.db
│   └── media.db
├── storage/
│   ├── photos/
│   └── videos/
├── .gitignore
└── README.md
```

---

## 🔐 Secrets Configuration

Create a `` file (git-ignored):

```python
gemini_key = "YOUR_GEMINI_KEY"
linkedin_access_token = "YOUR_LINKEDIN_ACCESS_TOKEN"
telegram_bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
```

You may optionally migrate these values to environment variables.

---

## ▶️ How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Initialize required folders:

```bash
mkdir -p storage/photos storage/videos database
```

3. Run the bot:

```bash
python bot_auto_linkedin.py
```

---

## 💬 Bot Commands

| Command            | Description                         |
| ------------------ | ----------------------------------- |
| `/start`           | Start the bot                       |
| `/idea <text>`     | Save an idea and trigger generation |
| `/list`            | List all ideas                      |
| `/search <id>`     | Select an idea by ID                |
| `/list_media`      | List media for all ideas            |
| `/remove <id>`     | Delete an idea and its media        |
| `/post`            | Publish the first unposted idea     |
| `/regenerate <id>` | Regenerate the AI post              |

📸 Sending **photos** or 🎥 **video** attaches media to the currently selected idea.

---

## 🧠 Generation Logic

- The AI automatically retries on failure
- Generation runs in the background
- Results are stored in the database
- An idea is only marked as posted after a successful LinkedIn publish

---

## 🚨 Important Notes

- Only authorized users can interact with the bot (`isAutorized`)
- SQLite databases and media files **must not be committed**
- If secrets are ever leaked, rotate them immediately

---

## 🛣️ Possible Roadmap

- Multi-user support
- Scheduled posts
- Telegram post preview
- Environment variable support (`.env`)
- Dockerization

---

## 🧑‍💻 Author

Personal project to automate professional LinkedIn content.

