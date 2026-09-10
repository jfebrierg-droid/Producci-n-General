# -*- coding: utf-8 -*-
"""
Script: procesar_ranking.py
Descripción: Procesamiento de ranking por IA con sistema multi-cuenta (ordenado: 4 -> 3 -> 2 -> 1),
reintentos automáticos para errores 503, respaldo de modelos, mensajes cortos dominicanos
con el estilo criollo en todos los ramos, emojis alegóricos por producto y el emoji de músculo para quienes cumplen la meta.
"""

from datetime import datetime
import json
import os
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import requests
from google import genai

# --- CONFIGURACIÓN DE MULTI-CUENTAS (Orden de prioridad estricto: 4 -> 3 -> 2 -> 1) ---
API_KEYS_GEMINI = [
    os.environ.get("GEMINI_API_KEY_4"),
    os.environ.get("GEMINI_API_KEY_3"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY")
]

# Lista maestra con TODOS los miembros del equipo MEGAPODEROSOS
LISTA_MAESTRA_AGENTES = [
    "Milvio Espinal", "Delkis Perez", "Sory Morla", "Indhira Mora", "Luis T Ortiz",
    "Ruddy Arias", "Leomayra Alcantara", "Marcos Adames", "Maria De La Cruz", "Indhira Santos",
    "Nicauris Benitez", "Mariela de León Minaya", "Mery Lopez", "Estefania Villegas (Roger)", "Yudelfa Cuevas",
    "Vladimil Herrera", "Orquidea Feliz", "Marisol Payano", "Jairo Martinez", "Alsiwin Ruiz",
    "Estarlin Acosta", "Eleuterio Fernandez", "Ninfa Perez", "Angel Matos", "Ingrid Beras",
    "Kevin Ramirez", "Eduardo Hernandez", "Ana Veloz", "Wanda Peña", "Joan Danis",
    "Belkis Sanchez", "Aranechi Tejeda", "Angela Vidal", "Felix Morillo", "Hander Perez",
    "Julissa Rosario", "Amalfi Julissa Rodriguez", "Charles Furment", "Angela Valerio", "Dioselina Ramos",
    "Luisa Gonzalez", "Hugo Cruz", "Jose Terrero", "Maribel Fernandez", "Esperanza Regalado",
    "John Adams", "Maria Soriano", "Albertina Febles", "Franklin Graterol", "Cirilo Fermin",
    "Eddy Concepcion", "Yolanda Cabrera", "Paula Herrera", "Rafael Capellan", "Salvador Martinez"
]

def format_moneda(valor):
    if valor < 0:
        return f"-${abs(valor):,.2f}"
    return f"${valor:,.2f}"

def obtener_datos_desde_drive_imagen(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print("Descargando imagen desde Google Drive...")

    try:
        response = requests.get(url, timeout=30)
    except requests.exceptions.Timeout:
        raise Exception("La solicitud a Google Drive tardó demasiado tiempo (timeout).")

    if response.status_code != 200:
        raise Exception("No se pudo descargar la imagen de Google Drive. Verifica que el archivo sea público.")

    image_path = "temp_ranking_drive.jpg"
    with open(image_path, "wb") as f:
        f.write(response.content)

    img = Image.open(image_path)
    print("Analizando imagen con IA (Sistema multi-cuenta priorizando Key 4 -> 3 -> 2 -> 1)...")
    
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
    - Mantén los signos negativos si los números son negativos.
    - Devuelve ÚNICAMENTE el bloque JSON válido, sin texto adicional antes ni después.
    """

    modelos_a_probar = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    texto_respuesta = None

    for index, api_key in enumerate(API_KEYS_GEMINI):
        if not api_key:
            print(f"Aviso: La API Key #{4 - index} no está configurada o está vacía.")
            continue
        
        client = genai.Client(api_key=api_key)
        
        for modelo in modelos_a_probar:
            exito_modelo = False
            for intento in range(3):
                try:
                    print(f"Intentando con API Key #{4 - index}, modelo {modelo} (intento {intento + 1})...")
                    response = client.models.generate_content(
                        model=modelo,
                        contents=[img, prompt]
                    )
                    texto_respuesta = response.text
                    exito_modelo = True
                    print(f"¡Éxito con el modelo {modelo} usando la clave actual!")
                    break
                except Exception as e:
                    error_msg = str(e)
                    print(f"Aviso: {error_msg}")
                    if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg:
                        tiempo_espera = (intento + 1) * 3
                        print(f"Servidor saturado (503). Esperando {tiempo_espera}s antes de reintentar...")
                        time.sleep(tiempo_espera)
                        continue
                    elif "429" in error_msg or "Quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        print("Límite de cuota alcanzado. Probando siguiente opción...")
                        break
                    else:
                        break
            if exito_modelo:
                break
        if texto_respuesta:
            break

    if os.path.exists(image_path):
        os.remove(image_path)

    if not texto_respuesta:
        raise Exception("Se agotaron los reintentos, modelos y claves debido a saturación del servidor (503) o límites de cuota.")

    match = re.search(r"\[.*\]", texto_respuesta, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise Exception(f"No se pudo interpretar la respuesta de la IA como JSON:\n{texto_respuesta}")

def parse_monto(valor_str):
    try:
        if not valor_str:
            return 0.0
        return float(str(valor_str).replace(",", ""))
    except ValueError:
        return 0.0

def obtener_meta(ramo):
    if ramo == "local": return 30000.0
    elif ramo == "inter": return 250.0
    elif ramo == "vida": return 3000.0
    elif ramo == "auto": return 100000.0
    return 0.0

def cumple_meta(ramo, valor_num):
    return valor_num >= obtener_meta(ramo)

def obtener_color(ramo, valor_num):
    if valor_num < 0: return "background-color: #ef4444; color: #ffffff;"
    color_verde = "background-color: #dcfce7; color: #15803d;"
    color_naranja = "background-color: #ffedd5; color: #c2410c;"
    color_rojo = "background-color: #ffe4e6; color: #b91c1c;"
    meta = obtener_meta(ramo)
    if valor_num >= meta: return color_verde
    elif valor_num >= 1: return color_naranja
    else: return color_rojo

def procesar_y_enviar():
    sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION")
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
            if agente.lower() in k.lower() or k.lower() in agente.lower():
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
            "val_auto": val_auto
        })

    top_local = sorted(datos_procesados, key=lambda x: x["val_local"], reverse=True)[:3]
    top_inter = sorted(datos_procesados, key=lambda x: x["val_inter"], reverse=True)[:3]
    top_vida = sorted(datos_procesados, key=lambda x: x["val_vida"], reverse=True)[:3]
    top_auto = sorted(datos_procesados, key=lambda x: x["val_auto"], reverse=True)[:3]

    def format_top_item(item, ramo, valor):
        if valor <= 0:
            return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(0.0)})</span>"
        if cumple_meta(ramo, valor):
            return f"<b>{item}</b> 💪 <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span>"
        else:
            meta = obtener_meta(ramo)
            if ramo == "auto":
                return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span>"
            else:
                falta = meta - valor
                return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span><br><span style='font-size: 15px; color: #c2410c; font-weight: bold; padding-left: 20px;'>— Te faltan {format_moneda(falta)} para ganar!!</span>"

    meses_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    mes_actual = meses_es.get(datetime.now().month, "mes")

    datos_procesados.sort(key=lambda x: (x["val_local"], x["val_inter"], x["val_vida"], x["val_auto"]), reverse=True)

    tot_local = sum(item["val_local"] for item in datos_procesados)
    tot_inter = sum(item["val_inter"] for item in datos_procesados)
    tot_vida = sum(item["val_vida"] for item in datos_procesados)
    tot_auto = sum(item["val_auto"] for item in datos_procesados)

    filas_html = ""
    for fila in datos_procesados:
        val_local, val_inter, val_vida, val_auto = fila["val_local"], fila["val_inter"], fila["val_vida"], fila["val_auto"]
        style_local = obtener_color("local", val_local)
        style_inter = obtener_color("inter", val_inter)
        style_vida = obtener_color("vida", val_vida)
        style_auto = obtener_color("auto", val_auto)

        filas_html += f"""
        <tr>
            <td style="background-color: #ffffff; color: #1e293b; padding: 16px 20px; font-weight: bold; border: 1px solid #cbd5e1; text-align: left; font-size: 19px;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_local)}</td>
            <td style="{style_inter} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_inter)}</td>
            <td style="{style_vida} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_vida)}</td>
            <td style="{style_auto} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_auto)}</td>
        </tr>
        """

    texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b; text-align: left;">
        <div style="font-size: 28px; font-weight: bold; color: #0284c7; margin-bottom: 14px; letter-spacing: 0.5px; text-align: left;">🔥 EQUIPO MEGAPODEROSO 💪</div>
        <div style="font-size: 22px; font-weight: bold; color: #334155; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; text-align: left;">📊 Numeritos del mes de {mes_actual.capitalize()}</div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 19px; line-height: 1.6; text-align: left;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-bottom: 20px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 3 &mdash; LOCAL</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_local[0]['intermediario'], 'local', top_local[0]['val_local'])}<br>
                        2. {format_top_item(top_local[1]['intermediario'], 'local', top_local[1]['val_local'])}<br>
                        3. {format_top_item(top_local[2]['intermediario'], 'local', top_local[2]['val_local'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-bottom: 20px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 3 &mdash; INTERNACIONAL</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_inter[0]['intermediario'], 'inter', top_inter[0]['val_inter'])}<br>
                        2. {format_top_item(top_inter[1]['intermediario'], 'inter', top_inter[1]['val_inter'])}<br>
                        3. {format_top_item(top_inter[2]['intermediario'], 'inter', top_inter[2]['val_inter'])}
                    </div>
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 3 &mdash; VIDA</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_vida[0]['intermediario'], 'vida', top_vida[0]['val_vida'])}<br>
                        2. {format_top_item(top_vida[1]['intermediario'], 'vida', top_vida[1]['val_vida'])}<br>
                        3. {format_top_item(top_vida[2]['intermediario'], 'vida', top_vida[2]['val_vida'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 3 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_auto[0]['intermediario'], 'auto', top_auto[0]['val_auto'])}<br>
                        2. {format_top_item(top_auto[1]['intermediario'], 'auto', top_auto[1]['val_auto'])}<br>
                        3. {format_top_item(top_auto[2]['intermediario'], 'auto', top_auto[2]['val_auto'])}
                    </div>
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 16px; font-size: 19px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 16px; text-align: left; font-weight: bold;">
            A continuación, el detalle completo de la producción:
        </div>
    </div>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 10px; text-align: left;">
        <div style="width: 100%; max-width: 850px; margin: 0; text-align: left;">
            <div style="background-color: #ffffff; color: #1e293b; padding: 24px 28px; font-family: Arial, sans-serif; border: 1px solid #cbd5e1; text-align: left; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #0284c7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                {texto_dinamico}
            </div>
            <div style="margin-bottom: 16px; text-align: left;">
                <img src="cid:banner_ranking" alt="Banner" width="850" style="width: 100%; max-width: 850px; height: auto; display: block; border: 0; border-radius: 6px;" />
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 19px; margin: 0; padding: 0; border-radius: 6px; overflow: hidden; text-align: left;">
                <thead>
                    <tr style="background-color: #0d1527; color: #ffffff; text-align: left;">
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Intermediario</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Local</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Internacional</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Vida</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Auto, Hogar y Empresa</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                    <tr style="font-weight: bold; font-size: 21px; text-align: left;">
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748; text-align: left; font-size: 21px;">Total General</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748; text-align: left; font-size: 21px;">{format_moneda(tot_local)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748; text-align: left; font-size: 21px;">{format_moneda(tot_inter)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748; text-align: left; font-size: 21px;">{format_moneda(tot_vida)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748; text-align: left; font-size: 21px;">{format_moneda(tot_auto)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 💪"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg_alternative = MIMEMultipart("alternative")
    msg_alternative.attach(MIMEText(html_content, "html"))
    msg.attach(msg_alternative)

    banner_path = "Banner Ranking de Producción - 1.jpg"
    if os.path.exists(banner_path):
        try:
            with open(banner_path, "rb") as f:
                img_data = f.read()
            img_mime = MIMEImage(img_data)
            img_mime.add_header('Content-ID', '<banner_ranking>')
            img_mime.add_header('Content-Disposition', 'inline', filename=banner_path)
            msg.attach(img_mime)
            print("Banner adjuntado internamente por CID con éxito.")
        except Exception as e:
            print(f"No se pudo adjuntar el banner local: {e}")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        destinatarios = [email.strip() for email in recipient_email.split(",") if email.strip()]
        server.sendmail(sender_email, destinatarios, msg.as_string())
        server.quit()
        print("¡Correo enviado con éxito!")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
