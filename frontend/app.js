const API_BASE = "/api";

// --- DOM refs ---
const modeTabs = document.querySelectorAll(".mode-tab");
const convertMode = document.getElementById("convertMode");
const hashMode = document.getElementById("hashMode");
const qrMode = document.getElementById("qrMode");
const dropZone = document.getElementById("dropZone");
const dropContent = document.getElementById("dropContent");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const controls = document.getElementById("controls");
const formatSelect = document.getElementById("formatSelect");
const convertBtn = document.getElementById("convertBtn");
const settingsPanel = document.getElementById("settingsPanel");
const settingsToggle = document.getElementById("settingsToggle");
const settingsBody = document.getElementById("settingsBody");
const qualityRange = document.getElementById("qualityRange");
const qualityValue = document.getElementById("qualityValue");
const bitrateSelect = document.getElementById("bitrateSelect");
const cleanMetaCheck = document.getElementById("cleanMetaCheck");
const urlInput = document.getElementById("urlInput");
const convertUrlBtn = document.getElementById("convertUrlBtn");
const progressSection = document.getElementById("progressSection");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const resultSection = document.getElementById("resultSection");
const resultText = document.getElementById("resultText");
const downloadBtn = document.getElementById("downloadBtn");
const resetBtn = document.getElementById("resetBtn");
const hashText = document.getElementById("hashText");
const hashFileInput = document.getElementById("hashFileInput");
const hashFileZone = document.getElementById("hashFileZone");
const hashFileLabel = document.getElementById("hashFileLabel");
const hashBtn = document.getElementById("hashBtn");
const hashResults = document.getElementById("hashResults");
const hashMd5 = document.getElementById("hashMd5");
const hashSha1 = document.getElementById("hashSha1");
const hashSha256 = document.getElementById("hashSha256");
const errorToast = document.getElementById("errorToast");
const errorMessage = document.getElementById("errorMessage");

// --- QR DOM refs ---
const qrTabs = document.querySelectorAll(".qr-tab");
const qrEncode = document.getElementById("qrEncode");
const qrDecode = document.getElementById("qrDecode");
const qrTextInput = document.getElementById("qrTextInput");
const qrFormatSelect = document.getElementById("qrFormatSelect");
const qrEncodeBtn = document.getElementById("qrEncodeBtn");
const qrResultImg = document.getElementById("qrResultImg");
const qrImage = document.getElementById("qrImage");
const qrDownloadBtn = document.getElementById("qrDownloadBtn");
const qrFileZone = document.getElementById("qrFileZone");
const qrFileInput = document.getElementById("qrFileInput");
const qrFileLabel = document.getElementById("qrFileLabel");
const qrDecodeBtn = document.getElementById("qrDecodeBtn");
const qrDecodeResult = document.getElementById("qrDecodeResult");
const qrDecodedText = document.getElementById("qrDecodedText");

// --- State ---
let selectedFiles = [];
let categoryMap = {};
let formatMap = {};
let currentMode = "convert";

// --- Helpers ---
function showError(msg) {
    errorMessage.textContent = msg;
    errorToast.classList.add("show");
    setTimeout(() => errorToast.classList.remove("show"), 4000);
}

function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function getExtension(filename) {
    const dot = filename.lastIndexOf(".");
    return dot === -1 ? "" : filename.slice(dot + 1).toLowerCase();
}

function findCategory(ext) {
    for (const [cat, exts] of Object.entries(categoryMap)) {
        if (exts.includes(ext)) return cat;
    }
    return null;
}

function isImageExt(ext) {
    return ["png", "jpg", "jpeg", "webp", "bmp", "gif", "ico"].includes(ext);
}

function isAudioExt(ext) {
    return ["mp3", "wav", "ogg", "flac", "m4a", "aac"].includes(ext);
}

function setProgress(pct, label) {
    progressFill.style.width = pct + "%";
    progressText.className = "progress-text";
    progressText.textContent = label;
}

function showProgressError(msg) {
    progressText.className = "progress-text progress-error";
    progressText.textContent = msg;
}

// --- Load format data ---
async function loadFormatData() {
    try {
        const [catRes, fmtRes] = await Promise.all([
            fetch(`${API_BASE}/categories`),
            fetch(`${API_BASE}/formats`),
        ]);
        categoryMap = await catRes.json();
        formatMap = await fmtRes.json();
    } catch {
        showError("Не удалось загрузить данные. Убедитесь, что бэкенд запущен.");
    }
}

// --- Mode switching ---
modeTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        modeTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        currentMode = tab.dataset.mode;
        convertMode.style.display = currentMode === "convert" ? "" : "none";
        hashMode.style.display = currentMode === "hash" ? "" : "none";
        qrMode.style.display = currentMode === "qr" ? "" : "none";
    });
});

// --- Settings toggle ---
settingsToggle.addEventListener("click", () => {
    settingsPanel.classList.toggle("open");
});

qualityRange.addEventListener("input", () => {
    qualityValue.textContent = qualityRange.value;
});

// --- File management (convert mode) ---
function addFiles(files) {
    for (const file of files) {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    }
    renderFileList();
    updateControls();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();
    updateControls();
}

function renderFileList() {
    fileList.innerHTML = "";
    if (selectedFiles.length === 0) {
        fileList.style.display = "none";
        return;
    }
    fileList.style.display = "flex";
    selectedFiles.forEach((file, i) => {
        const item = document.createElement("div");
        item.className = "file-list-item";

        const ext = getExtension(file.name);
        let previewHtml = "";
        if (isImageExt(ext)) {
            const url = URL.createObjectURL(file);
            previewHtml = `<div class="file-preview"><img src="${url}" alt=""></div>`;
        } else if (isAudioExt(ext)) {
            const url = URL.createObjectURL(file);
            previewHtml = `<div class="file-preview"><audio controls><source src="${url}" type="${file.type}"></audio></div>`;
        } else {
            previewHtml = `<div class="file-icon">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
            </div>`;
        }

        item.innerHTML = `
            ${previewHtml}
            <div class="file-body">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatBytes(file.size)}</span>
            </div>
            <button class="btn-remove" data-index="${i}" title="Удалить">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;
        item.querySelector(".btn-remove").addEventListener("click", (e) => {
            e.stopPropagation();
            removeFile(i);
        });
        fileList.appendChild(item);
    });
}

function updateControls() {
    if (selectedFiles.length === 0) {
        controls.style.display = "none";
        settingsPanel.style.display = "none";
        return;
    }

    const ext = getExtension(selectedFiles[0].name);
    const cat = findCategory(ext);
    if (!cat) {
        controls.style.display = "none";
        return;
    }

    formatSelect.innerHTML = "";
    const targets = formatMap[cat]?.[ext] || [];
    targets.forEach(fmt => {
        const opt = document.createElement("option");
        opt.value = fmt;
        opt.textContent = fmt.toUpperCase();
        formatSelect.appendChild(opt);
    });

    if (targets.length > 0) {
        controls.style.display = "flex";
        settingsPanel.style.display = "block";
        settingsPanel.classList.remove("open");
    } else {
        controls.style.display = "none";
        settingsPanel.style.display = "none";
    }
}

// --- Clipboard paste (Ctrl+V) ---
document.addEventListener("paste", async (e) => {
    if (currentMode !== "convert") return;

    const items = e.clipboardData.items;
    let found = false;

    for (const item of items) {
        if (item.kind === "file") {
            const file = item.getAsFile();
            if (file) {
                const ts = Date.now();
                const renamed = new File([file], `clipboard_${ts}.${file.name.split(".").pop() || "png"}`, { type: file.type });
                addFiles([renamed]);
                found = true;
            }
        }
    }

    if (!found) {
        const text = e.clipboardData.getData("text");
        if (text && text.trim()) {
            const ts = Date.now();
            const blob = new Blob([text], { type: "text/plain" });
            const file = new File([blob], `clipboard_${ts}.txt`, { type: "text/plain" });
            addFiles([file]);
            found = true;
        }
    }
});

// --- Drop zone ---
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
        addFiles(e.dataTransfer.files);
    }
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
        addFiles(fileInput.files);
    }
    fileInput.value = "";
});

// --- Convert flow ---
convertBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) return;
    const target = formatSelect.value;
    if (!target) { showError("Выберите целевой формат"); return; }

    convertBtn.disabled = true;
    resultSection.style.display = "none";
    dropZone.classList.remove("success");
    progressSection.style.display = "block";
    setProgress(0, "Загрузка...");

    const formData = new FormData();
    for (const file of selectedFiles) {
        formData.append("files", file);
    }
    formData.append("target_format", target);
    formData.append("quality", qualityRange.value);
    formData.append("bitrate", bitrateSelect.value);
    formData.append("clean_meta", cleanMetaCheck.checked ? "true" : "false");

    try {
        const xhr = new XMLHttpRequest();
        const promise = new Promise((resolve, reject) => {
            xhr.upload.addEventListener("progress", (e) => {
                if (e.lengthComputable) {
                    const pct = Math.min(95, Math.round((e.loaded / e.total) * 100));
                    setProgress(pct, `Загрузка... ${pct}%`);
                }
            });
            xhr.addEventListener("load", () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    setProgress(100, "Обработка завершена!");
                    resolve(xhr.response);
                } else {
                    const reader = new FileReader();
                    reader.onload = () => {
                        let msg = "Ошибка конвертации";
                        try { const err = JSON.parse(reader.result); msg = err.error || err.detail || msg; } catch {}
                        reject(new Error(msg));
                    };
                    reader.readAsText(xhr.response);
                }
            });
            xhr.addEventListener("error", () => reject(new Error("Сетевая ошибка")));
            xhr.addEventListener("abort", () => reject(new Error("Отменено")));
            xhr.responseType = "blob";
            xhr.open("POST", `${API_BASE}/convert`);
            xhr.send(formData);
        });

        const blob = await promise;
        const isZip = selectedFiles.length > 1;
        const outName = isZip ? "converted.zip" : selectedFiles[0].name.replace(
            new RegExp(`\\.${getExtension(selectedFiles[0].name)}$`), "." + target
        );

        const url = URL.createObjectURL(blob);
        downloadBtn.href = url;
        downloadBtn.download = outName;

        dropZone.classList.add("success");
        resultText.textContent = isZip ? "Все файлы сконвертированы!" : "Конвертация завершена!";
        setProgress(100, "Успешно сконвертировано!");
        resultSection.style.display = "block";
    } catch (err) {
        showProgressError(err.message);
    } finally {
        convertBtn.disabled = false;
    }
});

resetBtn.addEventListener("click", () => {
    selectedFiles = [];
    renderFileList();
    controls.style.display = "none";
    settingsPanel.style.display = "none";
    progressSection.style.display = "none";
    resultSection.style.display = "none";
    dropZone.classList.remove("success");
    setProgress(0, "");
});

// --- Convert URL flow ---
convertUrlBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) { showError("Введите URL для скачивания и конвертации"); return; }

    convertUrlBtn.disabled = true;
    resultSection.style.display = "none";
    progressSection.style.display = "block";
    setProgress(0, "Загрузка по URL...");

    const target = formatSelect.value || "jpg";

    const formData = new FormData();
    formData.append("url", url);
    formData.append("target_format", target);
    formData.append("quality", qualityRange.value);
    formData.append("bitrate", bitrateSelect.value);
    formData.append("clean_meta", cleanMetaCheck.checked ? "true" : "false");

    try {
        const xhr = new XMLHttpRequest();
        const promise = new Promise((resolve, reject) => {
            xhr.addEventListener("load", () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    setProgress(100, "Готово!");
                    resolve(xhr.response);
                } else {
                    const reader = new FileReader();
                    reader.onload = () => {
                        let msg = "Ошибка";
                        try { const err = JSON.parse(reader.result); msg = err.error || err.detail || msg; } catch {}
                        reject(new Error(msg));
                    };
                    reader.readAsText(xhr.response);
                }
            });
            xhr.addEventListener("error", () => reject(new Error("Сетевая ошибка")));
            xhr.addEventListener("abort", () => reject(new Error("Отменено")));
            xhr.responseType = "blob";
            xhr.open("POST", `${API_BASE}/convert-url`);
            xhr.send(formData);
        });

        const blob = await promise;
        const outName = `converted_${Date.now()}.${target}`;

        const blobUrl = URL.createObjectURL(blob);
        downloadBtn.href = blobUrl;
        downloadBtn.download = outName;

        resultText.textContent = "Конвертация по URL завершена!";
        setProgress(100, "Успешно!");
        resultSection.style.display = "block";
    } catch (err) {
        showProgressError(err.message);
    } finally {
        convertUrlBtn.disabled = false;
    }
});

// --- Hash mode ---
hashFileZone.addEventListener("click", () => hashFileInput.click());

hashFileInput.addEventListener("change", () => {
    if (hashFileInput.files.length) {
        hashFileLabel.textContent = hashFileInput.files[0].name;
        hashFileZone.classList.add("has-file");
    }
});

hashBtn.addEventListener("click", async () => {
    const text = hashText.value.trim();
    const file = hashFileInput.files[0];

    if (!text && !file) {
        showError("Введите текст или выберите файл");
        return;
    }

    hashBtn.disabled = true;
    hashResults.style.display = "none";

    const formData = new FormData();
    if (file) {
        formData.append("file", file);
    } else {
        formData.append("text", text);
    }

    try {
        const res = await fetch(`${API_BASE}/hash`, { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) {
            showError(data.error || data.detail || "Ошибка вычисления хэша");
            return;
        }
        hashMd5.textContent = data.md5;
        hashSha1.textContent = data.sha1;
        hashSha256.textContent = data.sha256;
        hashResults.style.display = "flex";
    } catch {
        showError("Сетевая ошибка");
    } finally {
        hashBtn.disabled = false;
    }
});

// --- QR Mode tabs ---
qrTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        qrTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        const mode = tab.dataset.qrMode;
        qrEncode.style.display = mode === "encode" ? "" : "none";
        qrDecode.style.display = mode === "decode" ? "" : "none";
    });
});

// --- QR Encode ---
qrEncodeBtn.addEventListener("click", async () => {
    const text = qrTextInput.value.trim();
    if (!text) { showError("Введите текст или URL для QR-кода"); return; }

    qrEncodeBtn.disabled = true;
    qrResultImg.style.display = "none";

    const fmt = qrFormatSelect.value;

    const formData = new FormData();
    formData.append("text", text);
    formData.append("fmt", fmt);

    try {
        const res = await fetch(`${API_BASE}/qr/encode`, { method: "POST", body: formData });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: "Ошибка генерации QR" }));
            throw new Error(err.error || err.detail || "Ошибка генерации QR");
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        qrImage.src = url;
        qrDownloadBtn.href = url;
        qrDownloadBtn.download = `qrcode.${fmt}`;
        qrResultImg.style.display = "block";
    } catch (err) {
        showError(err.message);
    } finally {
        qrEncodeBtn.disabled = false;
    }
});

// --- QR Decode ---
qrFileZone.addEventListener("click", () => qrFileInput.click());

qrFileInput.addEventListener("change", () => {
    if (qrFileInput.files.length) {
        qrFileLabel.textContent = qrFileInput.files[0].name;
        qrFileZone.classList.add("has-file");
    }
});

qrDecodeBtn.addEventListener("click", async () => {
    const file = qrFileInput.files[0];
    if (!file) { showError("Выберите изображение с QR-кодом"); return; }

    qrDecodeBtn.disabled = true;
    qrDecodeResult.style.display = "none";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_BASE}/qr/decode`, { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || data.detail || "Ошибка декодирования");
        }
        qrDecodedText.value = data.text;
        qrDecodeResult.style.display = "flex";
    } catch (err) {
        showError(err.message);
    } finally {
        qrDecodeBtn.disabled = false;
    }
});

// --- Service Worker ---
if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
}

// --- Init ---
loadFormatData();
