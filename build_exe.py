"""
EXE Builder Script
PyInstaller ile EXE oluşturur
"""
import PyInstaller.__main__
import os

# Proje dizini
base_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'run_app.py',
    '--name=AracimSaglam',
    '--onefile',
    '--windowed',
    '--icon=NONE',
    f'--add-data={os.path.join(base_dir, "website", "templates")};website/templates',
    f'--add-data={os.path.join(base_dir, "website", "static")};website/static',
    f'--add-data={os.path.join(base_dir, "data")};data',
    f'--add-data={os.path.join(base_dir, "agent")};agent',
    '--hidden-import=flask',
    '--hidden-import=jinja2',
    '--hidden-import=werkzeug',
    '--collect-all=flask',
    '--collect-all=jinja2',
    '--noconfirm',
])

print("\n" + "="*50)
print("✅ EXE oluşturuldu!")
print("📁 Konum: dist/AracimSaglam.exe")
print("="*50)
