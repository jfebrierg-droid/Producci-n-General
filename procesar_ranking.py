import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración de variables desde las credenciales secretas de GitHub
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", EMAIL_USER)

# URL pública de la imagen de origen o endpoint
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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Producción General - Megapoderosos"
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT_EMAIL

    parte_html = MIMEText(html_content, "html")
    msg.attach(parte_html)

    # Conexión al servidor SMTP de Office 365 / Outlook
    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

if __name__ == "__main__":
    try:
        html = obtener_html_ranking()
        if html:
            enviar_correo(html)
            print("Correo enviado exitosamente.")
        else:
            print("No se obtuvo contenido HTML de la API.")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        exit(1)