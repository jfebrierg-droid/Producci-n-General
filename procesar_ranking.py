from datetime import datetime
import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image
import google.generativeai as genai
import requests

# Configurar la API de Gemini para el análisis de la imagen
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Lista maestra con TODOS los miembros del equipo MEGAPODEROSOS
LISTA_MAESTRA_AGENTES = [
    "Milvio Espinal",
    "Delkis Perez",
    "Sory Morla",
    "Indhira Mora",
    "Luis T Ortiz",
    "Ruddy Arias",
    "Leomayra Alcantara",
    "Marcos Adames",
    "Maria De La Cruz",
    "Indhira Santos",
    "Nicauris Benitez",
    "Mariela de León Minaya",
    "Mery Lopez",
    "Estefania Villegas (Roger)",
    "Yudelfa Cuevas",
    "Vladimil Herrera",
    "Orquidea Feliz",
    "Marisol Payano",
    "Jairo Martinez",
    "Alsiwin Ruiz",
    "Estarlin Acosta",
    "Eleuterio Fernandez",
    "Ninfa Perez",
    "Angel Matos",
    "Ingrid Beras",
    "Kevin Ramirez",
    "Eduardo Hernandez",
    "Ana Veloz",
    "Wanda Peña",
    "Joan Danis",
    "Belkis Sanchez",
    "Aranechi Tejeda",
    "Angela Vidal",
    "Felix Morillo",
    "Hander Perez",
    "Julissa Rosario",
    "Amalfi Julissa Rodriguez",
    "Charles Furment",
    "Angela Valerio",
    "Dioselina Ramos",
    "Luisa Gonzalez",
    "Hugo Cruz",
    "Jose Terrero",
    "Maribel Fernandez",
    "Esperanza Regalado",
    "John Adams",
    "Maria Soriano",
    "Albertina Febles",
    "Franklin Graterol",
    "Cirilo Fermin",
    "Eddy Concepción",
    "Yolanda Cabrera",
    "Paula Herrera",
    "Rafael Capellan",
    "Salvador Martinez",
]


def format_moneda(valor):
    """Formatea un número asegurando que el signo menos vaya antes del dólar (-$X.XX)."""
    if valor < 0:
        return f"-${abs(valor):,.2f}"
    return f"${valor:,.2f}"


def obtener_datos_desde_drive_imagen(file_id):
    """Descarga la imagen de Google Drive y usa Gemini Vision para extraer la tabla de producción."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print("Descargando imagen desde Google Drive...")

    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.Timeout:
        raise Exception(
            "La solicitud a Google Drive tardó demasiado tiempo (timeout)."
        )

    if response.status_code != 200:
        raise Exception(
            "No se pudo descargar la imagen de Google Drive. Verifica que el archivo sea público."
        )

    image_path = "temp_ranking_drive.jpg"
    with open(image_path, "wb") as f:
        f.write(response.content)

    img = Image.open(image_path)

    print("Analizando imagen con IA para extraer los resultados...")
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = """
    Analiza esta imagen que contiene un reporte o tabla de producción de seguros del equipo MEGAPODEROSOS.
    Extrae la información de TODOS los intermediarios que aparecen y sus montos en los siguientes ramos:
    1. local
    2. inter (internacional)
    3. vida
    4. auto (auto, hogar y empresa)

    Devuelve la información estrictamente en formato de lista JSON de diccionarios, exactamente con estas claves:
    [
      {"intermediario": "Nombre del Intermediario", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
      ...
    ]
    Reglas importantes:
    - Incluye a TODOS los intermediarios visibles en la imagen.
    - Si un intermediario no tiene valor o aparece en cero/vacío, asigna el valor como "0.00".
    - Mantén los signos negativos si los números son negativos (ej. "-73,122.26").
    - Devuelve ÚNICAMENTE el bloque JSON válido, sin texto adicional antes ni después.
    """

    response = model.generate_content([img, prompt])
    texto_respuesta = response.text

    if os.path.exists(image_path):
        os.remove(image_path)

    match = re.search(r"\[.*\]", texto_respuesta, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise Exception(
            f"No se pudo interpretar la respuesta de la IA como JSON:\n{texto_respuesta}"
        )


def parse_monto(valor_str):
    try:
        if not valor_str:
            return 0.0
        return float(str(valor_str).replace(",", ""))
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
    if valor_num < 0:
        return "background-color: #ef4444; color: #ffffff;"

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
    password = os.environ.get(
        "EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION"
    )
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")

    drive_file_id = "1YmAVaDyplF6CQ_gk2NZsEmLyjFpcFH9Y"

    try:
        datos_ranking = obtener_datos_desde_drive_imagen(drive_file_id)
    except Exception as e:
        print(f"Error al procesar la imagen de Google Drive: {e}")
        return

    datos_extraidos_dict = {}
    for item in datos_ranking:
        nombre = item.get("intermediario", "").strip()
        datos_extraidos_dict[nombre] = item

    datos_procesados = []
    for agente in LISTA_MAESTRA_AGENTES:
        match_item = None
        for k, v in datos_extraidos_dict.items():
            if (
                agente.lower() in k.lower() or k.lower() in agente.lower()
            ):
                match_item = v
                break

        if match_item:
            val_local = parse_monto(match_item.get("local", "0.00"))
            val_inter = parse_monto(match_item.get("inter", "0.00")) / 61.0
            val_vida = parse_monto(match_item.get("vida", "0.00"))
            val_auto = parse_monto(match_item.get("auto", "0.00")) * 12.0
        else:
            val_local = 0.0
            val_inter = 0.0
            val_vida = 0.0
            val_auto = 0.0

        datos_procesados.append({
            "intermediario": agente,
            "val_local": val_local,
            "val_inter": val_inter,
            "val_vida": val_vida,
            "val_auto": val_auto,
        })

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
        if valor <= 0:
            return (
                f"{item} 🏃‍♂️ <span style='color: #64748b; font-weight:"
                f" normal;'>({format_moneda(0.0)})</span>"
            )
        if cumple_meta(ramo, valor):
            return (
                f"{item} 💪 <span style='color: #64748b; font-weight:"
                f" normal;'>({format_moneda(valor)})</span>"
            )
        else:
            meta = obtener_meta(ramo)
            if ramo == "auto":
                return (
                    f"{item} 🏃‍♂️ <span style='color: #64748b; font-weight:"
                    f" normal;'>({format_moneda(valor)})</span>"
                )
            else:
                falta = meta - valor
                return (
                    f"{item} 🏃‍♂️ <span style='color: #64748b; font-weight:"
                    f" normal;'>({format_moneda(valor)}) — <b>¡En vía!</b>"
                    f" Faltan {format_moneda(falta)}</span>"
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
        key=lambda x: (
            x["val_local"],
            x["val_inter"],
            x["val_vida"],
            x["val_auto"],
        ),
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

        style_local = obtener_color("local", val_local)
        style_inter = obtener_color("inter", val_inter)
        style_vida = obtener_color("vida", val_vida)
        style_auto = obtener_color("auto", val_auto)

        filas_html += f"""
        <tr>
            <td style="background-color: #ffffff; color: #1e293b; padding: 14px 16px; font-weight: bold; border: 1px solid #cbd5e1; text-align: left; font-size: 16px;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 14px 16px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 16px;">{format_moneda(val_local)}</td>
            <td style="{style_inter} padding: 14px 16px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 16px;">{format_moneda(val_inter)}</td>
            <td style="{style_vida} padding: 14px 16px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 16px;">{format_moneda(val_vida)}</td>
            <td style="{style_auto} padding: 14px 16px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 16px;">{format_moneda(val_auto)}</td>
        </tr>
        """

    texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b; text-align: left;">
        <div style="font-size: 24px; font-weight: bold; color: #0284c7; margin-bottom: 10px; letter-spacing: 0.5px; text-align: left;">
            🚀 ¡MEGAPODEROSOS!
        </div>
        <div style="font-size: 19px; font-weight: bold; color: #334155; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; text-align: left;">
            📊 Numeritos del mes de {mes_actual.capitalize()}
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 16px; line-height: 1.8; text-align: left;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 14px; padding-bottom: 16px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 8px; font-size: 17px; text-align: left;">⬆️ TOP 3 &mdash; LOCAL</div>
                    <div style="padding-left: 0px; color: #334155; text-align: left;">
                        1. {format_top_item(top_local[0]['intermediario'], 'local', top_local[0]['val_local'])}<br>
                        2. {format_top_item(top_local[1]['intermediario'], 'local', top_local[1]['val_local'])}<br>
                        3. {format_top_item(top_local[2]['intermediario'], 'local', top_local[2]['val_local'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 14px; padding-bottom: 16px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 8px; font-size: 17px; text-align: left;">⬆️ TOP 3 &mdash; INTERNACIONAL</div>
                    <div style="padding-left: 0px; color: #334155; text-align: left;">
                        1. {format_top_item(top_inter[0]['intermediario'], 'inter', top_inter[0]['val_inter'])}<br>
                        2. {format_top_item(top_inter[1]['intermediario'], 'inter', top_inter[1]['val_inter'])}<br>
                        3. {format_top_item(top_inter[2]['intermediario'], 'inter', top_inter[2]['val_inter'])}
                    </div>
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 14px; padding-top: 8px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 8px; font-size: 17px; text-align: left;">⬆️ TOP 3 &mdash; VIDA</div>
                    <div style="padding-left: 0px; color: #334155; text-align: left;">
                        1. {format_top_item(top_vida[0]['intermediario'], 'vida', top_vida[0]['val_vida'])}<br>
                        2. {format_top_item(top_vida[1]['intermediario'], 'vida', top_vida[1]['val_vida'])}<br>
                        3. {format_top_item(top_vida[2]['intermediario'], 'vida', top_vida[2]['val_vida'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 14px; padding-top: 8px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 8px; font-size: 17px; text-align: left;">⬆️ TOP 3 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    <div style="padding-left: 0px; color: #334155; text-align: left;">
                        1. {format_top_item(top_auto[0]['intermediario'], 'auto', top_auto[0]['val_auto'])}<br>
                        2. {format_top_item(top_auto[1]['intermediario'], 'auto', top_auto[1]['val_auto'])}<br>
                        3. {format_top_item(top_auto[2]['intermediario'], 'auto', top_auto[2]['val_auto'])}
                    </div>
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 16px; font-size: 16px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 14px; text-align: left; font-weight: bold;">
            ¡A seguir dándolo todo en cada ramo! A continuación, la pizarra general:
        </div>
    </div>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 10px; text-align: left;">
        <div style="width: 100%; max-width: 850px; margin: 0; text-align: left;">
            
            <!-- Tarjeta de Encabezado -->
            <div style="background-color: #ffffff; color: #1e293b; padding: 24px 28px; font-family: Arial, sans-serif; border: 1px solid #cbd5e1; text-align: left; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #0284c7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                {texto_dinamico}
            </div>

            <!-- Banner -->
            <div style="margin-bottom: 16px; text-align: left;">
                <a href="https://ibb.co/N21Ljnxt"><img src="https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg" alt="Banner-Ranking-de-Producci-n-1" border="0" style="width: 100%; max-width: 850px; height: auto; display: block; border: 0; border-radius: 6px;" /></a>
            </div>

            <!-- Tabla de Producción (Pizarra completa) -->
            <table style="width: 100%; border-collapse: collapse; font-size: 16px; margin: 0; padding: 0; border-radius: 6px; overflow: hidden; text-align: left;">
                <thead>
                    <tr style="background-color: #0d1527; color: #ffffff; text-align: left;">
                        <th style="padding: 14px; text-align: left; border: 1px solid #2d3748; font-size: 17px;">Intermediario</th>
                        <th style="padding: 14px; text-align: left; border: 1px solid #2d3748; font-size: 17px;">Local</th>
                        <th style="padding: 14px; text-align: left; border: 1px solid #2d3748; font-size: 17px;">Internacional</th>
                        <th style="padding: 14px; text-align: left; border: 1px solid #2d3748; font-size: 17px;">Vida</th>
                        <th style="padding: 14px; text-align: left; border: 1px solid #2d3748; font-size: 17px;">Auto, Hogar y Empresa</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                    <tr style="font-weight: bold; font-size: 17px; text-align: left;">
                        <td style="background-color: #0d1527; color: #ffffff; padding: 14px; border: 1px solid #2d3748; text-align: left; font-size: 17px;">Total General</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 14px; border: 1px solid #2d3748; text-align: left; font-size: 17px;">{format_moneda(tot_local)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 14px; border: 1px solid #2d3748; text-align: left; font-size: 17px;">{format_moneda(tot_inter)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 14px; border: 1px solid #2d3748; text-align: left; font-size: 17px;">{format_moneda(tot_vida)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 14px; border: 1px solid #2d3748; text-align: left; font-size: 17px;">{format_moneda(tot_auto)}</td>
                    </tr>
                </tbody>
            </table>

        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 🚀"
    )
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        destinatarios = [
            email.strip() for email in recipient_email.split(",") if email.strip()
        ]
        server.sendmail(sender_email, destinatarios, msg.as_string())
        server.quit()
        print(
            "¡Correo enviado con tipografía grande y alineado completamente a la"
            " izquierda!"
        )
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
    procesar_y_enviar()
