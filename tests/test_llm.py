from google import genai
import os
import secrets

# Set GEMINI_API_KEY environment variable
os.environ["GEMINI_API_KEY"] = secrets.gemini_key
client = genai.Client()

text = "sobre una placa que estoy haciendo para mantener diferentes sensores, un giroscopio, un acelerómetro, un sensor de temperatura"

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
        f"Topic:\n{text}"
    ),
)

print(response.text)