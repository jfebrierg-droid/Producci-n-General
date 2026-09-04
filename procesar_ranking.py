import os
import requests
import resend
import base64

# Configuración
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_2qY7cN4g_2EALfZ5sLsk6HPf3kHRSUzDG")
RECIPIENT_EMAIL = "jfebrierg@gmail.com"
API_URL = "https://jfebrier.pythonanywhere.com/procesar"

def obtener_html_ranking():
    path_imagen = "reporte_diario.png"
    
    # Si existe la imagen descargada de Drive, la envía en Base64
    if os.path.exists(path_imagen):
        with open(path_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        payload = {"imagen_b64": encoded_string}
    else:
        # Respaldo en caso de prueba sin archivo local
        payload = {"url_imagen": "https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg"}

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
