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

# BANCOS DE MENSAJES VARIADOS PARA EVITAR REPETICIÓN DURANTE EL AÑO
MENSAJES_BAJO = [
    (
        "⚠️ <b>¡Atención MEGAPODEROSOS!</b> Tenemos menos de 10 miembros con"
        " producción en este ramo. ¡Es momento de acelerar el paso y encender"
        " los motores para repuntar!"
    ),
    (
        "🚨 <b>¡Alerta de impulso!</b> Este producto cuenta con menos de 10"
        " asesores activos. ¡Vamos a ponernos las pilas y rescatar esos"
        " números antes de que cierre el período!"
    ),
    (
        "⚠️ <b>¡Equipo, a despertar!</b> Menos de 10 participantes registran"
        " resultados aquí. ¡Demostremos de qué estamos hechos y vamos a"
        " dinamizar las ventas!"
    ),
    (
        "⚡ <b>¡Atención especial requerida!</b> Este ramo tiene una"
        " participación menor a 10 personas. ¡Es hora de activar estrategias y"
        " empujar juntos hacia la meta!"
    ),
    (
        "⚠️ <b>¡Menos de 10 activos en este segmento!</b> MEGAPODEROSOS,"
        " necesitamos sacudirnos y meterle velocidad para cambiar este"
        " panorama cuanto antes."
    ),
    (
        "🚨 <b>¡Llamado de alerta!</b> La participación está por debajo de 10"
        " asesores en este producto. ¡Es nuestro momento de demostrar"
        " resiliencia y subir esos números!"
    ),
    (
        "⚠️ <b>¡Manos a la obra, equipo!</b> Con menos de 10 resultados en este"
        " ramo, necesitamos un golpe de timón urgente. ¡Vamos a motivarnos y"
        " salir a ganar!"
    ),
]

MENSAJES_MEDIO = [
    (
        "📈 <b>¡Vamos mejorando, equipo!</b> Ya contamos con un grupo activo"
        " entre 11 y 15 miembros en este ramo, pero aún hay espacio para"
        " escalar más. ¡Sigamos sumando!"
    ),
    (
        "🚀 <b>¡El ritmo va subiendo!</b> Entre 11 y 15 asesores ya tienen"
        " resultados en este producto. ¡Muy bien por el esfuerzo, vamos por"
        " más!"
    ),
    (
        "📊 <b>¡Se nota el progreso!</b> Este ramo muestra una participación"
        " en ascenso con 11-15 activos. ¡No aflojemos el paso, el objetivo"
        " está más cerca!"
    ),
    (
        "📈 <b>¡Excelente actitud de mejora!</b> Ya son varios los"
        " MEGAPODEROSOS aportando en este segmento (11-15 activos). ¡Sigamos"
        " impulsando los números!"
    ),
    (
        "🚀 <b>¡Vamos por el camino correcto!</b> Este producto ya cuenta con"
        " un buen bloque activo entre 11 y 15 agentes. ¡A mantener el enfoque"
        " y seguir escalando!"
    ),
    (
        "📈 <b>¡Buen avance en este ramo!</b> El rango de 11 a 15 miembros con"
        " resultados refleja nuestro esfuerzo constante. ¡A dar el último"
        " tirón para romper récords!"
    ),
    (
        "🚀 <b>¡La curva va hacia arriba!</b> Entre 11 y 15 MEGAPODEROSOS"
        " activos moviendo este producto. ¡Excelente trabajo intermedio,"
        " vamos por la cima!"
    ),
]

MENSAJES_ALTO = [
    (
        "🔥 <b>¡Imparables, MEGAPODEROSOS!</b> Gran ritmo de participación con"
        " 16 o más asesores generando resultados en este ramo. ¡Así se lidera!"
    ),
    (
        "🏆 <b>¡Excelente trabajo en equipo!</b> Superamos los 16 miembros"
        " activos en este producto. ¡Su constancia y energía son de otro nivel!"
    ),
    (
        "🌟 <b>¡Qué nivel de compromiso!</b> Contar con más de 16 personas"
        " produciendo aquí demuestra la casta de campeones que tenemos."
        " ¡Felicitaciones!"
    ),
    (
        "🔥 <b>¡Brillante desempeño!</b> Este ramo brilla con luz propia gracias"
        " a la participación masiva de 16 o más agentes. ¡Mantengamos este"
        " ritmo ganador!"
    ),
    (
        "💪 <b>¡Súper ritmo y gran motivación!</b> Más de 16 MEGAPODEROSOS"
        " activos dejando huella en este producto. ¡Sigamos arrasando con"
        " todo!"
    ),
    (
        "🏆 <b>¡Felicitaciones por el excelente ritmo!</b> Con 16 o más"
        " integrantes aportando resultados, demostramos por qué somos los"
        " MEGAPODEROSOS. ¡A seguir brillando!"
    ),
    (
        "🔥 <b>¡Paso firme y arrollador!</b> Contamos con más de 16 valiosos"
        " aportes en este ramo. ¡Una felicitación gigante por este ritmo"
        " excepcional!"
    ),
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


def seleccionar_mensaje_dinamico(lista_mensajes, semilla_extra=0):
    """Selecciona un mensaje único de la lista basado en el día del año y una semilla para garantizar que no se repita en las ejecuciones."""
    ahora = datetime.now()
    # Combinar día del año, hora y minuto para asegurar variación total incluso en ejecuciones múltiples
    indice = (
        ahora.timetuple().tm_yday * 7
        + ahora.hour
        + ahora.minute
        + semilla_extra
    ) % len(lista_mensajes)
    return lista_mensajes[indice]


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

    # CÁLCULO DINÁMICO DE MIEMBROS CON RESULTADOS (> 0) POR PRODUCTO
    count_local = sum(1 for x in datos_procesados if x["val_local"] > 0)
    count_vida = sum(1 for x in datos_procesados if x["val_vida"] > 0)
    count_auto = sum(1 for x in datos_procesados if x["val_auto"] > 0)

    # EVALUACIÓN DINÁMICA CON MENSAJES ROTATIVOS ÚNICOS POR RAMO
    def evaluar_participacion_ramo(nombre_ramo, count, semilla):
        if count < 10:
            msg_base = seleccionar_mensaje_dinamico(
                MENSAJES_BAJO, semilla_extra=semilla
            )
            return (
                f"<b>{nombre_ramo} ({count} miembros):</b><br>{msg_base}"
            )
        elif 10 <= count <= 15:
            msg_base = seleccionar_mensaje_dinamico(
                MENSAJES_MEDIO, semilla_extra=semilla
            )
            return (
                f"<b>{nombre_ramo} ({count} miembros):</b><br>{msg_base}"
            )
        else:  # >= 16
            msg_base = seleccionar_mensaje_dinamico(
                MENSAJES_ALTO, semilla_extra=semilla
            )
            return (
                f"<b>{nombre_ramo} ({count} miembros):</b><br>{msg_base}"
            )

    estado_local = evaluar_participacion_ramo("Local", count_local, semilla=1)
    estado_vida = evaluar_participacion_ramo("Vida", count_vida, semilla=2)
    estado_auto = evaluar_participacion_ramo(
        "Auto, Hogar y Empresa", count_auto, semilla=3
    )

    # Determinar el color del contenedor según el estado general de los productos
    counts = [count_local, count_vida, count_auto]
    if any(c < 10 for c in counts):
        box_bg = "#fffbeb"
        box_border = "#f59e0b"
        box_color = "#92400e"
    elif any(10 <= c <= 15 for c in counts):
        box_bg = "#fefce8"
        box_border = "#eab308"
        box_color = "#854d0e"
    else:
        box_bg = "#f0fdf4"
        box_border = "#22c55e"
        box_color = "#166534"

    mensaje_dinamico_atencion = f"""
    <div style="background-color: {box_bg}; border-left: 5px solid {box_border}; padding: 18px 22px; margin-top: 20px; margin-bottom: 16px; border-radius: 6px; font-size: 17px; color: {box_color}; text-align: left; line-height: 1.6;">
        <div style="font-weight: bold; margin-bottom: 14px; font-size: 20px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 8px;">📊 Estado Dinámico de Participación por Producto:</div>
        <div style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed rgba(0,0,0,0.08);">{estado_local}</div>
        <div style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed rgba(0,0,0,0.08);">{estado_vida}</div>
        <div>{estado_auto}</div>
    </div>
    """

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
                f"<b>{item}</b> 🏃‍♂️ <span style='color: #64748b; font-weight:"
                f" normal; font-size: 18px;'>({format_moneda(0.0)})</span>"
            )
        if cumple_meta(ramo, valor):
            return (
                f"<b>{item}</b> 💪 <span style='color: #64748b; font-weight:"
                f" normal; font-size: 18px;'>({format_moneda(valor)})</span>"
            )
        else:
            meta = obtener_meta(ramo)
            if ramo == "auto":
                return (
                    f"<b>{item}</b> 🏃‍♂️ <span style='color: #64748b; font-weight:"
                    f" normal; font-size: 18px;'>({format_moneda(valor)})</span>"
                )
            else:
                falta = meta - valor
                return (
                    f"<b>{item}</b> 🏃‍♂️ <span style='color: #64748b; font-weight:"
                    f" normal; font-size: 18px;'>({format_moneda(valor)})</span><br><span"
                    f" style='font-size: 15px; color: #c2410c; font-weight:"
                    f" bold; padding-left: 20px;'>— ¡En vía! Faltan"
                    f" {format_moneda(falta)}</span>"
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
            <td style="background-color: #ffffff; color: #1e293b; padding: 16px 20px; font-weight: bold; border: 1px solid #cbd5e1; text-align: left; font-size: 19px;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_local)}</td>
            <td style="{style_inter} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_inter)}</td>
            <td style="{style_vida} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_vida)}</td>
            <td style="{style_auto} padding: 16px 20px; text-align: left; border: 1px solid #cbd5e1; font-weight: bold; font-size: 19px;">{format_moneda(val_auto)}</td>
        </tr>
        """

    texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b; text-align: left;">
        <div style="font-size: 28px; font-weight: bold; color: #0284c7; margin-bottom: 14px; letter-spacing: 0.5px; text-align: left;">
            🚀 ¡MEGAPODEROSOS!
        </div>
        <div style="font-size: 22px; font-weight: bold; color: #334155; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; text-align: left;">
            📊 Numeritos del mes de {mes_actual.capitalize()}
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 19px; line-height: 1.6; text-align: left;">
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-bottom: 20px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">⬆️ TOP 3 &mdash; LOCAL</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_local[0]['intermediario'], 'local', top_local[0]['val_local'])}<br><br>
                        2. {format_top_item(top_local[1]['intermediario'], 'local', top_local[1]['val_local'])}<br><br>
                        3. {format_top_item(top_local[2]['intermediario'], 'local', top_local[2]['val_local'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-bottom: 20px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">⬆️ TOP 3 &mdash; INTERNACIONAL</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_inter[0]['intermediario'], 'inter', top_inter[0]['val_inter'])}<br><br>
                        2. {format_top_item(top_inter[1]['intermediario'], 'inter', top_inter[1]['val_inter'])}<br><br>
                        3. {format_top_item(top_inter[2]['intermediario'], 'inter', top_inter[2]['val_inter'])}
                    </div>
                </td>
            </tr>
            <tr>
                <td style="width: 50%; vertical-align: top; padding-right: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">⬆️ TOP 3 &mdash; VIDA</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_vida[0]['intermediario'], 'vida', top_vida[0]['val_vida'])}<br><br>
                        2. {format_top_item(top_vida[1]['intermediario'], 'vida', top_vida[1]['val_vida'])}<br><br>
                        3. {format_top_item(top_vida[2]['intermediario'], 'vida', top_vida[2]['val_vida'])}
                    </div>
                </td>
                <td style="width: 50%; vertical-align: top; padding-left: 16px; padding-top: 10px; text-align: left;">
                    <div style="color: #0284c7; font-weight: bold; margin-bottom: 10px; font-size: 19px; text-align: left;">⬆️ TOP 3 &mdash; AUTO, HOGAR Y EMPRESA</div>
                    <div style="color: #334155; text-align: left;">
                        1. {format_top_item(top_auto[0]['intermediario'], 'auto', top_auto[0]['val_auto'])}<br><br>
                        2. {format_top_item(top_auto[1]['intermediario'], 'auto', top_auto[1]['val_auto'])}<br><br>
                        3. {format_top_item(top_auto[2]['intermediario'], 'auto', top_auto[2]['val_auto'])}
                    </div>
                </td>
            </tr>
        </table>

        <!-- CONDICIÓN DINÁMICA ROTATIVA POR PRODUCTO -->
        {mensaje_dinamico_atencion}
        
        <div style="margin-top: 16px; font-size: 19px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 16px; text-align: left; font-weight: bold;">
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
            "¡Correo enviado con mensajes dinámicos rotativos sin repetición!"
        )
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


if __name__ == "__main__":
    procesar_y_enviar()
