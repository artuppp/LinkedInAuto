# import my_secrets
import my_secrets_env as my_secrets
from google import genai

client = genai.Client(api_key=my_secrets.gemini_key)

twitter_max_characters = my_secrets.twitter_max_characters


def condense_for_x(original_post):
    # Pic a LinkedIn post and condense it to a single tweet using Gemini API
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=(
                "I will provide a LinkedIn post. Your task is to rewrite it as a single tweet. "
                "STRICT RULES: "
                "1. The output must be under 250 characters. "
                "2. Maintain the core insight and professional tone. "
                "3. Use a maximum of 2 relevant hashtags at the end. "
                "4. Return ONLY the rewritten text, no quotes or intro. "
                "5. Keep it in English.\n\n"
                f"Original Post: {original_post}"
            ))

        condensed_text = response.text.strip()

        # Security check: ensure the text is not too long for X (280 characters)
        if len(condensed_text) > twitter_max_characters:
            condensed_text = condensed_text[:twitter_max_characters-3] + "..."

        print("Condensed text for X:", condensed_text)
        return condensed_text

    except Exception as e:
        print(f"Error condensing text: {str(e)}")
        return None


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
