# import my_secrets
import my_secrets_env as my_secrets
from google import genai

client = genai.Client(api_key=my_secrets.gemini_key)


def generate_post(topic):
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
                "Topic: " + topic
            ))
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return None
    print("Generated post content:", response.text)
    return response.text
