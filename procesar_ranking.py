import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def parse_monto(valor_str):
    """ Convierte cadenas como '115,507.18' o '-73,122.26' a un float de Python """
    try:
        return float(str(valor_str).replace(",", ""))
    except ValueError:
        return 0.0

def obtener_color(ramo, valor_num):
    """ Retorna el color de fondo y de texto según la regla de semáforo """
    # Verde: #22c55e (texto blanco), Naranja: #f97316 (texto blanco), Rojo: #ef4444 (texto blanco)
    color_verde = "background-color: #22c55e; color: #ffffff;"
    color_naranja = "background-color: #f97316; color: #ffffff;"
    color_rojo = "background-color: #ef4444; color: #ffffff;"

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
    banner_path = "reporte_diario.png"

    sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "AQUI_TU_CONTRASEÑA_DE_APLICACION")
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")

    # Lista con los 55 miembros del equipo
    datos_ranking = [
        {"intermediario": "Cliente Directo Megacentro", "local": "115,507.18", "inter": "0.00", "vida": "3,795.00", "auto": "0.00"},
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

    # Ordenar la lista de mayor a menor con prioridad en la columna Local, luego Internacional, Vida y Auto
    datos_ranking.sort(
        key=lambda x: (
            parse_monto(x["local"]),
            parse_monto(x["inter"]),
            parse_monto(x["vida"]),
            parse_monto(x["auto"])
        ),
        reverse=True
    )

    # Calcular los totales generales acumulados
    tot_local = sum(parse_monto(item["local"]) for item in datos_ranking)
    tot_inter = sum(parse_monto(item["inter"]) for item in datos_ranking)
    tot_vida = sum(parse_monto(item["vida"]) for item in datos_ranking)
    tot_auto = sum(parse_monto(item["auto"]) for item in datos_ranking)

    # Construir filas de la tabla HTML con colores de semáforo
    filas_html = ""
    for fila in datos_ranking:
        val_local = parse_monto(fila["local"])
        val_inter = parse_monto(fila["inter"])
        val_vida = parse_monto(fila["vida"])
        val_auto = parse_monto(fila["auto"])

        style_local = obtener_color("local", val_local)
        style_inter = obtener_color("inter", val_inter)
        style_vida = obtener_color("vida", val_vida)
        style_auto = obtener_color("auto", val_auto)

        filas_html += f"""
        <tr>
            <td style="background-color: #1a2332; color: #ffffff; padding: 8px; font-weight: bold; border: 1px solid #2d3748;">{fila['intermediario']}</td>
            <td style="{style_local} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${fila['local']}</td>
            <td style="{style_inter} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${fila['inter']}</td>
            <td style="{style_vida} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${fila['vida']}</td>
            <td style="{style_auto} padding: 8px; text-align: right; border: 1px solid #2d3748; font-weight: bold;">${fila['auto']}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #ffffff; margin: 0; padding: 10px;">
        <div style="max-width: 700px; margin: 0 auto;">
            <!-- Banner superior -->
            <div style="width: 100%; text-align: center; margin-bottom: 15px;">
                <img src="cid:banner_megapoderosos" alt="Reporte de Producción MEGAPODEROSOS" style="width: 100%; max-width: 700px; height: auto; display: block; margin: 0 auto;">
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
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
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748;">Total General</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #2d3748;">${tot_local:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #2d3748;">${tot_inter:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #2d3748;">${tot_vida:,.2f}</td>
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #2d3748;">${tot_auto:,.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["Subject"] = "Producción General - MEGAPODEROSOS"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText(html_content, "html"))

    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            img_data = f.read()
        image = MIMEImage(img_data)
        image.add_header("Content-ID", "<banner_megapoderosos>")
        image.add_header("Content-Disposition", "inline", filename="reporte_diario.png")
        msg.attach(image)

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
