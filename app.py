"""
Servidor Web FastAPI para el Convertidor de Documentos Word y PDF a Markdown.
Incluye endpoints de conversión individual, por lotes, descarga en ZIP y visualización interactiva.
"""

import asyncio
import io
import os
import sys
import webbrowser
import zipfile
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from converter import DocumentConverter

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Word & PDF to Markdown Converter",
    description="Aplicación web interactiva para convertir archivos de Word y PDF a formato Markdown (.md)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = DocumentConverter()


class ConversionResult(BaseModel):
    filename: str
    markdown_filename: str
    markdown: str
    stats: dict
    success: bool
    error: Optional[str] = None


@app.post("/api/convert", response_model=List[ConversionResult])
async def convert_files_endpoint(files: List[UploadFile] = File(...)):
    """Convierte uno o más archivos de Word (.docx/.doc) o PDF a Markdown."""
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos para convertir.")

    results: List[ConversionResult] = []

    for uploaded_file in files:
        orig_name = uploaded_file.filename or "documento"
        stem = Path(orig_name).stem
        md_name = f"{stem}.md"

        try:
            content_bytes = await uploaded_file.read()
            if not content_bytes:
                results.append(
                    ConversionResult(
                        filename=orig_name,
                        markdown_filename=md_name,
                        markdown="",
                        stats={"lines": 0, "words": 0, "chars": 0, "size_bytes": 0},
                        success=False,
                        error="El archivo está vacío.",
                    )
                )
                continue

            # Ejecución en threadpool para evitar bloquear el event loop con documentos pesados
            md_text = await asyncio.to_thread(converter.convert_stream, content_bytes, orig_name)

            lines = len(md_text.splitlines())
            words = len(md_text.split())
            chars = len(md_text)

            results.append(
                ConversionResult(
                    filename=orig_name,
                    markdown_filename=md_name,
                    markdown=md_text,
                    stats={
                        "lines": lines,
                        "words": words,
                        "chars": chars,
                        "size_bytes": len(content_bytes),
                    },
                    success=True,
                    error=None,
                )
            )

        except Exception as e:
            results.append(
                ConversionResult(
                    filename=orig_name,
                    markdown_filename=md_name,
                    markdown="",
                    stats={"lines": 0, "words": 0, "chars": 0, "size_bytes": 0},
                    success=False,
                    error=str(e),
                )
            )

    return results


class BatchDownloadRequest(BaseModel):
    files: List[dict]  # [{'filename': 'doc.md', 'content': '# Markdown...'}]


@app.post("/api/download-zip")
async def download_zip_endpoint(payload: BatchDownloadRequest):
    """Genera y descarga un archivo .ZIP con todos los archivos Markdown convertidos."""
    if not payload.files:
        raise HTTPException(status_code=400, detail="No hay archivos para comprimir.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in payload.files:
            fname = item.get("filename", "documento.md")
            if not fname.endswith(".md"):
                fname += ".md"
            content = item.get("content", "")
            zip_file.writestr(fname, content.encode("utf-8"))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="documentos_markdown.zip"'},
    )


# Servir frontend estático
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def start_server(port: int = 8011, open_browser: bool = True):
    """Inicia el servidor web FastAPI y opcionalmente abre el navegador."""
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f" Servidor iniciado exitosamente en: {url}")
    print(f" Presiona Ctrl + C en esta consola para detener.")
    print(f"=======================================================\n")

    if open_browser:
        import threading
        import time

        def _open():
            time.sleep(1.0)
            try:
                webbrowser.open(url)
            except Exception:
                pass

        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lanza la interfaz web de conversión de Word/PDF a Markdown.")
    parser.add_argument("--port", type=int, default=8011, help="Puerto del servidor (por defecto: 8011)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")

    args = parser.parse_args()
    start_server(port=args.port, open_browser=not args.no_browser)
