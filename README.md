# 📄 DocToMarkdown Studio

> Aplicación completa para convertir documentos de **Microsoft Word (.docx, .doc)** y **PDF (.pdf)** a formato **Markdown (.md)** limpio, estructurado y compatible con GitHub, Obsidian, Notion y LLMs.

Incluye **dos modalidades de uso**:
1. 🌐 **Aplicación Web Interactiva**: Interfaz visual en el navegador con arrastrar y soltar, previsualización en vivo lado a lado, copia al portapapeles y descarga individual o en `.zip`.
2. 💻 **Herramienta CLI por Terminal**: Permite convertir archivos individuales o procesar carpetas completas por lotes (batch) de forma ultrarrápida.

---

## ✨ Características Principales

- **Formatos Soportados**:
  - `PDF (.pdf)` mediante PyMuPDF / PyMuPDF4LLM con preservación de tablas, jerarquía de títulos y párrafos.
  - `Word Moderno (.docx)` mediante Mammoth + Markdownify (generación de HTML semántico limpio y conversión a Markdown sin metadatos basura de Office).
  - `Word Legado (.doc 97-2003)` con motor de extracción de texto estructurado.
  - `Markdown (.md / .markdown)` para abrir, editar y visualizar directamente archivos Markdown existentes.
- **Editor de Markdown Integrado**:
  - ✏️ **Edición en Tiempo Real**: Modifica el texto y observa la actualización inmediata en la vista previa.
  - ◫ **Vista Dividida (Split Screen)**: Editor a la izquierda y visualización en tiempo real a la derecha.
  - 🛠️ **Barra de Herramientas de Formato**: Botones para Negrita (**B**), Cursiva (*I*), Tachado (~~S~~), Títulos (H1, H2, H3), Listas, Tareas (☑), Citas (❝), Bloques de código (`</>`), Tablas y Enlaces.
  - ⌨️ **Atajos de Teclado**: Soporte para `Ctrl+B` (Negrita), `Ctrl+I` (Cursiva) e indentación con tecla `Tab`.
  - ➕ **Crear Nuevos Documentos**: Botón para crear notas o documentos `.md` en blanco desde cero.
  - 🏷️ **Renombrado en Vivo**: Puedes cambiar el nombre del archivo directamente antes de descargarlo.
- **Vista Previa Dual**:
  - 👁️ **Vista Previa Renderizada**: Renderizado visual inmediato de cómo se verá el documento.
  - 💻 **Código Markdown Fuente**: Editor/visor con contador de líneas, palabras y caracteres.
- **Acciones Rápidas**:
  - 📋 Botón para copiar directamente al portapapeles con un clic.
  - ⬇️ Descarga inmediata del archivo `.md`.
  - 📦 Descarga masiva en un archivo `.ZIP` cuando se convierten varios documentos.
- **Tema Claro y Oscuro**: Alterna entre tema oscuro moderno o tema claro según tu preferencia.

---

## 🚀 Inicio Rápido en Windows

### Opción 1: Iniciar la Aplicación Web (Recomendado)
Simplemente haz **doble clic** en:
```bat
iniciar_web.bat
```
El script activará el entorno virtual e iniciará el servidor abriendo tu navegador en `http://localhost:8011`.

O manualmente desde la terminal:
```powershell
.\.venv\Scripts\activate
python app.py
```

### Opción 2: Usar la Herramienta de Línea de Comandos (CLI)
Puedes arrastrar un archivo directamente sobre el archivo `convertir_cli.bat` o usar la consola:

#### Modo Interactivo:
```powershell
python cli.py
```
*(Te pedirá la ruta del archivo o carpeta paso a paso)*.

#### Convertir un archivo individual:
```powershell
python cli.py "ruta\a\tu\documento.docx"
```
*(Genera automáticamente `documento.md` en la misma carpeta)*.

#### Especificar nombre o carpeta de salida:
```powershell
python cli.py "documento.pdf" -o "salida\resumen.md"
```

#### Procesamiento por lotes (carpeta completa):
```powershell
python cli.py "C:\mis_documentos\" -o "C:\mis_markdowns\" --recursive
```

---

## 📁 Estructura del Proyecto

```text
focused-hertz/
│
├── app.py                 # Servidor backend web (FastAPI + Uvicorn)
├── cli.py                 # Interfaz de línea de comandos (CLI)
├── converter.py           # Motor central de conversión de Word y PDF
├── requirements.txt       # Dependencias del proyecto
├── iniciar_web.bat        # Lanzador rápido con 1-clic para la app web
├── convertir_cli.bat      # Lanzador rápido para consola / drag & drop en Windows
│
├── static/                # Frontend web interactivo
│   ├── index.html         # Interfaz web responsiva
│   ├── style.css          # Estilos modernos (dark/light theme)
│   └── app.js             # Lógica de arrastrar y soltar, preview y descarga
│
└── .venv/                 # Entorno virtual de Python
```

---

## 🛠️ Instalación Manual de Dependencias

Si deseas instalar el entorno en otra máquina:

```powershell
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activar el entorno
.\.venv\Scripts\activate

# 3. Instalar librerías
pip install -r requirements.txt
```
