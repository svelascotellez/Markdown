"""
Interfaz de línea de comandos (CLI) para convertir archivos Word y PDF a Markdown.
Soporta archivos individuales, carpetas completas y modo interactivo.
"""

import argparse
import sys
import time
from pathlib import Path

from converter import DocumentConverter


def print_banner():
    banner = r"""
╔═══════════════════════════════════════════════════════════════╗
║         CONVERTIDOR DE WORD Y PDF A MARKDOWN (.md)           ║
║       Formatos compatibles: .pdf, .docx, .doc (Word)          ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def convert_single_file(
    converter: DocumentConverter,
    file_path: Path,
    output_path: Path = None,
    extract_images: bool = False,
    image_dir: Path = None,
):
    print(f"\n[>] Procesando archivo: {file_path.name}")
    start_time = time.time()
    try:
        content, out_file = converter.convert_file(
            file_path,
            output_path,
            extract_images=extract_images,
            image_dir=image_dir,
        )
        elapsed = time.time() - start_time
        lines = len(content.splitlines())
        words = len(content.split())
        chars = len(content)

        print(f" [OK] Convertido con éxito en {elapsed:.2f} s")
        print(f"      Destino:     {out_file.resolve()}")
        if extract_images:
            actual_img_dir = image_dir if image_dir else out_file.parent / f"{file_path.stem}_images"
            print(f"      Imágenes:    {actual_img_dir.resolve()}")
        print(f"      Estadísticas: {lines} líneas | {words} palabras | {chars} caracteres")
        return True
    except Exception as e:
        print(f" [ERROR] No se pudo convertir '{file_path.name}': {e}")
        return False


def convert_batch_directory(
    converter: DocumentConverter,
    directory: Path,
    output_dir: Path = None,
    recursive: bool = False,
    extract_images: bool = False,
):
    print(f"\n[>] Escaneando directorio: {directory.resolve()}")
    if recursive:
        print("    Modo recursivo: activado (incluyendo subcarpetas)")
    if extract_images:
        print("    Extracción de imágenes: activada")

    start_time = time.time()
    results = converter.convert_directory(
        directory,
        output_dir,
        recursive=recursive,
        extract_images=extract_images,
    )
    elapsed = time.time() - start_time

    if not results:
        print(" [!] No se encontraron archivos .pdf, .docx o .doc en la ubicación especificada.")
        return

    success_count = sum(1 for _, _, ok, _ in results if ok)
    fail_count = len(results) - success_count

    print(f"\n[=] Resumen de conversión ({elapsed:.2f} s):")
    print(f"    Total encontrados: {len(results)}")
    print(f"    Convertidos con éxito: {success_count}")
    if fail_count > 0:
        print(f"    Fallidos: {fail_count}")

    print("\nDetalle:")
    for src, dst, ok, msg in results:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {src.name} -> {dst.name}")
        if not ok:
            print(f"         Error: {msg}")


def interactive_mode(converter: DocumentConverter):
    print_banner()
    print("Modo interactivo activado.\n")
    try:
        path_input = input("Introduce la ruta del archivo (.pdf/.docx) o carpeta a convertir: ").strip().strip('"').strip("'")
        if not path_input:
            print("No se ingresó ninguna ruta. Operación cancelada.")
            return

        target_path = Path(path_input)
        if not target_path.exists():
            print(f"Error: La ruta '{path_input}' no existe.")
            return

        out_input = input("Carpeta o nombre de archivo de salida (opcional, presiona Enter para usar la misma): ").strip().strip('"').strip("'")
        output_path = Path(out_input) if out_input else None

        img_ans = input("¿Deseas extraer imágenes incrustadas? (s/N): ").strip().lower()
        extract_images = img_ans in ["s", "si", "y", "yes"]

        if target_path.is_file():
            convert_single_file(converter, target_path, output_path, extract_images=extract_images)
        elif target_path.is_dir():
            rec_ans = input("¿Deseas buscar archivos en subcarpetas recursivamente? (s/N): ").strip().lower()
            recursive = rec_ans in ["s", "si", "y", "yes"]
            convert_batch_directory(
                converter,
                target_path,
                output_path,
                recursive=recursive,
                extract_images=extract_images,
            )

        print("\n¡Proceso finalizado!")
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")


def main():
    parser = argparse.ArgumentParser(
        description="Convierte documentos Word (.docx, .doc) y PDF (.pdf) a formato Markdown (.md).",
        epilog="Ejemplos:\n"
               "  python cli.py documento.pdf\n"
               "  python cli.py documento.pdf --extract-images\n"
               "  python cli.py reporte.docx -o reporte_final.md --extract-images\n"
               "  python cli.py ./documentos/ -o ./markdowns/ --recursive --extract-images\n"
               "  python cli.py   (inicia en modo interactivo)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Ruta del archivo o carpeta a convertir.",
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Ruta del archivo de salida o carpeta de destino.",
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Si 'source' es una carpeta, procesa recursivamente todas las subcarpetas.",
    )

    parser.add_argument(
        "--extract-images",
        action="store_true",
        help="Extrae las imágenes incrustadas en el documento a una carpeta local y las referencia en el Markdown.",
    )

    parser.add_argument(
        "--image-dir",
        default=None,
        help="Directorio destino para guardar las imágenes extraídas (por defecto: '<nombre_archivo>_images').",
    )

    args = parser.parse_args()
    converter = DocumentConverter()

    if args.source is None:
        # Iniciar modo interactivo amigable
        interactive_mode(converter)
        return

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: El archivo o carpeta especificada no existe: {source_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None
    image_dir = Path(args.image_dir) if args.image_dir else None

    if source_path.is_file():
        success = convert_single_file(
            converter,
            source_path,
            output_path,
            extract_images=args.extract_images,
            image_dir=image_dir,
        )
        sys.exit(0 if success else 1)
    elif source_path.is_dir():
        convert_batch_directory(
            converter,
            source_path,
            output_path,
            recursive=args.recursive,
            extract_images=args.extract_images,
        )
    else:
        print(f"Error: La ruta '{source_path}' no es válida.")
        sys.exit(1)


if __name__ == "__main__":
    main()
