import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def parse_monto(valor_str):
    """ Convierte cadenas como '115,507.18' o '-73,122.26' a un float de Python """
    try:
        return float(str(valor_str).replace(",", ""))
    except ValueError:
        return 0.0

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
            <td style="background-color: #1a2332; color: #ffffff; padding: 8px; font-weight: bold; border: 1px solid #2d3748; text-align: left;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${val_local:,.2f}</td>
            <td style="{style_inter} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${val_inter:,.2f}</td>
            <td style="{style_vida} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${val_vida:,.2f}</td>
            <td style="{style_auto} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${val_auto:,.2f}</td>
        </tr>
        """

    # Generar texto dinámico con el Top 3 incluido automáticamente
    texto_dinamico = f"""
    ¡Hola, equipo <b>MEGAPODEROSOS</b>! 🚀<br><br>
    Compartimos el reporte oficial de Humano Seguros. ¡Un reconocimiento especial a nuestros líderes destacados en este periodo!<br><br>
    
    🏆 <b>TOP 3 - LOCAL:</b><br>
    1. {top_local[0]['intermediario']} (${top_local[0]['val_local']:,.2f})<br>
    2. {top_local[1]['intermediario']} (${top_local[1]['val_local']:,.2f})<br>
    3. {top_local[2]['intermediario']} (${top_local[2]['val_local']:,.2f})<br><br>

    🏆 <b>TOP 3 - INTERNACIONAL:</b><br>
    1. {top_inter[0]['intermediario']} (${top_inter[0]['val_inter']:,.2f})<br>
    2. {top_inter[1]['intermediario']} (${top_inter[1]['val_inter']:,.2f})<br>
    3. {top_inter[2]['intermediario']} (${top_inter[2]['val_inter']:,.2f})<br><br>

    🏆 <b>TOP 3 - VIDA:</b><br>
    1. {top_vida[0]['intermediario']} (${top_vida[0]['val_vida']:,.2f})<br>
    2. {top_vida[1]['intermediario']} (${top_vida[1]['val_vida']:,.2f})<br>
    3. {top_vida[2]['intermediario']} (${top_vida[2]['val_vida']:,.2f})<br><br>

    🏆 <b>TOP 3 - AUTO, HOGAR Y EMPRESA:</b><br>
    1. {top_auto[0]['intermediario']} (${top_auto[0]['val_auto']:,.2f})<br>
    2. {top_auto[1]['intermediario']} (${top_auto[1]['val_auto']:,.2f})<br>
    3. {top_auto[2]['intermediario']} (${top_auto[2]['val_auto']:,.2f})<br><br>

    ¡A seguir dando el máximo en cada ramo! A continuación, el detalle completo del banner y la pizarra general:
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #ffffff; margin: 0; padding: 10px; text-align: left;">
        <div style="max-width: 850px; margin: 0; text-align: left; font-size: 0; line-height: 0;">
            
            <!-- Bloque de Texto Dinámico con el Top 3 (PRIMERO) -->
            <div style="background-color: #0d1527; color: #f8fafc; padding: 15px 20px; font-size: 13px; line-height: 1.5; font-family: Arial, sans-serif; border-bottom: 2px solid #3b82f6; text-align: left; margin-bottom: 10px; border-radius: 6px;">
                {texto_dinamico}
            </div>

            <!-- Banner Superior -->
            <img src="{BANNER_URL}" alt="Banner Ranking de Producción" style="width: 100%; max-width: 850px; height: auto; display: block; border: 0; margin: 0; padding: 0;">

            <!-- Tabla de Producción (Pizarra completa intacta) -->
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin: 0; padding: 0; line-height: normal;">
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
