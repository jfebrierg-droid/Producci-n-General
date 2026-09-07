import os
from html2image import Html2Image

def generar_imagen_ranking_completa(datos_tabla, ruta_banner, archivo_salida="ranking_septiembre.jpg"):
    """
    Genera una imagen completa del ranking de producción incluyendo el banner,
    el tablero de datos con todas las filas de los agentes y la fila de totales al final,
    evitando que se corte la imagen.
    """
    
    # 1. Construir las filas dinámicamente de la tabla HTML
    filas_html = ""
    total_local = 0.0
    total_internacional = 0.0
    total_vida = 0.0
    total_auto_hogar = 0.0

    for agente in datos_tabla:
        # Sumatorios para la fila de totales
        total_local += agente.get('local', 0.0)
        total_internacional += agente.get('internacional', 0.0)
        total_vida += agente.get('vida', 0.0)
        total_auto_hogar += agente.get('auto_hogar', 0.0)

        filas_html += f"""
        <tr>
            <td>{agente.get('nombre', '')}</td>
            <td style="color: #2e7d32;">${agente.get('local', 0.0):,.2f}</td>
            <td style="color: #2e7d32;">${agente.get('internacional', 0.0):,.2f}</td>
            <td>${agente.get('vida', 0.0):,.2f}</td>
            <td>${agente.get('auto_hogar', 0.0):,.2f}</td>
        </tr>
        """

    # 2. Agregar explícitamente la fila de TOTALES al final para que nunca falte
    fila_totales_html = f"""
        <tr style="background-color: #111827; color: #ffffff; font-weight: bold;">
            <td>TOTAL GENERAL</td>
            <td>${total_local:,.2f}</td>
            <td>${total_internacional:,.2f}</td>
            <td>${total_vida:,.2f}</td>
            <td>${total_auto_hogar:,.2f}</td>
        </tr>
    """

    # 3. Estructura HTML completa con estilos limpios y profesionales
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #0f172a;
                color: #333333;
                margin: 0;
                padding: 20px;
                width: 800px; /* Ancho fijo para mantener la estructura limpia */
            }}
            .header-banner {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header-banner img {{
                width: 100%;
                border-radius: 8px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            th {{
                background-color: #1e293b;
                color: #ffffff;
                padding: 12px 10px;
                text-align: left;
                font-size: 14px;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 13px;
            }}
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <!-- Banner visual -->
        <div class="header-banner">
            <img src="{ruta_banner}" alt="Banner Ranking de Producción">
        </div>

        <!-- Tablero de Datos -->
        <table>
            <thead>
                <tr>
                    <th>Intermediario</th>
                    <th>Local</th>
                    <th>Internacional</th>
                    <th>Vida</th>
                    <th>Auto, Hogar y Empresa</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
                {fila_totales_html}
            </tbody>
        </table>
    </body>
    </html>
    """

    # Guardar temporalmente el archivo HTML para renderizarlo
    archivo_html_temp = "temp_ranking.html"
    with open(archivo_html_temp, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 4. Renderizado con Html2Image calculando la altura automática en base al tamaño
    hti = Html2Image(output_path=os.getcwd())
    
    # Estimamos una altura dinámica segura (Header + tabla con N filas + padding extra para asegurar el total)
    altura_estimada = 350 + (len(datos_tabla) * 45)
    
    hti.screenshot(
        html_file=archivo_html_temp,
        save_as=archivo_salida,
        size=(840, altura_estimada)
    )

    # Limpiar archivo temporal
    if os.path.exists(archivo_html_temp):
        os.remove(archivo_html_temp)

    print(f"Imagen generada correctamente: {archivo_salida} (Altura aplicada: {altura_estimada}px)")

# --- EJEMPLO DE USO ---
if __name__ == "__main__":
    # Simulación de los datos de tu equipo MEGAPODEROSOS
    ejemplo_datos = [
        {"nombre": "Dioselina Ramos", "local": 46850.00, "internacional": 0.0, "vida": 130.00, "auto_hogar": 0.0},
        {"nombre": "Luisa Gonzalez", "local": 34441.00, "internacional": 211.73, "vida": 1300.00, "auto_hogar": 0.0},
        {"nombre": "Marcos Adames", "local": 14175.00, "internacional": 0.0, "vida": 520.00, "auto_hogar": 200608.68},
        {"nombre": "Angela Vidal", "local": 9755.25, "internacional": 0.0, "vida": 260.00, "auto_hogar": 42531.44},
    ]
    
    # Reemplaza 'ruta_al_banner.png' por la ruta real de tu banner o su URL
    # generar_imagen_ranking_completa(ejemplo_datos, ruta_banner="ruta_al_banner.png")
