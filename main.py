import glob
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google import genai
import pandas as pd

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES Y RUTAS
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Credenciales de correo (leídas de las variables de entorno de GitHub)
EMAIL_USER = os.environ.get("EMAIL_USER", "jfebrier@humano.com.do")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# Rutas de las carpetas y archivos
EXCEL_PATH = (
    "Contactos_Cumpleanos_Megacentro_Automatizacion_ULTIMA_VERSION_10000_MENSAJES.xlsx"
)
CARPETA_PDFS = "./Devoluciones de Reembolso - Automate"


def procesar_reembolsos():
  print("Iniciando procesamiento de reembolsos...")

  # 1. Buscar el PDF más reciente en la carpeta designada
  if not os.path.exists(CARPETA_PDFS):
    os.makedirs(CARPETA_PDFS, exist_ok=True)

  archivos_pdf = glob.glob(os.path.join(CARPETA_PDFS, "*.pdf"))
  if not archivos_pdf:
    print("No se encontraron archivos PDF nuevos para procesar.")
    return

  # Seleccionar el archivo PDF más reciente
  archivo_reciente = max(archivos_pdf, key=os.path.getctime)
  print(f"Procesando archivo: {archivo_reciente}")

  # 2. Extraer texto usando la API oficial de Gemini
  client = genai.Client(api_key=GEMINI_API_KEY)
  with open(archivo_reciente, "rb") as f:
    uploaded_file = client.files.upload(
        file=f, config={"mime_type": "application/pdf"}
    )

  prompt = (
      "Analiza este documento PDF de reembolso y extrae únicamente el texto"
      " exacto que se encuentra en la línea 'Vía:' (por ejemplo:"
      " Julissa Rosario Antigua/Jose Manuel Febrier Garcia). Devuelve solo el"
      " nombre limpio sin texto adicional ni explicaciones."
  )

  response = client.models.generate_content(
      model="gemini-2.5-flash", contents=[uploaded_file, prompt]
  )
  nombre_via = response.text.strip()
  print(f"Nombre extraído de la línea Vía: {nombre_via}")

  if not nombre_via:
    print("No se pudo identificar el destinatario en el PDF.")
    return

  # 3. Buscar el correo electrónico en el archivo Excel maestro (para verificar lógica)
  try:
    df = pd.read_excel(EXCEL_PATH)
    resultado = df[
        df["Nombre"].astype(str).str.contains(nombre_via, case=False, na=False)
    ]

    if resultado.empty:
      print(
          f"Aviso: No se encontró el contacto '{nombre_via}' en el Excel"
          " maestro, pero se procederá con la prueba."
      )
    else:
      correo_encontrado = resultado.iloc[0]["Correo"]
      print(
          f"Contacto localizado en Excel. Correo asociado que se enviaría en"
          f" producción: {correo_encontrado}"
      )

  except Exception as e:
    print(f"Error al leer el archivo Excel: {e}")
    return

  # 4. PRUEBA: Reenviar el correo exclusivamente a jfebrier@humano.com.do con el nuevo formato de asunto
  try:
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = "jfebrier@humano.com.do"

    # Asunto actualizado con el nombre del intermediario separado por guion
    msg["Subject"] = (
        f"PRUEBA - Reembolso Procesado - {os.path.basename(archivo_reciente)} -"
        f" {nombre_via}"
    )

    cuerpo = (
        f"Hola José,\n\nEsta es una prueba de envío exclusivo para"
        f" jfebrier@humano.com.do.\nNombre extraído de la Vía en el PDF:"
        f" {nombre_via}\n\nSaludos cordiales."
    )
    msg.attach(MIMEText(cuerpo, "plain"))

    # Adjuntar el archivo PDF original
    with open(archivo_reciente, "rb") as attachment:
      part = MIMEBase("application", "octet-stream")
      part.set_payload(attachment.read())
      encoders.encode_base64(part)
      part.add_header(
          "Content-Disposition",
          f"attachment; filename= {os.path.basename(archivo_reciente)}",
      )
      msg.attach(part)

    # Conexión al servidor SMTP de Office 365
    server = smtplib.SMTP("smtp.office365.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)

    # Enviar únicamente a tu correo de prueba
    server.sendmail(EMAIL_USER, "jfebrier@humano.com.do", msg.as_string())
    server.quit()
    print("¡Correo de prueba enviado exitosamente solo a jfebrier@humano.com.do!")

  except Exception as e:
    print(f"Error al enviar el correo de prueba: {e}")


if __name__ == "__main__":
  procesar_reembolsos()
