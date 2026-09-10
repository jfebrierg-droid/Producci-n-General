    # ============================================================
    # ENVÍO DEL CORREO - COMPATIBLE CON OUTLOOK
    # ============================================================

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.utils import formatdate, make_msgid

    # ------------------------------------------------------------
    # Crear estructura MIME
    # ------------------------------------------------------------
    msg = MIMEMultipart("related")

    msg["Subject"] = f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS 💪"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)

    # ID único para la imagen
    banner_cid = make_msgid(domain="megapoderosos.local")

    # ------------------------------------------------------------
    # Contenedor alternative
    # ------------------------------------------------------------
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    # ------------------------------------------------------------
    # Texto plano
    # ------------------------------------------------------------
    texto_plano = (
        f"Producción de {mes_actual.capitalize()} - MEGAPODEROSOS\n\n"
        "Este correo contiene información de producción del equipo.\n"
        "Si no puedes visualizar correctamente el contenido, utiliza "
        "un cliente de correo compatible con HTML."
    )

    msg_alternative.attach(
        MIMEText(texto_plano, "plain", "utf-8")
    )

    # ------------------------------------------------------------
    # IMPORTANTE:
    # Sustituir el CID del HTML por el CID generado dinámicamente
    # ------------------------------------------------------------
    html_content_outlook = html_content.replace(
        "cid:banner_ranking",
        f"cid:{banner_cid.strip('<>')}"
    )

    # ------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------
    msg_alternative.attach(
        MIMEText(html_content_outlook, "html", "utf-8")
    )

    # ------------------------------------------------------------
    # Adjuntar banner como imagen INLINE
    # ------------------------------------------------------------
    banner_path = "Banner Ranking de Producción - 1.jpg"

    if not os.path.exists(banner_path):
        print(
            f"ERROR: No se encontró el banner: {banner_path}"
        )
        return

    try:
        with open(banner_path, "rb") as f:
            img_data = f.read()

        banner_img = MIMEImage(img_data, _subtype="jpeg")

        # Content-ID EXACTAMENTE igual al utilizado en el HTML
        banner_img.add_header(
            "Content-ID",
            banner_cid
        )

        # Outlook necesita que sea tratado como contenido inline
        banner_img.add_header(
            "Content-Disposition",
            "inline",
            filename="Banner_Ranking.jpg"
        )

        # Evitar que Outlook lo trate como un adjunto convencional
        banner_img.add_header(
            "X-Attachment-Id",
            banner_cid.strip("<>")
        )

        msg.attach(banner_img)

        print("Banner preparado correctamente para Outlook.")

    except Exception as e:
        print(f"Error preparando el banner: {e}")
        return

    # ------------------------------------------------------------
    # ENVIAR CORREO
    # ------------------------------------------------------------
    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(sender_email, password)

        destinatarios = [
            email.strip()
            for email in recipient_email.split(",")
            if email.strip()
        ]

        server.sendmail(
            sender_email,
            destinatarios,
            msg.as_string()
        )

        server.quit()

        print("¡Correo enviado correctamente!")
        print("El banner fue incrustado como imagen INLINE.")

    except Exception as e:

        print(f"ERROR al enviar el correo: {e}")
