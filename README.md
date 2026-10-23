# Descargador de YouTube

Aplicacion de escritorio para Windows que permite introducir una URL de YouTube y descargar un video, una lista de reproduccion o los videos de un canal usando `yt-dlp`.

Usa esta herramienta solo para contenido propio, con permiso, o contenido cuya descarga este permitida.

## Requisitos

- Python 3.11 o superior.
- FFmpeg instalado y disponible en el `PATH` para convertir audio a MP3 y fusionar video/audio cuando YouTube los entrega por separado.

## Ejecutar en desarrollo

```powershell
python -m pip install -r requirements.txt
python src\youtube_downloader_app.py
```

## Crear el .exe

```powershell
.\build_exe.ps1
```

El ejecutable quedara en:

```text
dist\DescargadorDeYoutube.exe
```

## Uso

1. Pega una URL de YouTube.
2. Elige la carpeta destino.
3. Selecciona Video MP4 o Audio MP3.
4. Activa o desactiva la descarga de coleccion completa segun quieras tratar listas/canales como una coleccion o solo descargar el video principal.
5. Pulsa **Iniciar descarga**.

La opcion de cookies permite usar cookies de Chrome, Edge, Firefox, Brave u Opera si YouTube solicita autenticacion o confirmaciones de edad.
