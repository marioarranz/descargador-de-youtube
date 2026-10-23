$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name "DescargadorDeYoutube" "src\youtube_downloader_app.py"

Write-Host ""
Write-Host "EXE generado en: dist\DescargadorDeYoutube.exe"
