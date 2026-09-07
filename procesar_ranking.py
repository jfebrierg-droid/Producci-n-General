# --- 1. PRIMERO: Generar la imagen del HTML ---
    image_filename = f"ranking_{mes_actual}.png"
    print("Transformando el contenido del correo en una imagen...")
    try:
        hti = Html2Image(output_path='.')
        hti.screenshot(
            html_str=html_content, 
            save_as=image_filename, 
            size=(890, 1400)
        )
        print(f"¡Imagen generada con éxito como '{image_filename}'!")
    except Exception as e:
        print(f"Error al generar la imagen desde el HTML: {e}")

    # --- 2. SEGUNDO: Enviar correo electrónico con el texto y la imagen adjunta ---
    msg = MIMEMultipart()  # Cambiamos a MIMEMultipart estándar para soportar adjuntos
    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 💪"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    
    # Adjuntar el contenido HTML en texto
    msg.attach(MIMEText(html_content, "html"))

    # Adjuntar la imagen generada
    if os.path.exists(image_filename):
        try:
            with open(image_filename, "rb") as f:
                img_data = f.read()
            img_attachment = MIMEImage(img_data, name=image_filename)
            msg.attach(img_attachment)
            print("Imagen adjuntada al correo correctamente.")
        except Exception as e:
            print(f"No se pudo adjuntar la imagen al correo: {e}")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        destinatarios = [email.strip() for email in recipient_email.split(",") if email.strip()]
        server.sendmail(sender_email, destinatarios, msg.as_string())
        server.quit()
        print("¡Correo enviado con éxito (con su imagen adjunta)! moldeado!")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return
