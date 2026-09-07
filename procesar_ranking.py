# -*- coding: utf-8 -*-
"""
Script: procesar_ranking.py
Descripción: Generación limpia de imagen completa (sin cortes) y envío de correo optimizado.
"""

from datetime import datetime
import json
import os
import re
import smtplib
import time
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import requests
from google import genai
from html2image import Html2Image

# --- CONFIGURACIÓN DE MULTI-CUENTAS ---
API_KEYS_GEMINI = [
    os.environ.get("GEMINI_API_KEY_4"),
    os.environ.get("GEMINI_API_KEY_3"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY")
]

LISTA_MAESTRA_AGENTES = [
    "Milvio Espinal", "Delkis Perez", "Sory Morla", "Indhira Mora", "Luis T Ortiz",
    "Ruddy Arias", "Leomayra Alcantara", "Marcos Adames", "Maria De La Cruz", "Indhira Santos",
    "Nicauris Benitez", "Mariela de León Minaya", "Mery Lopez", "Estefania Villegas (Rogers)", "Yudelfa Cuevas",
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

def obtener_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
    return ""

def obtener_datos_desde_drive_imagen(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print("Descargando imagen desde Google Drive...")
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"No se pudo descargar la imagen de Google Drive. Código HTTP: {response.status_code}")

    image_path = "temp_ranking_drive.jpg"
    with open(image_path, "wb") as f:
        f.write(response.content)

    img = Image.open(image_path)
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
    - Devuelve ÚNICAMENTE o exclusivamente el bloque JSON válido, sin texto adicional.
    """

    # Lista de modelos actuales recomendados con reintentos para mitigar picos de alta demanda (503)
    modelos_a_probar = ['gemini-3.6-flash', 'gemini-2.5-flash']
    texto_respuesta = None

    for index, api_key in enumerate(API_KEYS_GEMINI):
        if not api_key: 
            continue
        client = genai.Client(api_key=api_key)
        for modelo in modelos_a_probar:
            for intento in range(2): # Reintento automático por saturación temporal
                try:
                    print(f"Intentando con {modelo} (Key #{index + 1}, Intento {intento + 1})...")
                    response = client.models.generate_content(model=modelo, contents=[img, prompt])
                    if response and response.text:
                        texto_respuesta = response.text
                        break
                except Exception as e:
                    print(f" -> Falló con {modelo}: {e}")
                    time.sleep(2)
                    continue
            if texto_respuesta: 
                break
        if texto_respuesta: 
            break

    if os.path.exists(image_path): 
        os.remove(image_path)
        
    if not texto_respuesta: 
        raise Exception("Error al procesar con IA: Los servidores están experimentando alta demanda. Por favor, intenta de nuevo en unos segundos.")

    match = re.search(r"\[.*\]", texto_respuesta, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        raise Exception(f"No se pudo interpretar la respuesta como JSON. Respuesta recibida:\n{texto_respuesta}")

def parse_monto(valor_str):
    try:
        return float(str(valor_str).replace(",", "")) if valor_str else 0.0
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
    if valor_num >= obtener_meta(ramo): return "background-color: #dcfce7; color: #15803d;"
    elif valor_num >= 1: return "background-color: #ffedd5; color: #c2410c;"
    else: return "background-color: #ffe4e6; color: #b91c1c;"

def procesar_y_enviar():
    sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION")
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")
    drive_file_id = "1YmAVaDyplF6CQ_gk2NZsEmLyjFpcFH9Y"

    try:
        datos_ranking = obtener_datos_desde_drive_imagen(drive_file_id)
    except Exception as e:
        print(f"Error: {e}")
        return

    datos_extraidos_dict = {item.get("intermediario", "").strip(): item for item in datos_ranking}
    datos_procesados = []

    for agente in LISTA_MAESTRA_AGENTES:
        match_item = next((v for k, v in datos_extraidos_dict.items() if agente.lower() in k.lower() or k.lower() in agente.lower()), None)
        
        val_local = parse_monto(match_item.get("local", "0.00")) if match_item else 0.0
        val_inter = parse_monto(match_item.get("inter", "0.00")) / 61.0 if match_item else 0.0
        val_vida = parse_monto(match_item.get("vida", "0.00")) if match_item else 0.0
        val_auto = parse_monto(match_item.get("auto", "0.00")) * 12.0 if match_item else 0.0

        datos_procesados.append({
            "intermediario": agente, "val_local": val_local, "val_inter": val_inter,
            "val_vida": val_vida, "val_auto": val_auto
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
            falta = obtener_meta(ramo) - valor
            if ramo == "auto":
                return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span>"
            return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span><br><span style='font-size: 15px; color: #c2410c; font-weight: bold; padding-left: 20px;'>— Te faltan {format_moneda(falta)} para ganar!</span>"

    meses_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    mes_actual = meses_es.get(datetime.now().month, "mes")

    datos_procesados.sort(key=lambda x: (x["val_local"], x["val_inter"], x["val_vida"], x["val_auto"]), reverse=True)

    tot_local = sum(i["val_local"] for i in datos_procesados)
    tot_inter = sum(i["val_inter"] for i in datos_procesados)
    tot_vida = sum(i["val_vida"] for i in datos_procesados)
    tot_auto = sum(i["val_auto"] for i in datos_procesados)

    filas_html = ""
    for fila in datos_procesados:
        filas_html += f"""
        <tr>
            <td style="background-color: #ffffff; color: #1e293b; padding: 16px 20px; font-weight: bold; border: 1px solid #cbd5e1; font-size: 19px;">{fila['intermediario']}</td>
            <td style="{obtener_color('local', fila['val_local'])} padding: 16px 20px; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(fila['val_local'])}</td>
            <td style="{obtener_color('inter', fila['val_inter'])} padding: 16px 20px; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(fila['val_inter'])}</td>
            <td style="{obtener_color('vida', fila['val_vida'])} padding: 16px 20px; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(fila['val_vida'])}</td>
            <td style="{obtener_color('auto', fila['val_auto'])} padding: 16px 20px; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(fila['val_auto'])}</td>
        </tr>
        """

    texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b; text-align: left;">
        <div style="font-size: 28px; font-weight: bold; color: #0284c7; margin-bottom: 14px;">🔥 EQUIPO MEGAPODEROSOS 💪</div>
        <div style="font-size: 22px; font-weight: bold; color: #334155; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px;">📊 Numeritos del mes de {mes_actual.capitalize()}</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 19px;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-bottom: 20px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px;">🏆 TOP 3 &mdash; LOCAL</div>
                    1. {format_top_item(top_local[0]['intermediario'], 'local', top_local[0]['val_local'])}<br>
                    2. {format_top_item(top_local[1]['intermediario'], 'local', top_local[1]['val_local'])}<br>
                    3. {format_top_item(top_local[2]['intermediario'], 'local', top_local[2]['val_local'])}
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-bottom: 20px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px;">🏆 TOP 3 &mdash; INTERNACIONAL</div>
                    1. {format_top_item(top_inter[0]['intermediario'], 'inter', top_inter[0]['val_inter'])}<br>
                    2. {format_top_item(top_inter[1]['intermediario'], 'inter', top_inter[1]['val_inter'])}<br>
                    3. {format_top_item(top_inter[2]['intermediario'], 'inter', top_inter[2]['val_inter'])}
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-top: 10px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px;">🏆 TOP 3 &mdash; VIDA</div>
                    1. {format_top_item(top_vida[0]['intermediario'], 'vida', top_vida[0]['val_vida'])}<br>
                    2. {format_top_item(top_vida[1]['intermediario'], 'vida', top_vida[1]['val_vida'])}<br>
                    3. {format_top_item(top_vida[2]['intermediario'], 'vida', top_vida[2]['val_vida'])}
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-top: 10px;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px;">🏆 TOP 3 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    1. {format_top_item(top_auto[0]['intermediario'], 'auto', top_auto[0]['val_auto'])}<br>
                    2. {format_top_item(top_auto[1]['intermediario'], 'auto', top_auto[1]['val_auto'])}<br>
                    3. {format_top_item(top_auto[2]['intermediario'], 'auto', top_auto[2]['val_auto'])}
                </td>
            </tr>
        </table>
        <div style="margin-top: 16px; font-size: 19px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 16px; font-weight: bold;">
            A continuación, el detalle completo de la producción:
        </div>
    </div>
    """

    banner_base64 = obtener_imagen_base64("Banner Ranking de Producción - 1.jpg")

    html_para_imagen = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 15px;">
        <div style="width: 850px; margin: 0 auto;">
            <div style="background-color: #ffffff; padding: 24px 28px; border: 1px solid #cbd5e1; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #0284c7;">
                {texto_dinamico}
            </div>
            {"<div style='margin-bottom: 16px;'><img src='" + banner_base64 + "' style='width: 100%; max-width: 850px; height: auto; display: block; border-radius: 6px;' /></div>" if banner_base64 else ""}
            <table style="width: 100%; border-collapse: collapse; font-size: 19px; border-radius: 6px; overflow: hidden;">
                <thead>
                    <tr style="background-color: #0d1527; color: #ffffff;">
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Intermediario</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Local</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Internacional</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Vida</th>
                        <th style="padding: 16px; text-align: left; border: 1px solid #2d3748; font-size: 21px;">Auto, Hogar y Empresa</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                    <tr style="font-weight: bold; font-size: 21px;">
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748;">Total General</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748;">{format_moneda(tot_local)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748;">{format_moneda(tot_inter)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748;">{format_moneda(tot_vida)}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 16px; border: 1px solid #2d3748;">{format_moneda(tot_auto)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    html_para_correo = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 15px;">
        <div style="width: 100%; max-width: 850px; margin: 0 auto;">
            <div style="background-color: #ffffff; padding: 24px 28px; border: 1px solid #cbd5e1; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #0284c7;">
                {texto_dinamico}
            </div>
            <div style="margin-bottom: 16px; color: #64748b; font-style: italic;">
                (La imagen completa del ranking va adjunta en este correo).
            </div>
        </div>
    </body>
    </html>
    """

    image_filename = f"ranking_{mes_actual}.png"
    print("Transformando el contenido en una imagen completa y limpia...")
    try:
        hti = Html2Image(
            output_path='.',
            custom_flags=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        hti.screenshot(
            html_str=html_para_imagen, 
            save_as=image_filename, 
            size=(890, 3200)
        )
        print(f"¡Imagen generada con éxito como '{image_filename}'!")
    except Exception as e:
        print(f"Error al generar la imagen: {e}")

    msg = MIMEMultipart()
    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 💪"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    
    msg.attach(MIMEText(html_para_correo, "html"))

    if os.path.exists(image_filename):
        try:
            with open(image_filename, "rb") as f:
                img_data = f.read()
            msg.attach(MIMEImage(img_data, name=image_filename))
            print("Imagen adjuntada al correo correctamente.")
        except Exception as e:
            print(f"No se pudo adjuntar la imagen: {e}")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, [e.strip() for e in recipient_email.split(",") if e.strip()], msg.as_string())
        server.quit()
        print("¡Correo enviado con éxito!")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
