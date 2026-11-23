# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

block_cipher = None

# ========== CONFIGURACIÓN PRINCIPAL ========== #
app_name = "LECECOM"
app_icon = os.path.join("assets", "icons", "icono_app.ico")
project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
postgres_bin = r"C:\Program Files\PostgreSQL\17\bin"

# ========== CONFIGURACIÓN DE ENTRADA ========== #
entry_point = 'index.py'  # Cambiado a tu archivo principal

# ========== ANÁLISIS DE DEPENDENCIAS ========== #
a = Analysis(
    [entry_point],  # Usamos la variable de entrada
    pathex=[project_path],
    binaries=[
        # OpenCV (si se usa)
        (os.path.join("venv", "Lib", "site-packages", "cv2", "*.dll"), "cv2"),
        (r'venv\Lib\site-packages\pyzbar\libiconv.dll', 'pyzbar'),
        (r'venv\Lib\site-packages\pyzbar\libzbar-64.dll', 'pyzbar'),
    ],
    datas=[
        # Recursos de la app
        (os.path.join("modules/updater.py"), "modules"),
        (os.path.join("assets", "*"), "assets"),
        (os.path.join("modules/actualizando.ui"), "modules"),
        (os.path.join("modules", "**", "*.ui"), "modules"),
        
        # PostgreSQL - TODOS los DLLs
        (os.path.join(postgres_bin, "*.dll"), "postgres_dlls"),
        
        # Otras dependencias
        (os.path.join('venv', 'Lib', 'site-packages', 'barcode', 'fonts', '*'), 'barcode/fonts'),
        *collect_data_files('PyQt6', subdir='Qt6'),
    ],
    hiddenimports=[
        'psycopg2',
        'psycopg2_binary',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtWebEngineWidgets',
        'sqlalchemy.dialects.postgresql',
        'qrcode',
        'pyzbar',
        'reportlab.lib',
        'jinja2.ext'
    ],
    hookspath=["hooks"],
    excludes=["tkinter", "test"],
    noarchive=False,
    cipher=block_cipher
)

# ========== CONSTRUCCIÓN ========== #
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=app_name,
          debug=False,
          icon=app_icon,
          upx=True,
          console=True)