from datetime import datetime
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import urllib.request

# ID correcto del archivo en Google Drive
FILE_ID = "1YmAVaDyplF6CQ_gk2NZsEmLyjFpcFH9Y"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


def descargar_desde_drive(output_path="reporte_diario.png"):
  """Descarga la imagen directamente desde Google Drive usando librerías nativas"""
  try:
    url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
    print("📁 Descargando reporte fresco desde Google Drive...")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(
        output_path, "wb"
    ) as out_file:
      out_file.write(response.read())

    print(f"✅ Imagen descargada exitosamente como: {output_path}")
    return output_path
  except Exception as e:
    print(f"⚠️ Error al descargar desde Google Drive: {e}")
    return None


def extraer_datos_con_gemini_rest(image_path):
  """Envía la imagen a Gemini utilizando la API REST mediante urllib (cero dependencias externas)"""
  if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY no está configurada en las variables de entorno.")
    return []

  try:
    with open(image_path, "rb") as image_file:
      image_bytes = image_file.read()
      image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"

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

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64,
                    }
                },
            ]
        }]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print("🤖 Consultando a Gemini Vision (vía API REST nativa)...")
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      texto_respuesta = (
          res_data.get("candidates", [{}])[0]
          .get("content", {})
          .get("parts", [{}])[0]
          .get("text", "")
          .strip()
      )

    # Limpieza de bloques markdown
    if "```python" in texto_respuesta:
      texto_respuesta = texto_respuesta.split("```python")[1].split("```")[0]
    elif "```" in texto_respuesta:
      texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]

    return eval(texto_respuesta.strip())
  except Exception as e:
    print(f"⚠️ Error al procesar con Gemini REST API: {e}")
    return []


def parse_monto(valor_str):
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
  sender_email = os.environ.get("EMAIL_USER")
  password = os.environ.get("EMAIL_PASSWORD")
  recipient_email = os.environ.get("EMAIL_RECIPIENT", sender_email)
  BANNER_URL = "https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg"

  # PASO 1: Descarga directa desde Drive
  imagen_local = descargar_desde_drive("reporte_diario.png")
  if not imagen_local:
    print("❌ Proceso abortado: no se pudo obtener la imagen de Google Drive.")
    return

  # PASO 2: Lectura automática con Gemini Vision (REST)
  datos_ranking = extraer_datos_con_gemini_rest(imagen_local)
  if not datos_ranking:
    print(
        "❌ Proceso abortado: no se pudieron extraer los datos de la imagen."
    )
    return

  # PASO 3: Procesamiento, fórmulas y EXCLUSIÓN de Cliente Directo Megacentro
  datos_procesados = []
  for item in datos_ranking:
    nombre = item.get("intermediario", "Desconocido")

    # FILTRO EXPLÍCITO: Omitir "Cliente Directo Megacentro" o filas de totales globales que traiga la imagen
    if (
        "megacentro" in nombre.lower()
        or "cliente directo" in nombre.lower()
        or "total general" in nombre.lower()
    ):
      continue

    val_local = parse_monto(item.get("local", "0"))
    val_inter = parse_monto(item.get("inter", "0")) / 61.0
    val_vida = parse_monto(item.get("vida", "0"))
    val_auto = parse_monto(item.get("auto", "0")) * 12.0

    datos_procesados.append({
        "intermediario": nombre,
        "val_local": val_local,
        "val_inter": val_inter,
        "val_vida": val_vida,
        "val_auto": val_auto,
    })

  # Top 3 independientes por categoría
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

  datos_procesados.sort(
      key=lambda x: (x["val_local"], x["val_inter"], x["val_vida"], x["val_auto"]),
      reverse=True,
  )

  # Totales calculados exclusivamente con los miembros del equipo filtrados
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

  # PASO 5: Envío del correo HTML
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
    print("🚀 ¡Correo enviado con éxito (sin Cliente Directo Megacentro)!")
  except Exception as e:
    print(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
  procesar_y_enviar()
