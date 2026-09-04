import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def procesar_y_enviar():
    banner_path = "banner.png"

    # Credenciales de envío (si no usas GitHub Secrets, pon tus datos aquí)
    sender_email = os.environ.get("EMAIL_USER", "jfebrierg@gmail.com")
    password = os.environ.get("EMAIL_PASSWORD", "COntrace120675")
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "jfebrierg@gmail.com")

    # Diagnóstico para verificar la carga de credenciales
    print("--- VERIFICACIÓN DE CREDENCIALES ---")
    print(f"EMAIL_USER: {sender_email}")
    print(f"EMAIL_RECIPIENT: {recipient_email}")
    print(f"EMAIL_PASSWORD configurado: {'SÍ' if password and password != 'TU_CONTRASEÑA_DE_APLICACION_AQUI' else 'NO/DEFAULT'}")
    print("-----------------------------------")

    if not password or password == "TU_CONTRASEÑA_DE_APLICACION_AQUI":
        print("ERROR: Debes colocar tu contraseña de aplicación de Gmail de 16 caracteres en el código o en los Secrets de GitHub.")
        return

    datos_ranking = [
        {"intermediario": "Cliente Directo Megacentro", "local": "115,507.18", "inter": "0.00", "vida": "3,795.00", "auto": "0.00", "total": "119,302.18"},
        {"intermediario": "Luisa Gonzalez", "local": "28,326.00", "inter": "12,915.53", "vida": "910.00", "auto": "0.00", "total": "42,151.53"},
        {"intermediario": "Marcos Adames", "local": "14,173.00", "inter": "0.00", "vida": "520.00", "auto": "12,566.53", "total": "27,259.53"},
        {"intermediario": "Nicauris Benitez", "local": "0.00", "inter": "21,332.92", "vida": "0.00", "auto": "0.00", "total": "21,332.92"},
        {"intermediario": "Angela Vidal", "local": "9,755.25", "inter": "0.00", "vida": "260.00", "auto": "3,542.62", "total": "13,557.87"},
        {"intermediario": "Ninfa Perez", "local": "8,660.00", "inter": "0.00", "vida": "180.00", "auto": "0.00", "total": "8,840.00"},
        {"intermediario": "Ana Veloz", "local": "7,186.75", "inter": "0.00", "vida": "260.00", "auto": "0.00", "total": "7,446.75"},
        {"intermediario": "Dioselina Ramos", "local": "7,015.00", "inter": "0.00", "vida": "130.00", "auto": "0.00", "total": "7,145.00"},
        {"intermediario": "Wilfredo Vicente", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "5,417.90", "total": "5,417.90"},
        {"intermediario": "Joan Danis", "local": "4,610.00", "inter": "0.00", "vida": "180.00", "auto": "596.07", "total": "5,386.07"},
        {"intermediario": "Eddy Concepcion", "local": "3,530.00", "inter": "0.00", "vida": "0.00", "auto": "0.00", "total": "3,530.00"},
        {"intermediario": "Maria De La Cruz", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "36.02", "total": "36.02"},
        {"intermediario": "Leomayra Alcantara", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "-319.89", "total": "-319.89"},
        {"intermediario": "Estefania Villegas", "local": "0.00", "inter": "0.00", "vida": "0.00", "auto": "-4,329.56", "total": "-4,329.56"},
        {"intermediario": "Julissa Rosario", "local": "0.00", "inter": "24,756.24", "vida": "0.00", "auto": "-73,122.26", "total": "-48,366.02"},
    ]

    filas_html = ""
    for fila in datos_ranking:
        filas_html += f"""
        <tr>
            <td style="background-color: #1a2332; color: #ffffff; padding: 8px; font-weight: bold; border: 1px solid #2d3748;">{fila['intermediario']}</td>
            <td style="background-color: #fde8e8; color: #000000; padding: 8px; text-align: right; border: 1px solid #fbd5d5;">${fila['local']}</td>
            <td style="background-color: #fde8e8; color: #000000; padding: 8px; text-align: right; border: 1px solid #fbd5d5;">${fila['inter']}</td>
            <td style="background-color: #fde8e8; color: #000000; padding: 8px; text-align: right; border: 1px solid #fbd5d5;">${fila['vida']}</td>
            <td style="background-color: #fde8e8; color: #000000; padding: 8px; text-align: right; border: 1px solid #fbd5d5;">${fila['auto']}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #ffffff; margin: 0; padding: 10px;">
        <div style="max-width: 650px; margin: 0 auto;">
            <div style="width: 100%; text-align: center; margin-bottom: 0px;">
                <img src="cid:banner_megapoderosos" alt="Ranking de Producción MEGAPODEROSOS" style="width: 100%; max-width: 650px; height: auto; display: block;">
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
                    <tr style="font-weight: bold;">
                        <td style="background-color: #0d1527; color: #ffffff; padding: 10px; border: 1px solid #2d3748;">Total General</td>
                        <td style="background-color: #f87171; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #ef4444;">$198,763.18</td>
                        <td style="background-color: #f87171; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #ef4444;">$59,004.69</td>
                        <td style="background-color: #f87171; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #ef4444;">$6,235.00</td>
                        <td style="background-color: #f87171; color: #ffffff; padding: 10px; text-align: right; border: 1px solid #ef4444;">-$55,612.57</td>
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
        image.add_header("Content-Disposition", "inline", filename="banner.png")
        msg.attach(image)
    else:
        print(f"Advertencia: No se encontró la imagen {banner_path} en el directorio del script.")

    try:
        print("Intentando conectar con el servidor SMTP de Gmail...")
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
