import os
import requests
import resend

# Configuración desde GitHub Secrets
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RECIPIENT_EMAIL = os.environ.get("EMAIL_USER")
URL_IMAGEN = os.environ.get("URL_IMAGEN", "")

API_URL = "https://jfebrier.pythonanywhere.com/procesar"

def obtener_html_ranking():
    payload = {"url_imagen": URL_IMAGEN}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get("html", "")

def enviar_correo(html_content):
    resend.api_key = RESEND_API_KEY

    params = {
        "from": "MEGAPODEROSOS <onboarding@resend.dev>",
        "to": [RECIPIENT_EMAIL],
        "subject": "Producción General - MEGAPODEROSOS",
        "html": html_content,
    }

    email = resend.Emails.send(params)
    print(f"Correo enviado exitosamente vía Resend. ID: {email.get('id')}")

if __name__ == "__main__":
    try:
        html = obtener_html_ranking()
        if html:
            enviar_correo(html)
        else:
            print("No se obtuvo contenido HTML de la API.")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        exit(1)
