const API_BASE = "http://localhost:8000/api";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const dropContent = document.getElementById("dropContent");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const removeBtn = document.getElementById("removeFile");
const controls = document.getElementById("controls");
const formatSelect = document.getElementById("formatSelect");
const convertBtn = document.getElementById("convertBtn");
const progressSection = document.getElementById("progressSection");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const resultSection = document.getElementById("resultSection");
const downloadBtn = document.getElementById("downloadBtn");
const resetBtn = document.getElementById("resetBtn");
const errorToast = document.getElementById("errorToast");
const errorMessage = document.getElementById("errorMessage");

let selectedFile = null;
let categoryMap = {};
let formatMap = {};

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

async function loadFormatData() {
    try {
        const [catRes, fmtRes] = await Promise.all([
            fetch(`${API_BASE}/categories`),
            fetch(`${API_BASE}/formats`),
        ]);
        categoryMap = await catRes.json();
        formatMap = await fmtRes.json();
    } catch {
        showError("Не удалось загрузить данные о форматах. Убедитесь, что бэкенд запущен.");
    }
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

function populateFormats(ext) {
    formatSelect.innerHTML = "";
    const cat = findCategory(ext);
    if (!cat) return;

    const targets = formatMap[cat]?.[ext] || [];
    targets.forEach((fmt) => {
        const opt = document.createElement("option");
        opt.value = fmt;
        opt.textContent = fmt.toUpperCase();
        formatSelect.appendChild(opt);
    });

    controls.style.display = targets.length > 0 ? "flex" : "none";
}

function selectFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    dropContent.style.display = "none";
    fileInfo.style.display = "flex";
    resultSection.style.display = "none";
    progressSection.style.display = "none";

    const ext = getExtension(file.name);
    populateFormats(ext);
}

function resetUI() {
    selectedFile = null;
    fileInput.value = "";
    dropContent.style.display = "";
    fileInfo.style.display = "none";
    controls.style.display = "none";
    progressSection.style.display = "none";
    resultSection.style.display = "none";
    progressFill.style.width = "0%";
}

// --- Drag & Drop ---
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
    const file = e.dataTransfer.files[0];
    if (file) selectFile(file);
});

fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) selectFile(fileInput.files[0]);
});

removeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUI();
});

// --- Convert ---
convertBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    const target = formatSelect.value;
    if (!target) {
        showError("Выберите целевой формат");
        return;
    }

    convertBtn.disabled = true;
    progressSection.style.display = "block";
    resultSection.style.display = "none";
    progressFill.style.width = "0%";
    progressText.textContent = "Загрузка...";

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("target_format", target);

    try {
        const xhr = new XMLHttpRequest();

        const promise = new Promise((resolve, reject) => {
            xhr.upload.addEventListener("progress", (e) => {
                if (e.lengthComputable) {
                    const pct = Math.round((e.loaded / e.total) * 80);
                    progressFill.style.width = pct + "%";
                    if (pct < 80) progressText.textContent = `Загрузка... ${pct}%`;
                }
            });

            xhr.addEventListener("loadstart", () => {
                progressFill.style.width = "0%";
            });

            xhr.addEventListener("load", () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    progressFill.style.width = "100%";
                    progressText.textContent = "Обработка завершена!";
                    resolve(xhr.response);
                } else {
                    let msg = "Ошибка конвертации";
                    try {
                        const err = JSON.parse(xhr.responseText);
                        msg = err.detail || msg;
                    } catch {}
                    reject(new Error(msg));
                }
            });

            xhr.addEventListener("error", () => reject(new Error("Сетевая ошибка")));
            xhr.addEventListener("abort", () => reject(new Error("Запрос отменён")));

            xhr.responseType = "blob";
            xhr.open("POST", `${API_BASE}/convert`);
            xhr.send(formData);
        });

        const blob = await promise;

        const ext = getExtension(selectedFile.name);
        const outName = selectedFile.name.replace(new RegExp(`\\.${ext}$`), "." + target);

        const url = URL.createObjectURL(blob);
        downloadBtn.href = url;
        downloadBtn.download = outName;

        resultSection.style.display = "block";
        progressSection.style.display = "none";
    } catch (err) {
        progressSection.style.display = "none";
        showError(err.message);
    } finally {
        convertBtn.disabled = false;
    }
});

// --- Reset ---
resetBtn.addEventListener("click", resetUI);

// --- Init ---
loadFormatData();
