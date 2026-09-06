import os
import glob
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

# Configuración de credenciales desde las variables de entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD") # Actualizado para coincidir con tu secreto de GitHub

# Rutas de trabajo
LOCAL_DIR = "./Devoluciones de Reembolso - Automate"
EXCEL_PATH = "./maestro_intermediarios.xlsx"

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
        
        # Limpiar el archivo de los servidores de Gemini
        client.files.delete(name=uploaded_file.name)
        return intermediario
    except Exception as e:
        print(f"Error al procesar el PDF con Gemini: {e}")
        return None

def buscar_correo_en_excel(intermediario):
    """Busca el correo del intermediario en el archivo Excel maestro."""
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel maestro en {EXCEL_PATH}")
        return None
    
    try:
        df = pd.read_excel(EXCEL_PATH)
        match = df[df['Intermediario'].str.contains(intermediario, case=False, na=False)]
        
        if not match.empty:
            correo = match.iloc[0]['Correo']
            print(f"Correo encontrado para '{intermediario}': {correo}")
            return correo
        else:
            print(f"No se encontró coincidencia en el Excel para el intermediario: {intermediario}")
            return None
    except Exception as e:
        print(f"Error leyendo el archivo Excel: {e}")
        return None

def reenviar_correo_original(destinatario_final, pdf_filename, intermediario_nombre):
    """Busca el correo original en el buzón y lo reenvía con todos sus anexos."""
    try:
        # Conexión IMAP para buscar el correo entrante reciente
        mail = imaplib.IMAP4_SSL("imap.gmail.com") # Ajusta esto si usas el servidor IMAP de Humano
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Buscamos correos recientes que contengan el nombre del archivo adjunto
        status, messages = mail.search(None, f'(SUBJECT "{os.path.basename(pdf_filename)}")')
        if status != "OK" or not messages[0]:
            # Búsqueda alternativa por los últimos correos no leídos
            status, messages = mail.search(None, "UNSEEN")
        
        if status == "OK" and messages[0]:
            latest_email_id = messages[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    original_msg = email.message_from_bytes(response_part[1])
                    
                    # Construir nuevo mensaje de reenvío
                    nuevo_correo = MIMEMultipart()
                    nuevo_correo['From'] = EMAIL_USER
                    nuevo_correo['To'] = destinatario_final
                    nuevo_correo['Cc'] = "jfebrier@humano.com.do" # Mantenemos CC por estructura
                    nuevo_correo['Subject'] = f"PRUEBA - Reembolso Procesado - {os.path.basename(pdf_filename)} - {intermediario_nombre}"

                    # Cuerpo del mensaje
                    cuerpo = f"Estimado intermediario,\n\nAdjunto encontrará el documento de reembolso procesado correspondiente a la vía: {intermediario_nombre}.\n\nAtentamente,\nHumano Seguros"
                    nuevo_correo.attach(MIMEText(cuerpo, 'plain'))

                    # Evitamos correos duplicados al enviador si TO y CC son el mismo en la prueba
                    destinatarios_envio = list(set([destinatario_final, "jfebrier@humano.com.do"]))
                    
                    # Copiar todos los adjuntos del correo original
                    for part in original_msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename:
                            attachment_data = part.get_payload(decode=True)
                            p = MIMEBase('application', 'octet-stream')
                            p.set_payload(attachment_data)
                            encoders.encode_base64(p)
                            p.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            nuevo_correo.attach(p)

                    # Enviar a través de SMTP
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server: # Ajusta si usas SMTP de Humano
                        server.login(EMAIL_USER, EMAIL_PASS)
                        server.sendmail(EMAIL_USER, destinatarios_envio, nuevo_correo.as_string())
                    
                    print(f"Correo reenviado exitosamente a {destinatario_final}")
                    mail.logout()
                    return True
        
        mail.logout()
        print("No se pudo localizar el correo original para reenviar los anexos.")
        return False
    except Exception as e:
        print(f"Error en el reenvío del correo: {e}")
        return False

def main():
    print("Iniciando procesamiento de reembolsos...")
    
    # Buscar archivos PDF en la ruta de trabajo local
    patron = os.path.join(LOCAL_DIR, "*.pdf")
    archivos_pdf = glob.glob(patron)
    
    if not archivos_pdf:
        print("No se encontraron archivos PDF nuevos para procesar.")
        return
    
    for pdf_path in archivos_pdf:
        print(f"\nProcesando archivo: {pdf_path}")
        
        # 1. Extraer intermediario con Gemini
        intermediario = extraer_intermediario_con_gemini(pdf_path)
        if not intermediario:
            intermediario = "Desconocido"
            
        # 2. MODO PRUEBA: Forzamos el envío a jfebrier@humano.com.do
        correo_destino = "jfebrier@humano.com.do"
        print(f"Modo de prueba activado: Ignorando Excel. El correo se enviará a {correo_destino}")
            
        # 3. Reenviar correo con todos sus anexos
        exito = reenviar_correo_original(correo_destino, pdf_path, intermediario)
        
        if exito:
            # Eliminar el PDF de la cola local
            os.remove(pdf_path)
            print(f"Archivo {pdf_path} procesado y eliminado.")

if __name__ == "__main__":
    main()
