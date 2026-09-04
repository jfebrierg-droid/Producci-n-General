import os
import requests
import resend

# Configuración
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_2qY7cN4g_2EALfZ5sLsk6HPf3kHRSUzDG")
RECIPIENT_EMAIL = "jfebrierg@gmail.com"
API_URL = "https://jfebrier.pythonanywhere.com/procesar"

# Enlace de descarga directa del archivo en Google Drive
URL_DRIVE = "https://drive.google.com/uc?export=download&id=1Nzq9YFjRqQgQqjjkZqqZ7abm0cm0zzf5"

def obtener_html_ranking():
    payload = {"url_imagen": URL_DRIVE}
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
