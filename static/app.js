/**
 * Lógica frontend interactiva para DocToMarkdown Studio & Editor
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elementos DOM
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const loadingText = document.getElementById('loadingText');
  const workspace = document.getElementById('workspace');
  const fileList = document.getElementById('fileList');
  const fileCount = document.getElementById('fileCount');
  const activeFileNameInput = document.getElementById('activeFileNameInput');
  const activeFileIcon = document.getElementById('activeFileIcon');
  const activeFileStats = document.getElementById('activeFileStats');
  
  // Tabs y vistas
  const tabSplit = document.getElementById('tabSplit');
  const tabEditor = document.getElementById('tabEditor');
  const tabRendered = document.getElementById('tabRendered');
  const previewBody = document.getElementById('previewBody');
  const renderedContainer = document.getElementById('renderedContainer');
  const rawContainer = document.getElementById('rawContainer');
  const rawMarkdownText = document.getElementById('rawMarkdownText');
  const editorToolbar = document.getElementById('editorToolbar');

  // Botones de acción
  const copyBtn = document.getElementById('copyBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const clearAllBtn = document.getElementById('clearAllBtn');
  const newDocBtnHeader = document.getElementById('newDocBtnHeader');
  const newDocBtnSidebar = document.getElementById('newDocBtnSidebar');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toastMessage');

  // Estado de la aplicación
  let convertedFiles = [];
  let activeIndex = -1;
  let currentViewMode = 'split'; // 'split', 'editor', o 'rendered'
  let newDocCounter = 1;

  // --- Manejo de Tema (Dark / Light) ---
  const savedTheme = localStorage.getItem('theme') || 'dark';
  setTheme(savedTheme);

  themeToggleBtn.addEventListener('click', () => {
    const isDark = document.body.classList.contains('dark-theme');
    setTheme(isDark ? 'light' : 'dark');
  });

  function setTheme(theme) {
    if (theme === 'light') {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      themeIcon.textContent = '🌙';
      localStorage.setItem('theme', 'light');
    } else {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      themeIcon.textContent = '☀️';
      localStorage.setItem('theme', 'dark');
    }
  }

  // --- Creación de Nuevo Archivo Markdown ---
  function createNewMarkdownDoc() {
    const filename = `nota_${newDocCounter++}.md`;
    const starterContent = `# ${filename.replace('.md', '')}\n\nEscribe tus notas en formato Markdown aquí.\n\n- [ ] Tarea 1\n- [ ] Tarea 2\n\n> Puedes usar la barra de herramientas superior o atajos de teclado como Ctrl+B y Ctrl+I.\n`;
    
    const lines = starterContent.split('\n').length;
    const words = starterContent.trim().split(/\s+/).length;
    const chars = starterContent.length;

    const newDoc = {
      filename: filename,
      markdown_filename: filename,
      markdown: starterContent,
      stats: {
        lines: lines,
        words: words,
        chars: chars,
        size_bytes: chars
      },
      success: true,
      error: null
    };

    convertedFiles.push(newDoc);
    updateWorkspace();
    setActiveFile(convertedFiles.length - 1);
    setViewMode('split');
    showToast(`📝 Creado '${filename}'`);
    rawMarkdownText.focus();
  }

  if (newDocBtnHeader) newDocBtnHeader.addEventListener('click', createNewMarkdownDoc);
  if (newDocBtnSidebar) newDocBtnSidebar.addEventListener('click', createNewMarkdownDoc);

  // --- Renombrar Archivo Activo ---
  activeFileNameInput.addEventListener('input', (e) => {
    if (activeIndex >= 0 && convertedFiles[activeIndex]) {
      let val = e.target.value.trim();
      if (!val) val = 'documento.md';
      convertedFiles[activeIndex].markdown_filename = val;
      updateSidebarList();
    }
  });

  // --- Drag and Drop y Selección de Archivos ---
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFiles(Array.from(files));
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
      fileInput.value = '';
    }
  });

  // --- Procesamiento y Envío a la API ---
  async function handleFiles(files) {
    const supportedExts = ['.pdf', '.docx', '.doc', '.md', '.markdown'];
    const validFiles = files.filter(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      return supportedExts.includes(ext);
    });

    if (validFiles.length === 0) {
      showToast('⚠️ Formato no compatible. Sube archivos .pdf, .docx, .doc o .md', true);
      return;
    }

    // Separar archivos .md para carga instantánea local
    const mdFiles = validFiles.filter(f => f.name.toLowerCase().endsWith('.md') || f.name.toLowerCase().endsWith('.markdown'));
    const docFiles = validFiles.filter(f => !f.name.toLowerCase().endsWith('.md') && !f.name.toLowerCase().endsWith('.markdown'));

    // Carga local de archivos .md
    for (const f of mdFiles) {
      try {
        const text = await f.text();
        const lines = text.split('\n').length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const chars = text.length;

        const res = {
          filename: f.name,
          markdown_filename: f.name.endsWith('.md') ? f.name : f.name + '.md',
          markdown: text,
          stats: { lines, words, chars, size_bytes: f.size },
          success: true,
          error: null
        };
        addOrUpdateFile(res);
      } catch (err) {
        console.error(err);
      }
    }

    if (docFiles.length > 0) {
      loadingText.textContent = `Convirtiendo ${docFiles.length} documento(s) a Markdown...`;
      loadingIndicator.classList.remove('hidden');

      const formData = new FormData();
      docFiles.forEach(file => formData.append('files', file));

      try {
        const response = await fetch('/api/convert', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Error en el servidor: ${response.statusText}`);
        }

        const results = await response.json();
        results.forEach(res => addOrUpdateFile(res));
        showToast(`✨ ${results.length} documento(s) procesados.`);
      } catch (err) {
        console.error(err);
        showToast(`❌ Error al convertir: ${err.message}`, true);
      } finally {
        loadingIndicator.classList.add('hidden');
      }
    }

    updateWorkspace();
    if (convertedFiles.length > 0) {
      setActiveFile(convertedFiles.length - 1);
    }
  }

  function addOrUpdateFile(fileObj) {
    const existingIdx = convertedFiles.findIndex(f => f.filename === fileObj.filename);
    if (existingIdx >= 0) {
      convertedFiles[existingIdx] = fileObj;
    } else {
      convertedFiles.push(fileObj);
    }
  }

  // --- Actualización de la Interfaz ---
  function updateWorkspace() {
    if (convertedFiles.length === 0) {
      workspace.classList.add('hidden');
      return;
    }

    workspace.classList.remove('hidden');
    fileCount.textContent = convertedFiles.length;
    updateSidebarList();
  }

  function updateSidebarList() {
    fileList.innerHTML = '';
    convertedFiles.forEach((file, index) => {
      const li = document.createElement('li');
      li.className = `file-item ${index === activeIndex ? 'active' : ''}`;
      
      const isPdf = file.filename.toLowerCase().endsWith('.pdf');
      const isMd = file.filename.toLowerCase().endsWith('.md');
      const icon = isPdf ? '📄' : (isMd ? '📋' : '📝');

      li.innerHTML = `
        <div class="file-item-info">
          <span class="file-item-icon">${icon}</span>
          <span class="file-item-name" title="${escapeHtml(file.markdown_filename || file.filename)}">${escapeHtml(file.markdown_filename || file.filename)}</span>
        </div>
        <span class="file-item-status ${file.success ? 'status-success' : 'status-error'}">
          ${file.success ? 'Listo' : 'Error'}
        </span>
      `;

      li.addEventListener('click', () => {
        setActiveFile(index);
      });

      fileList.appendChild(li);
    });
  }

  function setActiveFile(index) {
    if (index < 0 || index >= convertedFiles.length) return;
    activeIndex = index;
    const file = convertedFiles[index];

    // Actualizar clase activa en la lista
    document.querySelectorAll('.file-item').forEach((el, idx) => {
      el.classList.toggle('active', idx === index);
    });

    // Actualizar metadatos
    const isPdf = file.filename.toLowerCase().endsWith('.pdf');
    const isMd = file.filename.toLowerCase().endsWith('.md');
    activeFileIcon.textContent = isPdf ? '📄' : (isMd ? '📋' : '📝');
    activeFileNameInput.value = file.markdown_filename || file.filename;

    if (file.success) {
      rawMarkdownText.value = file.markdown;
      updateStatsAndPreview(file.markdown);
    } else {
      activeFileStats.textContent = 'Error';
      rawMarkdownText.value = `Error al procesar documento:\n${file.error}`;
      renderedContainer.innerHTML = `
        <div style="color: var(--danger); padding: 20px; background: var(--danger-light); border-radius: 8px;">
          <h3>⚠️ Error al procesar documento</h3>
          <p>${escapeHtml(file.error || 'Error desconocido')}</p>
        </div>
      `;
    }
  }

  // --- Edición en Tiempo Real ---
  rawMarkdownText.addEventListener('input', () => {
    if (activeIndex >= 0 && convertedFiles[activeIndex]) {
      const newText = rawMarkdownText.value;
      convertedFiles[activeIndex].markdown = newText;
      updateStatsAndPreview(newText);
    }
  });

  function updateStatsAndPreview(text) {
    const lines = text ? text.split('\n').length : 0;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;

    if (convertedFiles[activeIndex]) {
      convertedFiles[activeIndex].stats = { lines, words, chars };
    }
    activeFileStats.textContent = `${words} palabras · ${lines} líneas · ${chars} car.`;
    renderMarkdown(text);
  }

  // --- Atajos de Teclado en el Editor ---
  rawMarkdownText.addEventListener('keydown', (e) => {
    // Tabulación indentada
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = rawMarkdownText.selectionStart;
      const end = rawMarkdownText.selectionEnd;
      rawMarkdownText.value = rawMarkdownText.value.substring(0, start) + '  ' + rawMarkdownText.value.substring(end);
      rawMarkdownText.selectionStart = rawMarkdownText.selectionEnd = start + 2;
      rawMarkdownText.dispatchEvent(new Event('input'));
    }

    // Ctrl+B / Cmd+B -> Negrita
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
      e.preventDefault();
      applyFormatting('bold');
    }

    // Ctrl+I / Cmd+I -> Cursiva
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'i') {
      e.preventDefault();
      applyFormatting('italic');
    }
  });

  // --- Barra de Herramientas de Formato Markdown ---
  if (editorToolbar) {
    editorToolbar.addEventListener('click', (e) => {
      const btn = e.target.closest('.tool-btn');
      if (!btn) return;
      const tool = btn.dataset.tool;
      if (tool) {
        applyFormatting(tool);
      }
    });
  }

  function applyFormatting(tool) {
    rawMarkdownText.focus();
    const start = rawMarkdownText.selectionStart;
    const end = rawMarkdownText.selectionEnd;
    const val = rawMarkdownText.value;
    const selected = val.substring(start, end);

    let before = '';
    let after = '';
    let replacement = '';

    switch (tool) {
      case 'bold':
        before = '**';
        after = '**';
        replacement = selected || 'texto en negrita';
        break;
      case 'italic':
        before = '*';
        after = '*';
        replacement = selected || 'texto en cursiva';
        break;
      case 'strike':
        before = '~~';
        after = '~~';
        replacement = selected || 'texto tachado';
        break;
      case 'h1':
        before = '# ';
        after = '\n';
        replacement = selected || 'Título 1';
        break;
      case 'h2':
        before = '## ';
        after = '\n';
        replacement = selected || 'Título 2';
        break;
      case 'h3':
        before = '### ';
        after = '\n';
        replacement = selected || 'Título 3';
        break;
      case 'ul':
        before = '- ';
        after = '\n';
        replacement = selected || 'Elemento de lista';
        break;
      case 'ol':
        before = '1. ';
        after = '\n';
        replacement = selected || 'Elemento numerado';
        break;
      case 'task':
        before = '- [ ] ';
        after = '\n';
        replacement = selected || 'Tarea pendiente';
        break;
      case 'quote':
        before = '> ';
        after = '\n';
        replacement = selected || 'Cita';
        break;
      case 'code':
        before = '```javascript\n';
        after = '\n```\n';
        replacement = selected || '// Código aquí';
        break;
      case 'link':
        before = '[';
        after = '](https://ejemplo.com)';
        replacement = selected || 'Texto del enlace';
        break;
      case 'table':
        before = '\n| Encabezado 1 | Encabezado 2 | Encabezado 3 |\n| :--- | :--- | :--- |\n| Fila 1 | Dato A | Dato B |\n| Fila 2 | Dato C | Dato D |\n';
        after = '';
        replacement = '';
        break;
      case 'hr':
        before = '\n\n---\n\n';
        after = '';
        replacement = '';
        break;
      default:
        return;
    }

    const insertedText = before + replacement + after;
    rawMarkdownText.value = val.substring(0, start) + insertedText + val.substring(end);
    
    // Posicionar cursor
    rawMarkdownText.selectionStart = start + before.length;
    rawMarkdownText.selectionEnd = start + before.length + replacement.length;

    rawMarkdownText.dispatchEvent(new Event('input'));
  }

  // --- Renderizador de Markdown ---
  function renderMarkdown(md) {
    if (!renderedContainer) return;
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        renderedContainer.innerHTML = window.marked.parse(md || '');
        return;
      } catch (e) {
        console.warn('Error en marked.parse:', e);
      }
    }
    renderedContainer.innerHTML = fallbackMarkdownToHtml(md);
  }

  function fallbackMarkdownToHtml(md) {
    if (!md) return '';
    let html = escapeHtml(md);
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/^---$/gim, '<hr>');
    html = html.replace(/\n\n/g, '<br><br>');
    return `<div class="fallback-md">${html}</div>`;
  }

  // --- Cambio de pestañas de Vista (Split / Editor / Rendered) ---
  function setViewMode(mode) {
    currentViewMode = mode;
    [tabSplit, tabEditor, tabRendered].forEach(b => b.classList.remove('active'));

    previewBody.classList.remove('mode-split', 'mode-editor', 'mode-rendered');
    previewBody.classList.add(`mode-${mode}`);

    if (mode === 'split') {
      tabSplit.classList.add('active');
      editorToolbar.style.display = 'flex';
    } else if (mode === 'editor') {
      tabEditor.classList.add('active');
      editorToolbar.style.display = 'flex';
      rawMarkdownText.focus();
    } else if (mode === 'rendered') {
      tabRendered.classList.add('active');
      editorToolbar.style.display = 'none';
    }
  }

  tabSplit.addEventListener('click', () => setViewMode('split'));
  tabEditor.addEventListener('click', () => setViewMode('editor'));
  tabRendered.addEventListener('click', () => setViewMode('rendered'));

  // --- Copiar al Portapapeles ---
  copyBtn.addEventListener('click', async () => {
    if (activeIndex < 0 || !convertedFiles[activeIndex]) return;
    const textToCopy = rawMarkdownText.value;
    try {
      await navigator.clipboard.writeText(textToCopy);
      showToast('📋 ¡Markdown copiado al portapapeles!');
    } catch (e) {
      rawMarkdownText.select();
      document.execCommand('copy');
      showToast('📋 ¡Markdown copiado!');
    }
  });

  // --- Descargar Archivo Individual .md ---
  downloadBtn.addEventListener('click', () => {
    if (activeIndex < 0 || !convertedFiles[activeIndex]) return;
    const file = convertedFiles[activeIndex];
    let filename = activeFileNameInput.value.trim() || file.markdown_filename || 'documento.md';
    if (!filename.endsWith('.md')) filename += '.md';
    const content = rawMarkdownText.value;
    downloadBlob(content, filename, 'text/markdown;charset=utf-8');
    showToast(`💾 Descargando ${filename}`);
  });

  // --- Descargar Todos en ZIP ---
  downloadZipBtn.addEventListener('click', async () => {
    const successFiles = convertedFiles.filter(f => f.success);
    if (successFiles.length === 0) {
      showToast('⚠️ No hay archivos para descargar.', true);
      return;
    }

    try {
      showToast('📦 Preparando archivo ZIP...');
      const payload = {
        files: successFiles.map(f => ({
          filename: f.markdown_filename || f.filename,
          content: f.markdown
        }))
      };

      const response = await fetch('/api/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Error al generar el ZIP en el servidor');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'documentos_markdown.zip';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast('✅ Descarga del ZIP completada.');
    } catch (e) {
      console.error(e);
      showToast('❌ Error al descargar el archivo ZIP', true);
    }
  });

  // --- Limpiar Lista ---
  clearAllBtn.addEventListener('click', () => {
    if (confirm('¿Deseas limpiar todos los documentos?')) {
      convertedFiles = [];
      activeIndex = -1;
      updateWorkspace();
      showToast('Lista limpiada');
    }
  });

  // --- Funciones de Utilidad ---
  function downloadBlob(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }

  function showToast(message, isError = false) {
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    if (isError) {
      toast.style.borderColor = 'var(--danger)';
    } else {
      toast.style.borderColor = 'var(--accent)';
    }

    clearTimeout(toast.timeoutId);
    toast.timeoutId = setTimeout(() => {
      toast.classList.add('hidden');
    }, 3200);
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
