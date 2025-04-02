import os
import subprocess
import re
import qrcode
import barcode
from barcode.writer import ImageWriter


def escape_latex(text):
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '\\': r'\textbackslash',
        '^': r'\^{}', '~': r'\~{}', '<': r'\textless', '>': r'\textgreater'
    }
    return "".join(replacements.get(c, c) for c in str(text))


def generar_codigo_barras(id_movimiento, output_dir):
    try:
        # Nombre del archivo SIN extensión
        filename = f"barcode_{id_movimiento}"
        # Ruta completa (la librería añade .png automáticamente)
        full_path = os.path.join(output_dir, filename)

        code = barcode.get('code128', id_movimiento, writer=ImageWriter())
        code.save(full_path, options={"write_text": False})  # Guarda como .png

        return f"{full_path}.png"  # ← Retorna la ruta correcta
    except Exception as e:
        raise RuntimeError(f"Error generando código de barras: {str(e)}")


def generar_qr(id_movimiento, output_path):
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(id_movimiento)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return output_path
    except Exception as e:
        raise RuntimeError(f"Error generando QR: {str(e)}")


def generar_reporte_latex(
    data,
    template_path=os.path.join(
        'Documents', 'documentación', 'RMovimiento de material.tex'),
    output_dir='reports'
):
    try:
        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

        # 1. Cargar plantilla LaTeX
        if not os.path.exists(template_path):
            return False, f"Plantilla no encontrada en: {template_path}"

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 2. Generar códigos gráficos
        barcode_path = generar_codigo_barras(data['id_movimiento'], output_dir)
        qrcode_path = os.path.join(
            output_dir, f"qrcode_{data['id_movimiento']}.png")
        generar_qr(data['id_movimiento'], qrcode_path)

        # 3. Preparar rutas para LaTeX (compatibilidad multiplataforma)
        barcode_path_tex = barcode_path.replace("\\", "/")
        qrcode_path_tex = qrcode_path.replace("\\", "/")

        replacements = {
            r'@@ID_MOVIMIENTO@@': escape_latex(data['id_movimiento']),
            r'@@ORIGEN@@': escape_latex(data['origen']),
            r'@@DESTINO@@': escape_latex(data['destino']),
            r'@@FECHA@@': escape_latex(data['fecha']),
            r'@@TABLA_DATOS@@': data['tabla_datos'],
            r'@@BARCODE_PATH@@': escape_latex(barcode_path_tex),
            r'@@QRCODE_PATH@@': escape_latex(qrcode_path_tex),
            r'@@NOMBRE_USUARIO@@': escape_latex(data['nombre_usuario']),
        }

        for pattern, replacement in replacements.items():
            template = re.sub(pattern, replacement, template)

        # 3. Guardar archivo .tex
        tex_output = os.path.join(
            output_dir, f'reporte_{data["id_movimiento"]}.tex')
        with open(tex_output, 'w', encoding='utf-8') as f:
            f.write(template)

        # 4. Compilar con pdflatex (capturar salida completa)

        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode',
                '-output-directory', output_dir, tex_output],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = f"Error LaTeX:\n{result.stderr}"
            return False, error_msg

        return True, ""

    except subprocess.TimeoutExpired:
        return False, "Tiempo de compilación excedido"
    except FileNotFoundError:
        return False, "pdflatex no está instalado o no está en el PATH"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


def generar_reporte_entrega_latex(
    data,
    template_path=os.path.join(
        'Documents', 'documentación', 'REntregaMateriales.tex'),
    output_dir='Entregas'
):
    try:
        os.makedirs(output_dir, exist_ok=True)

        # 1. Cargar plantilla ENTREGA
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 2. Generar QR
        qrcode_path = os.path.join(
            output_dir, f"qrcode_{data['id_entrega']}.png")
        generar_qr(data['id_entrega'], qrcode_path)

        # 3. Activar condicionales
        toggle_commands = []
        if data.get("miscelaneos") and len(data["miscelaneos"]) > 0:
            toggle_commands.append(r"\toggletrue{miscelaneos}")
        else:
            # Desactivar si no hay datos
            toggle_commands.append(r"\togglefalse{miscelaneos}")

        if data.get("ont") and len(data["ont"]) > 0:
            toggle_commands.append(r"\toggletrue{ont}")
        else:
            toggle_commands.append(r"\togglefalse{ont}")

        if data.get("modem") and len(data["modem"]) > 0:
            toggle_commands.append(r"\toggletrue{modem}")
        else:
            toggle_commands.append(r"\togglefalse{modem}")

        # Insertar comandos después de \begin{document}
        template = template.replace(
            r"\begin{document}",
            r"\begin{document}" + "\n" + "\n".join(toggle_commands)
        )

        # 4. Preparar reemplazos
        replacements = {
            r'@@area@@': escape_latex(data['area']),
            r'@@Cope@@': escape_latex(data['cope']),
            r'@@FECHA@@': escape_latex(data['fecha']),
            r'@@ExpTec@@': escape_latex(data['exptec']),
            r'@@Usuario@@': escape_latex(data['usuario']),
            r'@@ID_ENTREGA@@': escape_latex(data['id_entrega']),
            r'@@QRCODE_PATH@@': escape_latex(qrcode_path.replace("\\", "/")),
            r'@@TECNICO@@': escape_latex(data['tecnico']),
            r'@@ADMINISTRADOR@@': escape_latex(data['administrador']),
            # Filas de tablas (sin escapar las barras)
            r"@@MISCELANEOS@@": " \\\\\n".join(data.get("miscelaneos", [])),
            r"@@ONT@@": " \\\\\n".join(data.get("ont", [])),
            r"@@MODEM@@": " \\\\\n".join(data.get("modem", []))
        }

        # 5. Aplicar reemplazos
        for pattern, replacement in replacements.items():
            template = template.replace(pattern, replacement)

        # 6. Guardar y compilar
        tex_output = os.path.join(
            output_dir, f'reporte_{data["id_entrega"]}.tex')
        with open(tex_output, 'w', encoding='utf-8') as f:
            f.write(template)

        # Compilar con pdflatex
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode',
                '-output-directory', output_dir, tex_output],
            capture_output=True,
            text=True,
            timeout=30
        )

        return (True, "") if result.returncode == 0 else (False, result.stderr)

    except Exception as e:
        return False, f"Error generando reporte de entrega: {str(e)}"


def limpiar_archivos_temporales(output_dir):
    # Eliminar archivos temporales de LaTeX (.log, .aux, .tex, etc.)
    extensiones = ['.log', '.aux', '.out', '.tex']
    for archivo in os.listdir(output_dir):
        if any(archivo.endswith(ext) for ext in extensiones):
            ruta_archivo = os.path.join(output_dir, archivo)
            try:
                os.remove(ruta_archivo)
            except Exception as e:
                print(f"No se pudo eliminar {ruta_archivo}: {str(e)}")
