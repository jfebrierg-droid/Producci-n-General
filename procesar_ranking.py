# -*- coding: utf-8 -*-
"""
Script: procesar_ranking.py
Descripción: Procesamiento de ranking por IA con sistema multi-cuenta (Gemini 4 -> 3 -> 2 -> 1)
y respaldo automático de OpenAI (ChatGPT - gpt-4o) para máxima disponibilidad.
Estructura MIME robusta para compatibilidad total con Outlook.
"""

import base64
from datetime import datetime
import json
import os
import re
import smtplib
import time
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate, make_msgid
from PIL import Image
import requests
from google import genai
from openai import OpenAI  # Importado para el respaldo de ChatGPT

# --- CONFIGURACIÓN DE MULTI-CUENTAS (Orden de prioridad estricto: 4 -> 3 -> 2 -> 1) ---
API_KEYS_GEMINI = [
    os.environ.get("GEMINI_API_KEY_4"),
    os.environ.get("GEMINI_API_KEY_3"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY")
]

# Lista maestra con TODOS los miembros del equipo MEGAPODEROSOS (Estefania Villegas actualizada a Rogers)
LISTA_MAESTRA_AGENTES = [
    "Milvio Espinal", "Delkis Perez", "Sory Morla", "Indhira Mora", "Luis T Ortiz",
    "Ruddy Arias", "Leomayra Alcantara", "Marcos Adames", "Maria De La Cruz", "Indhira Santos",
    "Nicauris Benitez", "Mariela de León Minaya", "Mery Lopez", "Estefania Villegas (Rogers)", "Yudelfa Cuevas",
    "Vladimil Herrera", "Orquidia Feliz", "Marisol Payano", "Jairo Martinez", "Alsiwin Ruiz",
    "Estarlin Acosta", "Eleuterio Fernandez", "Ninfa Perez", "Angel Matos", "Ingrid Beras",
    "Kevin Ramirez", "Eduardo Hernandez", "Ana Veloz", "Wanda Peña", "Joan Danis",
    "Belkis Sanchez", "Aranechi Tejeda", "Angela Vidal", "Felix Morillo", "Hander Perez",
    "Julissa Rosario", "Amalfi Julissa Rodriguez", "Charles Furment", "Angela Valerio", "Dioselina Ramos",
    "Luisa Gonzalez", "Hugo Cruz", "Jose Terrero", "Mercedes Fernandez", "Esperanza Regalado",
    "John Adams", "Maria Soriano", "Albertina Febles", "Franklin Graterol", "Cirilo Fermin",
    "Eddy Concepcion", "Yolanda Cabrera", "Paula Herrera", "Rafael Capellan", "Salvador Martinez",
    "Wilfredo Vicente"
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
    print("Analizando imagen con IA (Sistema multi-cuenta Gemini priorizando Key 4 -> 3 -> 2 -> 1)...")
    
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
            print(f"Aviso: La API Key #{4 - index} de Gemini no está configurada o está vacía.")
            continue
        
        client = genai.Client(api_key=api_key)
        
        for modelo in modelos_a_probar:
            exito_modelo = False
            for intento in range(3):
                try:
                    print(f"Intentando con Gemini API Key #{4 - index}, modelo {modelo} (intento {intento + 1})...")
                    response = client.models.generate_content(
                        model=modelo,
                        contents=[img, prompt]
                    )
                    texto_respuesta = response.text
                    exito_modelo = True
                    print(f"¡Éxito con el modelo {modelo} usando Gemini!")
                    break
                except Exception as e:
                    error_msg = str(e)
                    print(f"Aviso: {error_msg}")
                    if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg:
                        tiempo_espera = (intento + 1) * 3
                        print(f"Servidor de Gemini saturado (503). Esperando {tiempo_espera}s antes de reintentar...")
                        time.sleep(tiempo_espera)
                        continue
                    elif "429" in error_msg or "Quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        print("Límite de cuota alcanzado en Gemini. Probando siguiente opción...")
                        break
                    else:
                        break
            if exito_modelo:
                break
        if texto_respuesta:
            break

    # --- RESPALDO AUTOMÁTICO CON OPENAI (CHATGPT) SI GEMINI FALLA ---
    if not texto_respuesta:
        print("Gemini agotó sus intentos o presentó saturación. Activando respaldo con ChatGPT (OpenAI - gpt-4o)...")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if openai_key:
            try:
                client_openai = OpenAI(api_key=openai_key)
                
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                response_openai = client_openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=2000
                )
                texto_respuesta = response_openai.choices[0].message.content
                print("¡Éxito procesando la imagen con el respaldo de ChatGPT (OpenAI)!")
            except Exception as e_openai:
                print(f"Error también con el respaldo de OpenAI: {e_openai}")
        else:
            print("Aviso: La variable OPENAI_API_KEY no está configurada en los secretos de GitHub.")

    if os.path.exists(image_path):
        os.remove(image_path)

    if not texto_respuesta:
        raise Exception("Se agotaron todas las opciones de Gemini y el respaldo de ChatGPT debido a saturación o errores.")

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

    # Filtrar solo valores mayores a 0 para el Top 5
    top_local = sorted([x for x in datos_procesados if x["val_local"] > 0], key=lambda x: x["val_local"], reverse=True)[:5]
    top_inter = sorted([x for x in datos_procesados if x["val_inter"] > 0], key=lambda x: x["val_inter"], reverse=True)[:5]
    top_vida = sorted([x for x in datos_procesados if x["val_vida"] > 0], key=lambda x: x["val_vida"], reverse=True)[:5]
    top_auto = sorted([x for x in datos_procesados if x["val_auto"] > 0], key=lambda x: x["val_auto"], reverse=True)[:5]

    def generar_filas_top(lista_top, ramo):
        html_tops = ""
        for i in range(5):
            if i < len(lista_top):
                item = lista_top[i]
                val = item[f"val_{ramo}"]
                nombre = item['intermediario']
                
                if val <= 0:
                    detalle = f"<b>{nombre}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(0.0)})</span>"
                elif cumple_meta(ramo, val):
                    detalle = f"<b>{nombre}</b> 💪 <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(val)})</span>"
                else:
                    meta = obtener_meta(ramo)
                    if ramo == "auto":
                        detalle = f"<b>{nombre}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(val)})</span>"
                    else:
                        falta = meta - val
                        detalle = f"<b>{nombre}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(val)})</span><br><span style='font-size: 15px; color: #c2410c; font-weight: bold; padding-left: 20px;'>— Te faltan {format_moneda(falta)} para ganar!!</span>"
                
                html_tops += f"{i+1}. {detalle}<br>"
            else:
                html_tops += f"{i+1}. <span style='color: #0284c7; font-style: italic; font-weight: bold;'>Tú puedes estar en este Top</span><br>"
        return html_tops

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
        <div style="font-size: 28px; font-weight: bold; color: #0284c7; margin-bottom: 14px; letter-spacing: 0.5px; text-align: left;">🔥 EQUIPO MEGAPODEROSOS 💪</div>
        <div style="font-size: 22px; font-weight: bold; color: #334155; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; text-align: left;">📊 Numeritos del mes de {mes_actual.capitalize()}</div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 19px; line-height: 1.6; text-align: left;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-bottom: 25px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 5 &mdash; LOCAL</div>
                    <div style="color: #334155; text-align: left; font-size: 18px;">
                        {generar_filas_top(top_local, 'local')}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-bottom: 25px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 5 &mdash; INTERNACIONAL</div>
                    <div style="color: #334155; text-align: left; font-size: 18px;">
                        {generar_filas_top(top_inter, 'inter')}
                    </div>
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 5 &mdash; VIDA</div>
                    <div style="color: #334155; text-align: left; font-size: 18px;">
                        {generar_filas_top(top_vida, 'vida')}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">🏆 TOP 5 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    <div style="color: #334155; text-align: left; font-size: 18px;">
                        {generar_filas_top(top_auto, 'auto')}
                    </div>
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 20px; font-size: 19px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 16px; text-align: left; font-weight: bold;">
            A continuación, el detalle completo de la producción:
        </div>
    </div>
    """

    BANNER_URL = "https://raw.githubusercontent.com/jfebrierg-droid/Producci-n-General/refs/heads/main/Banner%20Ranking%20de%20Producci%C3%B3n%20-%201.jpg"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 10px; text-align: left;">
        <div style="width: 100%; max-width: 850px; margin: 0; text-align: left;">
            <div style="background-color: #ffffff; color: #1e293b; padding: 24px 28px; font-family: Arial, sans-serif; border: 1px solid #cbd5e1; text-align: left; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #0284c7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                {texto_dinamico}
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse; margin: 0 0 16px 0;">
                <tr>
                    <td align="center" style="padding: 0;">
                        <img
                            src="{BANNER_URL}"
                            alt="Ranking de Producción - MEGAPODEROSOS"
                            width="850"
                            style="display:block; width:850px; max-width:100%; height:auto; border:0; outline:none; text-decoration:none;"
                            border="0"
                        />
                    </td>
                </tr>
            </table>
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 💪"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)

    texto_plano = (
        f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS\n\n"
        "Este correo contiene información de producción del equipo."
    )
    msg.attach(MIMEText(texto_plano, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
