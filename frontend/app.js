const API_BASE = "/api";

// --- DOM refs ---
const modeTabs = document.querySelectorAll(".mode-tab");
const convertMode = document.getElementById("convertMode");
const hashMode = document.getElementById("hashMode");
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
        item.innerHTML = `
            <div class="file-icon">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
            </div>
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

// --- Init ---
loadFormatData();
