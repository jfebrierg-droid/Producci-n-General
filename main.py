import os
import pandas as pd
import smtplib
import imaplib
import email
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google import genai
from google.genai import types

# Configuración de credenciales
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")

EXCEL_PATH = "./maestro_intermediarios.xlsx"
LOCAL_DIR = "./temp_pdfs"

def extraer_intermediario_con_gemini(pdf_path):
    """Utiliza Gemini para extraer el texto de la 'Vía:' desde el PDF."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Subiendo {pdf_path} a Gemini para análisis...")
        uploaded_file = client.files.upload(file=pdf_path)
        
        prompt = (
            "Analiza este documento de reembolso de Humano Seguros. "
            "Busca el campo 'Vía:' o el nombre del corredor / intermediario asociado. "
            "Devuelve ÚNICAMENTE el nombre exacto del intermediario o corredor encontrado, sin texto adicional."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        intermediario = response.text.strip()
        print(f"Intermediario detectado: {intermediario}")
        client.files.delete(name=uploaded_file.name)
        return intermediario
    except Exception as e:
        print(f"Error al procesar el PDF con Gemini: {e}")
        return None

def procesar_correos_pendientes():
    """Conecta por IMAP, busca correos de reembolsos, extrae PDFs y reenvía."""
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

    try:
        # Conexión IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com") # O tu servidor IMAP corporativo
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Buscar correos no leídos provenientes de reembolsos@humano.com.do
        status, messages = mail.search(None, '(UNSEEN FROM "reembolsos@humano.com.do")')
        if status != "OK" or not messages[0]:
            print("No se encontraron nuevos correos de reembolsos.")
            mail.logout()
            return

        for email_id in messages[0].split():
            res, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    original_msg = email.message_from_bytes(response_part[1])
                    pdf_path = None
                    
                    # Extraer archivos adjuntos PDF del correo
                    for part in original_msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename and filename.lower().endswith('.pdf'):
                            pdf_path = os.path.join(LOCAL_DIR, filename)
                            with open(pdf_path, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            print(f"PDF descargado temporalmente: {filename}")
                            break
                    
                    if not pdf_path:
                        print("El correo no contenía ningún PDF adjunto.")
                        continue

                    # 1. Extraer intermediario con Gemini
                    intermediario = extraer_intermediario_con_gemini(pdf_path)
                    if not intermediario:
                        intermediario = "Desconocido"

                    # 2. Modo prueba: forzamos el destinatario a tu correo
                    correo_destino = "jfebrier@humano.com.do"
                    print(f"Modo prueba: Redirigiendo correo a {correo_destino}")

                    # 3. Construir nuevo mensaje para reenvío conservando anexos
                    nuevo_correo = MIMEMultipart()
                    nuevo_correo['From'] = EMAIL_USER
                    nuevo_correo['To'] = correo_destino
                    nuevo_correo['Cc'] = "jfebrier@humano.com.do"
                    nuevo_correo['Subject'] = f"Reembolsos - Vía: {intermediario}"

                    cuerpo = f"Estimado equipo,\n\nReembolso procesado correspondiente a la vía: {intermediario}.\n\nAtentamente,\nHumano Seguros"
                    nuevo_correo.attach(MIMEText(cuerpo, 'plain'))

                    # Adjuntar todos los archivos originales del correo
                    for part in original_msg.walk():
                        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                            continue
                        fname = part.get_filename()
                        if fname:
                            p = MIMEBase('application', 'octet-stream')
                            p.set_payload(part.get_payload(decode=True))
                            encoders.encode_base64(p)
                            p.add_header('Content-Disposition', f'attachment; filename="{fname}"')
                            nuevo_correo.attach(p)

                    # Enviar por SMTP
                    destinatarios = list(set([correo_destino, "jfebrier@humano.com.do"]))
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(EMAIL_USER, EMAIL_PASS)
                        server.sendmail(EMAIL_USER, destinatarios, nuevo_correo.as_string())
                    
                    print("Correo reenviado exitosamente con todos sus anexos.")
                    
                    # Opcional: Marcar el correo original como leído para no procesarlo dos veces
                    mail.store(email_id, '+FLAGS', '\\Seen')

                    # Limpiar archivo temporal
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)

        mail.logout()
    except Exception as e:
        print(f"Error procesando los correos: {e}")

if __name__ == "__main__":
    print("Iniciando revisión de buzón...")
    procesar_correos_pendientes()
