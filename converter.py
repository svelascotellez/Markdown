"""
Conversor robusto de documentos PDF y Word (.docx, .doc) a Markdown (.md)
Soporta archivos locales, streams en memoria y procesamiento por lotes.
"""

import io
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

import pymupdf4llm
import pymupdf
import mammoth
from markdownify import markdownify as html_to_md
from markitdown import MarkItDown


class DocumentConverter:
    """Clase principal para la conversión de documentos Word y PDF a Markdown."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".markdown"}

    def __init__(self):
        self.markitdown = MarkItDown()

    def clean_markdown(self, text: str) -> str:
        """Limpia y normaliza el texto Markdown resultante."""
        if not text:
            return ""

        # Normalizar saltos de línea de Windows a formato estándar
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Eliminar más de dos saltos de línea consecutivos
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Eliminar espacios innecesarios al final de las líneas
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip() + "\n"

    def convert_pdf_to_markdown(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        page_chunks: bool = False,
        extract_images: bool = False,
        image_dir: Optional[Union[str, Path]] = None,
    ) -> str:
        """
        Convierte un archivo PDF a Markdown utilizando PyMuPDF4LLM
        (reconocimiento avanzado de tablas, encabezados y formato de lectura).
        Permite la extracción opcional de imágenes embebidas.
        """
        doc = None
        temp_path = None
        try:
            if isinstance(source, (str, Path)):
                doc = pymupdf.open(str(source))
            elif isinstance(source, bytes):
                doc = pymupdf.open(stream=source, filetype="pdf")
            elif hasattr(source, "read"):
                content = source.read()
                doc = pymupdf.open(stream=content, filetype="pdf")
            else:
                raise ValueError("Tipo de fuente no compatible para PDF.")

            img_path_str = ""
            write_imgs = False
            if extract_images:
                write_imgs = True
                if image_dir:
                    img_path_str = str(image_dir)
                    os.makedirs(img_path_str, exist_ok=True)
                else:
                    img_path_str = "media"
                    os.makedirs(img_path_str, exist_ok=True)

            md_text = pymupdf4llm.to_markdown(
                doc,
                page_chunks=page_chunks,
                show_progress=False,
                write_images=write_imgs,
                image_path=img_path_str if write_imgs else "",
            )

            if isinstance(md_text, list):
                # Si page_chunks es True devuelve una lista de diccionarios por página
                md_text = "\n\n---\n\n".join(chunk.get("text", "") for chunk in md_text)

            return self.clean_markdown(md_text)

        except Exception as e:
            # Fallback a MarkItDown en caso de algún error particular
            try:
                if isinstance(source, (str, Path)):
                    result = self.markitdown.convert(str(source))
                    return self.clean_markdown(result.text_content)
                elif isinstance(source, bytes) or hasattr(source, "read"):
                    data = source if isinstance(source, bytes) else source.read()
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                        tf.write(data)
                        temp_path = tf.name
                    result = self.markitdown.convert(temp_path)
                    return self.clean_markdown(result.text_content)
            except Exception:
                pass
            raise RuntimeError(f"Error al convertir PDF a Markdown: {str(e)}") from e
        finally:
            if doc is not None:
                doc.close()
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def convert_docx_to_markdown(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        use_mammoth: bool = True,
        extract_images: bool = False,
        image_dir: Optional[Union[str, Path]] = None,
    ) -> str:
        """
        Convierte un archivo Word (.docx) a Markdown.
        Utiliza Mammoth (HTML limpio y semántico) + Markdownify por defecto,
        con fallback a MarkItDown. Soporta extracción y guardado de imágenes embebidas.
        """
        temp_path = None
        try:
            if use_mammoth:
                bio = None
                img_converter = None
                if extract_images:
                    target_img_dir = Path(image_dir) if image_dir else Path("media")
                    target_img_dir.mkdir(parents=True, exist_ok=True)
                    counter = 0

                    def _save_image(image):
                        nonlocal counter
                        counter += 1
                        ext = mammoth.images.image_filename_extension(image) or "png"
                        img_filename = f"image_{counter}.{ext}"
                        img_filepath = target_img_dir / img_filename
                        with image.open() as img_stream:
                            img_filepath.write_bytes(img_stream.read())
                        # Usar ruta relativa estándar para el enlace en Markdown
                        rel_path = f"{target_img_dir.as_posix()}/{img_filename}"
                        return {"src": rel_path}

                    img_converter = mammoth.images.img_element(_save_image)

                convert_kwargs = {}
                if img_converter is not None:
                    convert_kwargs["convert_image"] = img_converter

                if isinstance(source, (str, Path)):
                    with open(source, "rb") as docx_file:
                        result = mammoth.convert_to_html(docx_file, **convert_kwargs)
                elif isinstance(source, bytes):
                    bio = io.BytesIO(source)
                    result = mammoth.convert_to_html(bio, **convert_kwargs)
                elif hasattr(source, "read"):
                    bio = io.BytesIO(source.read())
                    result = mammoth.convert_to_html(bio, **convert_kwargs)
                else:
                    raise ValueError("Tipo de fuente no compatible para DOCX.")

                html = result.value
                # Opciones de conversión a Markdown optimizadas para legibilidad
                md_text = html_to_md(
                    html,
                    heading_style="ATX",  # # Encabezado en lugar de subrayado
                    bullets="-",
                    strip=["script", "style"],
                )
                return self.clean_markdown(md_text)

            else:
                # Usar MarkItDown
                if isinstance(source, (str, Path)):
                    res = self.markitdown.convert(str(source))
                    return self.clean_markdown(res.text_content)
                else:
                    data = source if isinstance(source, bytes) else source.read()
                    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
                        tf.write(data)
                        temp_path = tf.name
                    res = self.markitdown.convert(temp_path)
                    return self.clean_markdown(res.text_content)

        except Exception as e:
            # Si mammoth falló, intentamos fallback con MarkItDown
            try:
                if isinstance(source, (str, Path)):
                    res = self.markitdown.convert(str(source))
                    return self.clean_markdown(res.text_content)
                elif isinstance(source, bytes) or hasattr(source, "read"):
                    data = source if isinstance(source, bytes) else source.read()
                    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
                        tf.write(data)
                        temp_path = tf.name
                    res = self.markitdown.convert(temp_path)
                    return self.clean_markdown(res.text_content)
            except Exception:
                pass
            raise RuntimeError(f"Error al convertir DOCX a Markdown: {str(e)}") from e
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def convert_doc_to_markdown(
        self,
        source: Union[str, Path, bytes, BinaryIO],
    ) -> str:
        """
        Convierte archivos Word de formato binario antiguo (.doc).
        """
        temp_path = None
        try:
            if isinstance(source, (str, Path)):
                file_path = str(source)
            else:
                data = source if isinstance(source, bytes) else source.read()
                with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tf:
                    tf.write(data)
                    temp_path = tf.name
                file_path = temp_path

            result = self.markitdown.convert(file_path)
            return self.clean_markdown(result.text_content)
        except Exception as e:
            raise RuntimeError(
                f"Error al procesar archivo .doc antiguo: {str(e)}. "
                f"Sugerencia: Guarda el documento como formato moderno .docx para mejores resultados."
            ) from e
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def convert_file(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        extract_images: bool = False,
        image_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[str, Path]:
        """
        Convierte un archivo dado por su ruta en disco y guarda el archivo .md si se especifica salida.
        Retorna (texto_markdown, ruta_destino).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"El archivo '{file_path}' no existe.")

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Formato no compatible '{suffix}'. Formatos soportados: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        if output_path is None:
            out_p = path.with_suffix(".md")
        else:
            out_p = Path(output_path)
            if out_p.is_dir():
                out_p = out_p / f"{path.stem}.md"

        img_target_dir = image_dir
        if extract_images and not img_target_dir:
            img_target_dir = out_p.parent / f"{path.stem}_images"

        if suffix == ".pdf":
            md_content = self.convert_pdf_to_markdown(
                path,
                extract_images=extract_images,
                image_dir=img_target_dir,
            )
        elif suffix == ".docx":
            md_content = self.convert_docx_to_markdown(
                path,
                extract_images=extract_images,
                image_dir=img_target_dir,
            )
        elif suffix == ".doc":
            md_content = self.convert_doc_to_markdown(path)
        elif suffix in {".md", ".markdown"}:
            md_content = self.clean_markdown(path.read_text(encoding="utf-8", errors="replace"))
        else:
            raise ValueError(f"Extensión no soportada: {suffix}")

        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md_content, encoding="utf-8")

        return md_content, out_p

    def convert_stream(
        self,
        stream_or_bytes: Union[bytes, BinaryIO],
        filename: str,
        extract_images: bool = False,
        image_dir: Optional[Union[str, Path]] = None,
    ) -> str:
        """
        Convierte un archivo recibido como stream o bytes (ideal para APIs y Web).
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"El archivo '{filename}' tiene una extensión no soportada ({ext}). "
                f"Formatos aceptados: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        if ext == ".pdf":
            return self.convert_pdf_to_markdown(
                stream_or_bytes,
                extract_images=extract_images,
                image_dir=image_dir,
            )
        elif ext == ".docx":
            return self.convert_docx_to_markdown(
                stream_or_bytes,
                extract_images=extract_images,
                image_dir=image_dir,
            )
        elif ext == ".doc":
            return self.convert_doc_to_markdown(stream_or_bytes)
        elif ext in {".md", ".markdown"}:
            data = stream_or_bytes if isinstance(stream_or_bytes, bytes) else stream_or_bytes.read()
            return self.clean_markdown(data.decode("utf-8", errors="replace"))
        else:
            raise ValueError(f"Extensión no soportada: {ext}")

    def convert_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        recursive: bool = False,
        extract_images: bool = False,
    ) -> List[Tuple[Path, Path, bool, str]]:
        """
        Convierte todos los archivos soportados en una carpeta.
        Retorna lista de tuplas: (archivo_origen, archivo_destino, exito, mensaje)
        """
        in_p = Path(input_dir)
        if not in_p.is_dir():
            raise NotADirectoryError(f"'{input_dir}' no es un directorio válido.")

        out_dir = Path(output_dir) if output_dir else in_p

        pattern = "**/*" if recursive else "*"
        results = []

        for item in in_p.glob(pattern):
            if item.is_file() and item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                # Calcular ruta relativa para preservar subcarpetas si es recursivo
                if recursive and output_dir:
                    rel_parent = item.parent.relative_to(in_p)
                    target_dir = out_dir / rel_parent
                else:
                    target_dir = out_dir

                target_file = target_dir / f"{item.stem}.md"

                try:
                    self.convert_file(
                        item,
                        target_file,
                        extract_images=extract_images,
                    )
                    results.append((item, target_file, True, "Convertido exitosamente"))
                except Exception as e:
                    results.append((item, target_file, False, str(e)))

        return results

