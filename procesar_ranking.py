import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def parse_monto(valor_str):
    """ Convierte cadenas como '115,507.18' o '-73,122.26' a un float de Python """
    try:
        return float(str(valor_str).replace(",", ""))
    except ValueError:
        return 0.0

def cumple_meta(ramo, valor_num):
    """ Retorna True si el valor alcanza o supera la meta mínima de su ramo """
    if ramo == "local":
        return valor_num >= 30000
    elif ramo == "inter":
        return valor_num >= 250
    elif ramo == "vida":
        return valor_num >= 3000
    elif ramo == "auto":
        return valor_num >= 100000
    return False

def obtener_color(ramo, valor_num):
    """ Retorna el color de fondo y de texto según el formato suave de la imagen """
    color_verde = "background-color: #dcfce7; color: #15803d;"
    color_naranja = "background-color: #ffedd5; color: #c2410c;"
    color_rojo = "background-color: #ffe4e6; color: #b91c1c;"

    if ramo == "local":
        if valor_num >= 30000:
            return color_verde
        elif valor_num >= 1:
            return color_naranja
        else:
            return color_rojo

    elif ramo == "inter":
        if valor_num >= 250:
            return color_verde
        elif valor_num >= 1:
            return color_naranja
        else:
            return color_rojo

    elif ramo == "vida":
        if valor_num >= 3000:
            return color_verde
        elif valor_num >= 1:
            return color_naranja
        else:
            return color_rojo

    elif ramo == "auto":
        if valor_num >= 100000:
            return color_verde
        elif valor_num >= 1:
            return color_naranja
        else:
            return color_rojo

    return "background-color: #ffffff; color: #000000;"

def procesar_y_enviar():
    sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION")
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")

    # URL directa de la imagen del banner alojada en ImgBB
    BANNER_URL = "https://i.ibb.co/F4sBwq6m/Banner-Ranking-de-Producci-n-1.jpg"

    # Obtener el mes en español automáticamente
    meses_es = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    mes_actual = meses_es.get(datetime.now().month, "mes")

    # Lista de miembros del equipo
    datos_ranking = [
        {"intermediario": "Luisa Gonzalez", "local": "28,326.00", "inter": "12,915.53", "vida": "910.00", "auto": "0.00"},
        {"intermediario": "Marcos Adames", "local": "14,173.00", "inter": "0.00", "vida": "520.00", "auto": "12,566.53"},
        {"intermediario": "Nicauris Benitez", "local": "0.00", "inter": "21,332.92", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Angela Vidal", "local": "9,755.25", "inter": "0.00", "vida": "260.00", "auto": "3,542.62"},
        {"intermediario": "Ninfa Perez", "local": "8,660.00", "inter": "0.00", "vida": "180.00", "auto": "0.00"},
        {"intermediario": "Ana Veloz", "local": "7,186.75", "inter": "0.00", "vida": "260.00", "auto": "0.00"},
        {"intermediario": "Dioselina Ramos", "local": "7,015.00", "inter": "0.00", "vida": "130.00", "auto": "0.00"},
        {"intermediario": "Wilfredo Vicente", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "5,417.90"},
        {"intermediario": "Joan Danis", "local": "4,610.00", "inter": "0.00", "vida": "180.00", "auto": "596.07"},
        {"intermediario": "Eddy Concepcion", "local": "3,530.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Maria De La Cruz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "36.02"},
        {"intermediario": "Leomayra Alcantara", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "-319.89"},
        {"intermediario": "Estefania Villegas", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "-4,329.56"},
        {"intermediario": "Julissa Rosario", "local": "0.00", "inter": "24,756.24", "vida": "0.00", "auto": "-73,122.26"},
        {"intermediario": "Milvio Espinal", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Delkis Perez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Sory Morla", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Indhira Mora", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Luis T Ortiz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Ruddy Arias", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Indhira Santos", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Mariela de León Minaya", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Mery Lopez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Yudelka Cuevas", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Vladimil Herrera", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Orquidea Feliz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Marisol Payano", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Jairo Martinez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Alsiwin Ruiz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Estarlin Acosta", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Eleuterio Fernandez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Angel Matos", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Ingrid Beras", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Kevin Ramirez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Eduardo Hernandez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Wanda Peña", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Belkis Sanchez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Aranechi Tejeda", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Felix Morillo", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Hander Perez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Amalfi Julissa Rodriguez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Charles Furment", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Angela Valerio", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Hugo Cruz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Jose Terrero", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Maribel Fernandez", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Esperanza Regalado", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "John Adams", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Maria Soriano", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Albertina Febles", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Franklin Graterol", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Cirilo Fermin", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Yolanda Cabrera", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"},
        {"intermediario": "Paula Herrera", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "0.00"}
    ]

    # Procesar valores aplicando transformaciones
    datos_procesados = []
    for item in datos_ranking:
        val_local = parse_monto(item["local"])
        val_inter = parse_monto(item["inter"]) / 61.0
        val_vida = parse_monto(item["vida"])
        val_auto = parse_monto(item["auto"]) * 12.0

        datos_procesados.append({
            "intermediario": item["intermediario"],
            "val_local": val_local,
            "val_inter": val_inter,
            "val_vida": val_vida,
            "val_auto": val_auto
        })

    # Extraer Top 3 por cada categoría de manera independiente
    top_local = sorted(datos_procesados, key=lambda x: x["val_local"], reverse=True)[:3]
    top_inter = sorted(datos_procesados, key=lambda x: x["val_inter"], reverse=True)[:3]
    top_vida = sorted(datos_procesados, key=lambda x: x["val_vida"], reverse=True)[:3]
    top_auto = sorted(datos_procesados, key=lambda x: x["val_auto"], reverse=True)[:3]

    # Función auxiliar para asignar el trofeo al lado del nombre solo si cumple la meta
    def format_top_item(item, ramo, valor):
        trofeo = " 🏆" if cumple_meta(ramo, valor) else ""
        return f"{item}{trofeo} <span style='color: #64748b; font-weight: normal;'>(${valor:,.2f})</span>"

    # Orden para la tabla completa (prioridad: Local > Internacional > Vida > Auto)
    datos_procesados.sort(
        key=lambda x: (x["val_local"], x["val_inter"], x["val_vida"], x["val_auto"]),
        reverse=True
    )

    # Calcular totales generales
    tot_local = sum(item["val_local"] for item in datos_procesados)
    tot_inter = sum(item["val_inter"] for item in datos_procesados)
    tot_vida = sum(item["val_vida"] for item in datos_procesados)
    tot_auto = sum(item["val_auto"] for item in datos_procesados)

    # Construir HTML de las filas de la pizarra completa
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
            <td style="background-color: #ffffff; color: #1e293b; padding: 8px; font-weight: bold; border: 1px solid #cbd5e1; text-align: left;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_local:,.2f}</td>
            <td style="{style_inter} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_inter:,.2f}</td>
            <td style="{style_vida} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_vida:,.2f}</td>
            <td style="{style_auto} padding: 8px; text-align: right; border: 1px solid #cbd5e1; font-weight: bold;">${val_auto:,.2f}</td>
        </tr>
        """

    # Bloque de texto superior con fondo blanco y diseño limpio y profesional
    texto_dinamico = f"""
    <div style="font-family: Arial, sans-serif; color: #1e293b;">
        <div style="font-size: 16px; font-weight: bold; color: #0284c7; margin-bottom: 6px; letter-spacing: 0.5px;">
            🚀 ¡MEGAPODEROSOS!
        </div>
        <div style="font-size: 14px; font-weight: bold; color: #334155; margin-bottom: 14px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            📊 Reporte de Numeritos &mdash; {mes_actual.capitalize()}
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
        
        <div style="margin-top: 12px; font-size: 12px; color: #475569; border-top: 1px solid #e2e8f0; padding-top: 10px; text-align: center;">
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
        <div style="max-width: 850px; margin: 0; text-align: left; font-size: 0; line-height: 0;">
            
            <!-- Tarjeta de Encabezado con Fondo Blanco e impacto visual -->
            <div style="background-color: #ffffff; color: #1e293b; padding: 20px 24px; font-size: 13px; line-height: 1.5; font-family: Arial, sans-serif; border: 1px solid #cbd5e1; text-align: left; margin-bottom: 12px; border-radius: 8px; border-left: 5px solid #0284c7; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                {texto_dinamico}
            </div>

            <!-- Banner Superior -->
            <img src="{BANNER_URL}" alt="Banner Ranking de Producción" style="width: 100%; max-width: 850px; height: auto; display: block; border: 0; margin: 0 0 12px 0; padding: 0; border-radius: 6px;">

            <!-- Tabla de Producción (Pizarra completa) -->
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin: 0; padding: 0; line-height: normal; border-radius: 6px; overflow: hidden;">
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Producción General - MEGAPODEROSOS"
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
        print("¡Correo enviado exitosamente!")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
