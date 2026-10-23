from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "Descargador de YouTube"


class DownloadCancelled(Exception):
    """Raised from the progress hook when the user cancels the download."""


class YouTubeDownloaderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("900x650")
        self.minsize(760, 560)

        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None

        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.mode_var = tk.StringVar(value="video")
        self.quality_var = tk.StringVar(value="best")
        self.collection_var = tk.BooleanVar(value=True)
        self.archive_var = tk.BooleanVar(value=True)
        self.browser_cookies_var = tk.StringVar(value="none")
        self.status_var = tk.StringVar(value="Listo")
        self.current_item_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)

        self._configure_theme()
        self._build_layout()
        self.after(100, self._drain_events)

    def _configure_theme(self) -> None:
        self.configure(bg="#f4f6f8")
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background="#f4f6f8")
        style.configure("Hint.TLabel", foreground="#5f6b7a", background="#f4f6f8")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Root.TFrame", background="#f4f6f8")
        style.configure("TCheckbutton", background="#ffffff")
        style.configure("TRadiobutton", background="#ffffff")

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=24, style="Root.TFrame")
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            root,
            text="Introduce un enlace de video, lista o canal. Descarga solo contenido propio o con permiso.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        panel = ttk.Frame(root, padding=18, style="Panel.TFrame")
        panel.grid(row=2, column=0, sticky="nsew")
        panel.columnconfigure(1, weight=1)
        panel.rowconfigure(9, weight=1)

        ttk.Label(panel, text="URL de YouTube").grid(row=0, column=0, columnspan=3, sticky="w")
        url_entry = ttk.Entry(panel, textvariable=self.url_var, font=("Segoe UI", 11))
        url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 16))
        url_entry.focus()

        ttk.Label(panel, text="Carpeta destino").grid(row=2, column=0, columnspan=3, sticky="w")
        folder_entry = ttk.Entry(panel, textvariable=self.folder_var)
        folder_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 16), padx=(0, 8))
        ttk.Button(panel, text="Elegir...", command=self._choose_folder).grid(row=3, column=2, sticky="ew", pady=(6, 16))

        options = ttk.Frame(panel, style="Panel.TFrame")
        options.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 14))
        options.columnconfigure((0, 1, 2), weight=1)

        mode_box = ttk.LabelFrame(options, text="Formato", padding=12)
        mode_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Radiobutton(mode_box, text="Video MP4", value="video", variable=self.mode_var).pack(anchor="w")
        ttk.Radiobutton(mode_box, text="Audio MP3", value="audio", variable=self.mode_var).pack(anchor="w", pady=(6, 0))

        quality_box = ttk.LabelFrame(options, text="Calidad", padding=12)
        quality_box.grid(row=0, column=1, sticky="nsew", padx=8)
        ttk.Combobox(
            quality_box,
            state="readonly",
            textvariable=self.quality_var,
            values=("best", "1080p", "720p", "480p", "360p"),
        ).pack(fill=tk.X)

        cookies_box = ttk.LabelFrame(options, text="Cookies", padding=12)
        cookies_box.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        ttk.Combobox(
            cookies_box,
            state="readonly",
            textvariable=self.browser_cookies_var,
            values=("none", "chrome", "edge", "firefox", "brave", "opera"),
        ).pack(fill=tk.X)

        ttk.Checkbutton(
            panel,
            text="Descargar coleccion completa si la URL es lista, canal o pestana de videos",
            variable=self.collection_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Checkbutton(
            panel,
            text="Recordar descargas completadas para evitar duplicados en futuras ejecuciones",
            variable=self.archive_var,
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 16))

        controls = ttk.Frame(panel, style="Panel.TFrame")
        controls.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        controls.columnconfigure(0, weight=1)
        self.download_button = ttk.Button(controls, text="Iniciar descarga", command=self._start_download)
        self.download_button.grid(row=0, column=1, padx=(0, 8))
        self.cancel_button = ttk.Button(controls, text="Cancelar", command=self._cancel_download, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=2)

        ttk.Label(panel, textvariable=self.status_var).grid(row=8, column=0, columnspan=3, sticky="w")
        ttk.Progressbar(panel, variable=self.progress_var, maximum=100).grid(
            row=9, column=0, columnspan=3, sticky="ew", pady=(8, 4)
        )
        ttk.Label(panel, textvariable=self.current_item_var, style="Hint.TLabel").grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        log_frame = ttk.LabelFrame(panel, text="Actividad", padding=8)
        log_frame.grid(row=11, column=0, columnspan=3, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED, bg="#fbfcfd", relief=tk.FLAT)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.folder_var.get() or str(Path.home()))
        if selected:
            self.folder_var.set(selected)

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        output_dir = Path(self.folder_var.get()).expanduser()

        if not url:
            messagebox.showwarning(APP_TITLE, "Introduce una URL de YouTube.")
            return

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"No se pudo crear la carpeta destino:\n{exc}")
            return

        self.cancel_event.clear()
        self.progress_var.set(0)
        self.current_item_var.set("")
        self._set_running(True)
        self._log(f"Iniciando descarga: {url}")

        settings = {
            "url": url,
            "output_dir": output_dir,
            "mode": self.mode_var.get(),
            "quality": self.quality_var.get(),
            "download_collection": self.collection_var.get(),
            "use_archive": self.archive_var.get(),
            "cookies_browser": self.browser_cookies_var.get(),
        }

        self.worker = threading.Thread(target=self._download_worker, args=(settings,), daemon=True)
        self.worker.start()

    def _cancel_download(self) -> None:
        self.cancel_event.set()
        self.status_var.set("Cancelando...")
        self._log("Cancelacion solicitada. Se detendra al cerrar el archivo actual.")

    def _set_running(self, running: bool) -> None:
        self.download_button.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.cancel_button.configure(state=tk.NORMAL if running else tk.DISABLED)

    def _download_worker(self, settings: dict[str, Any]) -> None:
        try:
            import yt_dlp
        except ImportError:
            self.events.put(
                (
                    "error",
                    "Falta la dependencia yt-dlp. Instala dependencias con: pip install -r requirements.txt",
                )
            )
            return

        try:
            ydl_opts = self._build_ydl_options(settings)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([settings["url"]])
        except DownloadCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:  # yt-dlp raises several extractor/network exceptions.
            self.events.put(("error", str(exc)))
        else:
            self.events.put(("finished", None))

    def _build_ydl_options(self, settings: dict[str, Any]) -> dict[str, Any]:
        output_dir: Path = settings["output_dir"]
        mode = settings["mode"]
        quality = settings["quality"]

        options: dict[str, Any] = {
            "outtmpl": str(output_dir / "%(uploader)s" / "%(playlist_title|Videos)s" / "%(title)s [%(id)s].%(ext)s"),
            "ignoreerrors": True,
            "noplaylist": not settings["download_collection"],
            "progress_hooks": [self._progress_hook],
            "logger": QueueLogger(self.events),
            "windowsfilenames": True,
            "restrictfilenames": False,
        }

        if settings["use_archive"]:
            options["download_archive"] = str(output_dir / ".yt-dlp-archive.txt")

        cookies_browser = settings["cookies_browser"]
        if cookies_browser != "none":
            options["cookiesfrombrowser"] = (cookies_browser,)

        if mode == "audio":
            options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
            return options

        if quality == "best":
            format_selector = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/best"
        else:
            max_height = quality.removesuffix("p")
            format_selector = (
                f"bv*[ext=mp4][height<={max_height}]+ba[ext=m4a]/"
                f"b[ext=mp4][height<={max_height}]/"
                f"bv*[height<={max_height}]+ba/best[height<={max_height}]"
            )

        options.update(
            {
                "format": format_selector,
                "merge_output_format": "mp4",
            }
        )
        return options

    def _progress_hook(self, info: dict[str, Any]) -> None:
        if self.cancel_event.is_set():
            raise DownloadCancelled()

        status = info.get("status")
        filename = Path(info.get("filename") or "").name

        if status == "downloading":
            total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
            downloaded = info.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total else 0
            speed = self._format_bytes(info.get("speed")) + "/s" if info.get("speed") else ""
            eta = f"ETA {info.get('eta')}s" if info.get("eta") is not None else ""
            self.events.put(("progress", {"percent": percent, "filename": filename, "speed": speed, "eta": eta}))
        elif status == "finished":
            self.events.put(("item_finished", filename))

    def _drain_events(self) -> None:
        while True:
            try:
                event, payload = self.events.get_nowait()
            except queue.Empty:
                break

            if event == "progress":
                self.progress_var.set(payload["percent"])
                details = " ".join(part for part in (payload["speed"], payload["eta"]) if part)
                self.status_var.set(f"Descargando... {payload['percent']:.1f}% {details}".strip())
                self.current_item_var.set(payload["filename"])
            elif event == "item_finished":
                self.progress_var.set(100)
                self.status_var.set("Procesando archivo...")
                self.current_item_var.set(payload)
                self._log(f"Archivo descargado: {payload}")
            elif event == "log":
                self._log(payload)
            elif event == "warning":
                self._log(f"Advertencia: {payload}")
            elif event == "error":
                self._set_running(False)
                self.status_var.set("Error")
                self._log(f"Error: {payload}")
                messagebox.showerror(APP_TITLE, payload)
            elif event == "cancelled":
                self._set_running(False)
                self.status_var.set("Cancelado")
                self._log("Descarga cancelada.")
            elif event == "finished":
                self._set_running(False)
                self.progress_var.set(100)
                self.status_var.set("Descarga completada")
                self._log("Descarga completada.")

        self.after(100, self._drain_events)

    def _log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    @staticmethod
    def _format_bytes(value: float | int | None) -> str:
        if not value:
            return ""
        units = ("B", "KB", "MB", "GB")
        size = float(value)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"


class QueueLogger:
    def __init__(self, events: queue.Queue[tuple[str, Any]]) -> None:
        self.events = events

    def debug(self, message: str) -> None:
        if message.startswith("[debug]"):
            return
        self.events.put(("log", message))

    def warning(self, message: str) -> None:
        self.events.put(("warning", message))

    def error(self, message: str) -> None:
        self.events.put(("log", message))


def main() -> None:
    app = YouTubeDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
