# -*- coding: utf-8 -*-
"""
Script: procesar_ranking.py
Descripción: Procesamiento de ranking por IA con sistema multi-cuenta (fallback de API Keys)
y un motor combinatorio avanzado de más de 1,000 variaciones de mensajes motivacionales.
"""

from datetime import datetime
import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image
import requests
from google import genai

# --- CONFIGURACIÓN DE MULTI-CUENTAS (GEMINI_API_KEY_2 primero, luego GEMINI_API_KEY) ---
API_KEYS_GEMINI = [
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

# --- MOTOR COMBINATORIO DE MENSAJES (>1,000 COMBINACIONES ÚNICAS) ---
BANCO_BAJO = {
    "aperturas": [
        "Analizando cómo vamos en este segmento,",
        "Revisando los números actuales de este ramo,",
        "Viendo el comportamiento del equipo en este producto,",
        "Haciendo una pausa para evaluar este indicador,",
        "Para nadie es un secreto que en este ramo"
    ],
    "nucleos": [
        "tenemos un margen de mejora gigante y toca ponerse las pilas para revertir este inicio",
        "estamos por debajo de nuestro potencial real y necesitamos apretar el paso con actitud",
        "el tablero nos pide un cambio de ritmo urgente y salir a buscar esas cotizaciones pendientes",
        "tenemos tarea pendiente y hay que redoblar esfuerzos para activar esta cartera",
        "las oportunidades están ahí esperando, solo falta dar el primer toque de puerta con energía"
    ],
    "cierres": [
        "¡Confié plenamente en la capacidad de este equipo para darle la vuelta!",
        "¡Sé de qué estamos hechos los MEGAPODEROSOS, a meterle toda la fuerza!",
        "¡Vamos a demostrar nuestra casta comercial esta misma semana!",
        "¡Es momento de sacar el carácter y poner los números donde deben estar!",
        "¡A mover el teléfono y arrancar con fuerza este tramo!"
    ]
}

BANCO_MEDIO = {
    "aperturas": [
        "El pulso del equipo en este ramo",
        "Viendo el ritmo que llevamos en este segmento,",
        "Analizando el avance de la semana en este producto,",
        "El esfuerzo constante que se ve reflejado aquí",
        "Paso a paso estamos consolidando el trabajo en este ramo y"
    ],
    "nucleos": [
        "nos muestra un desempeño estable que demuestra el compromiso diario de todos",
        "camina con buen paso y una disciplina comercial que da gusto ver",
        "mantiene una inercia positiva muy interesante que debemos cuidar y potenciar",
        "refleja el enfoque correcto aunque todavía tenemos espacio para un último empujón",
        "va tomando forma sólida gracias al trabajo coordinado del grupo"
    ],
    "cierres": [
        "¡A mantenernos firmes para asegurar un cierre de mes extraordinario!",
        "¡Sigamos con esa misma energía rumbo a la meta establecida!",
        "¡Excelente constancia, vamos a mantener el pie en el acelerador!",
        "¡Este es el camino correcto, sigamos sumando con orgullo!",
        "¡A consolidar estos resultados con el talento que nos caracteriza!"
    ]
}

BANCO_ALTO = {
    "aperturas": [
        "¡Lo que estamos logrando en este ramo",
        "¡Qué nivel tan impresionante estamos mostrando en este segmento,",
        "¡El rendimiento colectivo en este producto",
        "¡Imparables y con una energía desbordante,",
        "¡De 10 absoluto el trabajo que se está haciendo en este ramo y"
    ],
    "nucleos": [
        "es simplemente digno de aplaudir y refleja el verdadero ADN de los MEGAPODEROSOS",
        "supera cualquier expectativa demostrando la categoría y experiencia de este equipo",
        "marca un precedente brutal de lo que somos capaces cuando nos lo proponemos",
        "está rompiendo esquemas gracias a la entrega y el profesionalismo de cada uno",
        "nos posiciona en lo más alto dejando claro quién manda en la cancha"
    ],
    "cierres": [
        "¡Sigan volando alto y comiéndose el resto del año con este mismo hambre de triunfo!",
        "¡Esto es liderazgo puro, a disfrutar el éxito y seguir inspirando!",
        "¡Qué manera tan brutal de trabajar, sigamos haciendo historia!",
        "¡Aplausos de pie para todos los involucrados, a mantener la cima!",
        "¡Con esta misma pasión nadie nos para!"
    ]
}

BANCO_INTERNACIONAL = {
    "aperturas": [
        "Tratándose de nuestro producto internacional,",
        "En cuanto al ramo internacional, reconocido por su alta exigencia,",
        "Evaluando el terreno internacional,",
        "Mirando de frente al reto internacional,",
        "Sabemos que el segmento internacional es uno de los más retadores y"
    ],
    "nucleos": [
        "cada paso al frente cuenta el doble y merece todo nuestro reconocimiento",
        "ponerse la camiseta aquí demuestra una visión comercial de otro nivel",
        "romper el hielo en este producto exige una disciplina y destreza superior",
        "cada gestión exitosa en este campo resalta el esfuerzo titánico del equipo",
        "enfrentar este desafío tan complejo demuestra el calibre de nuestros agentes"
    ],
    "cierres": [
        "¡Valoramos enormemente ese esfuerzo extra que marca la diferencia!",
        "¡A seguir conquistando este mercado tan exclusivo con orgullo!",
        "¡Su valentía ante los retos más difíciles nos enorgullece a todos!",
        "¡Sigamos abriendo brecha donde pocos se atreven!",
        "¡Un reconocimiento especial por asumir este gran desafío con categoría!"
    ]
}

def generar_mensaje_combinatorio(banco, semilla=0):
    semana = datetime.now().isocalendar()[1]
    idx_a = (semana + semilla) % len(banco["aperturas"])
    idx_n = (semana * 3 + semilla) % len(banco["nucleos"])
    idx_c = (semana * 7 + semilla) % len(banco["cierres"])
    return f"{banco['aperturas'][idx_a]} {banco['nucleos'][idx_n]}. {banco['cierres'][idx_c]}"

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
    print("Analizando imagen con IA (Sistema multi-cuenta activo con google.genai y gemini-3.6-flash)...")
    
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

    texto_respuesta = None
    for index, api_key in enumerate(API_KEYS_GEMINI):
        if not api_key:
            print(f"Aviso: La API Key #{index + 1} no está configurada o está vacía.")
            continue
        try:
            print(f"Intentando con la cuenta / API Key #{index + 1}...")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[img, prompt]
            )
            texto_respuesta = response.text
            print(f"¡Éxito utilizando la cuenta #{index + 1}!")
            break
        except Exception as e:
            error_msg = str(e)
            print(f"Aviso con la cuenta #{index + 1}: {error_msg}")
            if "429" in error_msg or "Quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print("Límite de cuota alcanzado. Cambiando a la siguiente cuenta de respaldo...")
                continue
            else:
                raise e

    if os.path.exists(image_path):
        os.remove(image_path)

    if not texto_respuesta:
        raise Exception("Se agotó la cuota o no hay claves válidas configuradas en todas las cuentas de Google.")

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

    count_local = sum(1 for x in datos_procesados if x["val_local"] > 0)
    count_inter = sum(1 for x in datos_procesados if x["val_inter"] > 0)
    count_vida = sum(1 for x in datos_procesados if x["val_vida"] > 0)
    count_auto = sum(1 for x in datos_procesados if x["val_auto"] > 0)

    def evaluar_participacion_ramo(ramo_key, count, semilla):
        if ramo_key == "inter":
            if count == 0:
                msg_base = generar_mensaje_combinatorio(BANCO_BAJO, semilla_extra=semilla)
                contexto = "Aún no tenemos participantes en este ramo. ¡Es la oportunidad perfecta para romper el hielo en uno de los productos más retadores!"
            else:
                msg_base = generar_mensaje_combinatorio(BANCO_INTERNACIONAL, semilla_extra=semilla)
                contexto = f"Tenemos <b>{count}</b> persona{'s' if count != 1 else ''} participando, resaltando el gran esfuerzo por ser uno de los productos más retadores."
        else:
            if count < 10:
                msg_base = generar_mensaje_combinatorio(BANCO_BAJO, semilla_extra=semilla)
                contexto = f"Tenemos solo <b>{count}</b> persona{'s' if count != 1 else ''} participando, por lo que hay que ponerse las pilas."
            elif 10 <= count <= 15:
                msg_base = generar_mensaje_combinatorio(BANCO_MEDIO, semilla_extra=semilla)
                contexto = f"Tenemos <b>{count}</b> personas participando. ¡Vamos avanzando con buen ritmo!"
            else:
                msg_base = generar_mensaje_combinatorio(BANCO_ALTO, semilla_extra=semilla)
                contexto = f"Tenemos <b>{count}</b> personas participando, demostrando que sí se puede."
        return f"{contexto} <i>&ldquo;{msg_base}&rdquo;</i>"

    estado_local = evaluar_participacion_ramo("local", count_local, semilla=1)
    estado_inter = evaluar_participacion_ramo("inter", count_inter, semilla=4)
    estado_vida = evaluar_participacion_ramo("vida", count_vida, semilla=2)
    estado_auto = evaluar_participacion_ramo("auto", count_auto, semilla=3)

    counts = [count_local, count_vida, count_auto]
    if any(c < 10 for c in counts):
        box_bg, box_border, box_color = "#fffbeb", "#f59e0b", "#92400e"
    elif any(10 <= c <= 15 for c in counts):
        box_bg, box_border, box_color = "#fefce8", "#eab308", "#854d0e"
    else:
        box_bg, box_border, box_color = "#f0fdf4", "#22c55e", "#166534"

    mensaje_dinamico_atencion = f"""
    <div style="background-color: {box_bg}; border-left: 5px solid {box_border}; padding: 18px 22px; margin-top: 20px; margin-bottom: 16px; border-radius: 6px; font-size: 17px; color: {box_color}; text-align: left; line-height: 1.6;">
        <div style="font-weight: bold; margin-bottom: 14px; font-size: 20px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 8px;">Participación por Producto:</div>
        <div style="margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed rgba(0,0,0,0.08);"><strong>Local:</strong> {estado_local}</div>
        <div style="margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed rgba(0,0,0,0.08); background-color: rgba(255, 255, 255, 0.7); padding: 8px 12px; border-radius: 4px; border-left: 4px solid #3182ce;"><strong>Internacional:</strong> {estado_inter}</div>
        <div style="margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed rgba(0,0,0,0.08);"><strong>Vida:</strong> {estado_vida}</div>
        <div><strong>Auto, Hogar y Empresa:</strong> {estado_auto}</div>
    </div>
    """

    top_local = sorted(datos_procesados, key=lambda x: x["val_local"], reverse=True)[:3]
    top_inter = sorted(datos_procesados, key=lambda x: x["val_inter"], reverse=True)[:3]
    top_vida = sorted(datos_procesados, key=lambda x: x["val_vida"], reverse=True)[:3]
    top_auto = sorted(datos_procesados, key=lambda x: x["val_auto"], reverse=True)[:3]

    def format_top_item(item, ramo, valor):
        if valor <= 0:
            return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(0.0)})</span>"
        if cumple_meta(ramo, valor):
            return f"<b>{item}</b> ⭐ <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span>"
        else:
            meta = obtener_meta(ramo)
            if ramo == "auto":
                return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span>"
            else:
                falta = meta - valor
                return f"<b>{item}</b> <span style='color: #64748b; font-weight: normal; font-size: 18px;'>({format_moneda(valor)})</span><br><span style='font-size: 15px; color: #c2410c; font-weight: bold; padding-left: 20px;'>— Faltan {format_moneda(falta)} para la meta</span>"

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
        <div style="font-size: 28px; font-weight: bold; color: #0284c7; margin-bottom: 14px; letter-spacing: 0.5px; text-align: left;">🔥 MEGAPODEROSOS 💪</div>
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

        {mensaje_dinamico_atencion}
        
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
                <a href="https://ibb.co/N21Ljnxt"><img src="https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg" alt="Banner" border="0" style="width: 100%; max-width: 850px; height: auto; display: block; border: 0; border-radius: 6px;" /></a>
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        destinatarios = [email.strip() for email in recipient_email.split(",") if email.strip()]
        server.sendmail(sender_email, destinatarios, msg.as_string())
        server.quit()
        print("¡Correo enviado con éxito! Título actualizado con éxito.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
