from datetime import datetime
import io
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuración de APIs
GOOGLE_API_KEY = os.environ.get(
    "GOOGLE_API_KEY"
)  # Tu API Key de Gemini / Google AI Studio
genai.configure(api_key=GOOGLE_API_KEY)

# ID de la carpeta de Google Drive donde está el reporte
FOLDER_ID = "1Nzq9YFjRqQgQqjjKZqqZ7abm0cm0zzf5"
NOMBRE_ARCHIVO = "reporte_diario.png"


def buscar_y_descargar_de_drive(output_path="ranking_actual.jpg"):
  """Se conecta a Google Drive, busca el archivo 'reporte_diario.png'

  dentro de la carpeta específica y lo descarga automáticamente.
  """
  try:
    # Nota: Asegúrate de tener configuradas tus credenciales de service account o entorno de Google Drive
    # Si usas credenciales de Google Cloud, puedes autenticarte así:
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    # Si utilizas un archivo JSON de credenciales:
    # creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    # service = build('drive', 'v3', credentials=creds)

    # Si estás ejecutando en un entorno con credenciales por defecto de Google Cloud / OAuth:
    service = build("drive", "v3")

    # Consulta para buscar el archivo exacto dentro de la carpeta
    query = f"name = '{NOMBRE_ARCHIVO}' and '{FOLDER_ID}' in parents and trashed = false"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
      print(
          f"❌ No se encontró el archivo '{NOMBRE_ARCHIVO}' en la carpeta de"
          " Google Drive."
      )
      return None

    file_id = items[0]["id"]
    print(
        f"📁 Archivo encontrado en Google Drive (ID: {file_id}). Descargando..."
    )

    # Descargar el archivo
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(output_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
      status, done = downloader.next_chunk()

    print(f"✅ Imagen descargada exitosamente como: {output_path}")
    return output_path

  except Exception as e:
    print(f"⚠️ Error al conectar o descargar desde Google Drive: {e}")
    return None


def extraer_datos_con_gemini(image_path):
  """Utiliza Gemini Vision para leer la imagen recién descargada de Drive

  y extraer todos los valores tabulares de los intermediarios en formato JSON.
  """
  model = genai.GenerativeModel("gemini-2.5-flash")

  prompt = (
      "Analiza esta imagen de reporte de producción. Extrae todos los"
      " intermediarios/asesores y sus valores numéricos para cada columna:"
      " 'local', 'inter' (Internacional), 'vida', y 'auto' (Auto, Hogar y"
      " Empresa). Devuelve la respuesta ÚNICAMENTE como una lista de"
      " diccionarios en Python estricta, con las claves: 'intermediario',"
      " 'local', 'inter', 'vida', 'auto'. Los valores deben ser cadenas de"
      " texto tal cual se ven (ej. '124,082.18' o '0.00' o '-73,122.26'). No"
      " omitas a ningún asesor de la lista."
  )

  # Subir el archivo temporalmente a Gemini para análisis visual
  sample_file = genai.upload_file(image_path)

  response = model.generate_content([sample_file, prompt])
  print(
      "🤖 Datos extraídos y leídos directamente de la imagen por Gemini Vision."
  )

  # Parsear el texto devuelto por Gemini para convertirlo en una lista ejecutable de Python
  texto_respuesta = response.text.strip()
  # Limpieza básica por si el modelo incluye bloques de código markdown ```python ... ```
  if "```python" in texto_respuesta:
    texto_respuesta = texto_respuesta.split("```python")[1].split("```")[0]
  elif "```" in texto_respuesta:
    texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]

  try:
    datos_ranking = eval(texto_respuesta.strip())
    return datos_ranking
  except Exception as err:
    print(f"Error al parsear la respuesta de Gemini: {err}")
    return []


def parse_monto(valor_str):
  """Convierte cadenas como '124,082.18' o '-73,122.26' a un float de Python"""
  try:
    limpio = (
        str(valor_str)
        .replace("$", "")
        .replace(" ", "")
        .replace(",", "")
        .strip()
    )
    return float(limpio)
  except ValueError:
    return 0.0


def obtener_meta(ramo):
  if ramo == "local":
    return 30000.0
  elif ramo == "inter":
    return 250.0
  elif ramo == "vida":
    return 3000.0
  elif ramo == "auto":
    return 100000.0
  return 0.0


def cumple_meta(ramo, valor_num):
  return valor_num >= obtener_meta(ramo)


def obtener_color(ramo, valor_num):
  color_verde = "background-color: #dcfce7; color: #15803d;"
  color_naranja = "background-color: #ffedd5; color: #c2410c;"
  color_rojo = "background-color: #ffe4e6; color: #b91c1c;"
  meta = obtener_meta(ramo)

  if valor_num >= meta:
    return color_verde
  elif valor_num >= 1:
    return color_naranja
  else:
    return color_rojo


def procesar_y_enviar():
  sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
  password = os.environ.get("EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION")
  recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")
  BANNER_URL = "https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg"

  # PASO 1: Descargar siempre el reporte fresco desde Google Drive
  imagen_local = buscar_y_descargar_de_drive("reporte_diario.png")
  if not imagen_local:
    print("❌ Proceso abortado: no se pudo obtener la imagen de Google Drive.")
    return

  # PASO 2: Extraer datos automáticamente usando IA sobre la imagen descargada
  datos_ranking = extraer_datos_con_gemini(imagen_local)
  if not datos_ranking:
    print(
        "❌ Proceso abortado: no se pudieron extraer los datos de la imagen."
    )
    return

  # PASO 3: Procesar valores aplicando las fórmulas correctas
  # - Local y Vida: directos
  # - Internacional: dividido por 61.0
  # - Auto, Hogar y Empresa: multiplicado por 12.0
  datos_procesados = []
  for item in datos_ranking:
    val_local = parse_monto(item.get("local", "0"))
    val_inter = parse_monto(item.get("inter", "0")) / 61.0
    val_vida = parse_monto(item.get("vida", "0"))
    val_auto = parse_monto(item.get("auto", "0")) * 12.0

    datos_procesados.append({
        "intermediario": item.get("intermediario", "Desconocido"),
        "val_local": val_local,
        "val_inter": val_inter,
        "val_vida": val_vida,
        "val_auto": val_auto,
    })

  # PASO 4: Extraer Top 3 independientes por categoría
  top_local = sorted(
      datos_procesados, key=lambda x: x["val_local"], reverse=True
  )[:3]
  top_inter = sorted(
      datos_procesados, key=lambda x: x["val_inter"], reverse=True
  )[:3]
  top_vida = sorted(
      datos_procesados, key=lambda x: x["val_vida"], reverse=True
  )[:3]
  top_auto = sorted(
      datos_procesados, key=lambda x: x["val_auto"], reverse=True
  )[:3]

  def format_top_item(item, ramo, valor):
    if cumple_meta(ramo, valor):
      return (
          f"{item} 💪 <span style='color: #64748b; font-weight:"
          f" normal;'>(${valor:,.2f})</span>"
      )
    else:
      meta = obtener_meta(ramo)
      if ramo == "auto":
        return (
            f"{item} 🏃‍♂️ <span style='color: #64748b; font-weight:"
            f" normal;'>(${valor:,.2f})</span>"
        )
      else:
        falta = meta - valor
        return (
            f"{item} 🏃‍♂️ <span style='color: #64748b; font-weight:"
            f" normal;'>(${valor:,.2f}) — <b>¡En vía!</b> Faltan"
            f" ${falta:,.2f}</span>"
        )

  # Mes dinámico en español
  meses_es = {
      1: "enero",
      2: "febrero",
      3: "marzo",
      4: "abril",
      5: "mayo",
      6: "junio",
      7: "julio",
      8: "agosto",
      9: "septiembre",
      10: "octubre",
      11: "noviembre",
      12: "diciembre",
  }
  mes_actual = meses_es.get(datetime.now().month, "mes")

  # Ordenar tabla general
  datos_procesados.sort(
      key=lambda x: (x["val_local"], x["val_inter"], x["val_vida"], x["val_auto"]),
      reverse=True,
  )

  tot_local = sum(item["val_local"] for item in datos_procesados)
  tot_inter = sum(item["val_inter"] for item in datos_procesados)
  tot_vida = sum(item["val_vida"] for item in datos_procesados)
  tot_auto = sum(item["val_auto"] for item in datos_procesados)

  filas_html = ""
  for fila in datos_procesados:
    val_local = fila["val_local"]
    val_inter = fila["val_inter"]
    val_vida = fila["val_vida"]
    val_auto = fila["val_auto"]

    filas_html += f"""
        <tr>
            <td style="background-color: #ffffff; color: #1e293b; padding: 8px; font-weight: bold; border: 1px solid #cbd5e1; text-align: left;">{fila['intermediario']}</td>
            <td style="{obtener_color('local', val_local)} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_local:,.2f}</td>
            <td style="{obtener_color('inter', val_inter)} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_inter:,.2f}</td>
            <td style="{obtener_color('vida', val_vida)} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_vida:,.2f}</td>
            <td style="{obtener_color('auto', val_auto)} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_auto:,.2f}</td>
        </tr>
        """

  texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b;">
        <div style="font-size: 16px; font-weight: bold; color: #0284c7; margin-bottom: 6px; letter-spacing: 0.5px;">
            🚀 ¡MEGAPODEROSOS!
        </div>
        <div style="font-size: 14px; font-weight: bold; color: #334155; margin-bottom: 14px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            📊 Numeritos del mes de {mes_actual.capitalize()}
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; line-height: 1.6;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 10px; padding-bottom: 12px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 4px;">⬆️ TOP 3 &mdash; LOCAL</div>
                    <div style="padding-left: 6px; color: #334155;">
                        1. {format_top_item(top_local[0]['intermediario'], 'local', top_local[0]['val_local'])}<br>
                        2. {format_top_item(top_local[1]['intermediario'], 'local', top_local[1]['val_local'])}<br>
                        3. {format_top_item(top_local[2]['intermediario'], 'local', top_local[2]['val_local'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 10px; padding-bottom: 12px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 4px;">⬆️ TOP 3 &mdash; INTERNACIONAL</div>
                    <div style="padding-left: 6px; color: #334155;">
                        1. {format_top_item(top_inter[0]['intermediario'], 'inter', top_inter[0]['val_inter'])}<br>
                        2. {format_top_item(top_inter[1]['intermediario'], 'inter', top_inter[1]['val_inter'])}<br>
                        3. {format_top_item(top_inter[2]['intermediario'], 'inter', top_inter[2]['val_inter'])}
                    </div>
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 10px; padding-top: 4px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 4px;">⬆️ TOP 3 &mdash; VIDA</div>
                    <div style="padding-left: 6px; color: #334155;">
                        1. {format_top_item(top_vida[0]['intermediario'], 'vida', top_vida[0]['val_vida'])}<br>
                        2. {format_top_item(top_vida[1]['intermediario'], 'vida', top_vida[1]['val_vida'])}<br>
                        3. {format_top_item(top_vida[2]['intermediario'], 'vida', top_vida[2]['val_vida'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 10px; padding-top: 4px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 4px;">⬆️ TOP 3 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    <div style="padding-left: 6px; color: #334155;">
                        1. {format_top_item(top_auto[0]['intermediario'], 'auto', top_auto[0]['val_auto'])}<br>
                        2. {format_top_item(top_auto[1]['intermediario'], 'auto', top_auto[1]['val_auto'])}<br>
                        3. {format_top_item(top_auto[2]['intermediario'], 'auto', top_auto[2]['val_auto'])}
                    </div>
                </td>
            </tr>
        </table>
    </div>
    """

  html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 10px;">
        <div style="max-width: 850px; margin: 0;">
            <div style="background-color: #ffffff; padding: 20px 24px; border: 1px solid #cbd5e1; margin-bottom: 12px; border-radius: 8px; border-left: 5px solid #0284c7;">
                {texto_dinamico}
            </div>

            <img src="{BANNER_URL}" alt="Banner" style="width: 100%; max-width: 850px; display: block; border-radius: 6px; margin-bottom: 12px;">

            <table style="width: 100%; border-collapse: collapse; font-size: 12px; border-radius: 6px; overflow: hidden;">
                <thead>
                    <tr style="background-color: #0d1527; color: #ffffff;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #2d3748;">Intermediario</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #2d3748;">Local</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #2d3748;">Internacional</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #2d3748;">Vida</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #2d3748;">Auto, Hogar y Empresa</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                    <tr style="font-weight: bold; font-size: 13px;">
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748; text-align: left;">Total General</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748; text-align: right;">${tot_local:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748; text-align: right;">${tot_inter:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748; text-align: right;">${tot_vida:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748; text-align: right;">${tot_auto:,.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

  # PASO 5: Envío del correo electrónico
  msg = MIMEMultipart("alternative")
  msg["Subject"] = "Producción General - MEGAPODEROSOS"
  msg["From"] = sender_email
  msg["To"] = recipient_email
  msg.attach(MIMEText(html_content, "html"))

  try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, recipient_email.split(","), msg.as_string())
    server.quit()
    print(
        "🚀 ¡Correo con el reporte actualizado desde Google Drive enviado"
        " exitosamente!"
    )
  except Exception as e:
    print(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
  procesar_y_enviar()
