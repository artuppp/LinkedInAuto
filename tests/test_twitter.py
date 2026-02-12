import tweepy
import my_secrets

# 1. Tus credenciales (Cópialas desde el Dashboard de Twitter Developer)
api_key = my_secrets.twitter_api_key
api_secret = my_secrets.twitter_api_key_secret
access_token = my_secrets.twitter_access_token
access_token_secret = my_secrets.twitter_access_token_secret

# CAMBIA ESTO: "texto", "imagen" o "video"
TIPO_POST = "imagen"
# Nombre de tu archivo con extensión
RUTA_ARCHIVO = "/home/arturo/Desktop/LinkedInAuto/LinkedInAuto/storage/photos/WhatsApp Image 2026-01-21 at 10.17.29.jpeg"

# --- AUTENTICACIÓN ---
# v1.1 (Necesaria para subir archivos)
auth = tweepy.OAuth1UserHandler(
    api_key, api_secret, access_token, access_token_secret)
api_v1 = tweepy.API(auth)

# v2 (Necesaria para publicar el tuit)
client_v2 = tweepy.Client(
    api_key, api_secret, access_token, access_token_secret)


def publicar():
    # Esto verifica si tus credenciales son válidas para la API v1.1
    try:
        user = api_v1.verify_credentials()
        print(f"Autenticación exitosa: Bienvenido {user.screen_name}")
    except Exception as e:
        print(f"Error de autenticación: {e}")
    try:
        media_ids = []

        if TIPO_POST in ["imagen", "video"]:
            print(f"Subiendo {TIPO_POST}...")
            # Subida del archivo a la v1.1
            media = api_v1.media_upload(filename=RUTA_ARCHIVO)
            media_ids.append(media.media_id)
            texto_tuit = f"Tuit con {TIPO_POST} desde Python 🐍"
        else:
            texto_tuit = "Tuit de solo texto desde Python 🐍"

        # Publicar en v2 vinculando el media_id si existe
        if media_ids:
            response = client_v2.create_tweet(
                text=texto_tuit, media_ids=media_ids)
        else:
            response = client_v2.create_tweet(text=texto_tuit)

        print(f"¡Éxito! Tuit publicado con ID: {response.data['id']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    publicar()  # En la API v2 usamos tweepy.Client
