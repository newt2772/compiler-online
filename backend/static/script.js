const STORAGE_KEY = "compiler-theme";
const MONACO_CDN = "https://unpkg.com/monaco-editor@0.45.0/min/vs";

let editor = null;
let languages = [];
let starterCodes = {};

const langMonacoMap = {
    cpp: "cpp",
    c: "c",
    python: "python",
    java: "java",
    javascript: "javascript",
};

// --- Theme ---

function isDark() {
    return document.body.classList.contains("dark-mode");
}

function setTheme(dark) {
    document.body.classList.toggle("dark-mode", dark);
    document.getElementById("theme-toggle").textContent = dark
        ? "Use Light"
        : "Use Dark";
    localStorage.setItem(STORAGE_KEY, dark ? "dark" : "light");
    if (editor) {
        monaco.editor.setTheme(dark ? "vs-dark" : "vs");
    }
}

document.getElementById("theme-toggle").addEventListener("click", function () {
    setTheme(!isDark());
});

// --- Monaco Editor ---

require.config({ paths: { vs: MONACO_CDN } });

require(["vs/editor/editor.main"], function () {
    editor = monaco.editor.create(
        document.getElementById("editor-container"),
        {
            value: "",
            language: "cpp",
            theme: isDark() ? "vs-dark" : "vs",
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace",
            automaticLayout: true,
            scrollBeyondLastLine: false,
            lineNumbers: "on",
            tabSize: 4,
            wordWrap: "on",
        }
    );

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, runCode);
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, function (e) {
        saveCurrentCode();
    });

    loadLanguages();
    loadHistory();
});

// --- Languages ---

async function loadLanguages() {
    try {
        const resp = await fetch("/api/languages");
        languages = await resp.json();
    } catch {
        languages = [];
    }

    const select = document.getElementById("language-select");
    select.innerHTML = "";
    languages.forEach(function (lang) {
        const opt = document.createElement("option");
        opt.value = lang.id;
        opt.textContent = lang.name;
        select.appendChild(opt);
        starterCodes[lang.id] = lang.starter_code;
    });

    if (languages.length > 0) {
        select.value = languages[0].id;
        applyLanguage(languages[0].id);
    }
}

function applyLanguage(langId) {
    if (!editor) return;
    const model = editor.getModel();
    monaco.editor.setModelLanguage(model, langMonacoMap[langId] || langId);

    const currentCode = editor.getValue().trim();
    const isStarterOrEmpty =
        !currentCode ||
        Object.values(starterCodes).some(
            function (sc) { return sc.trim() === currentCode; }
        );

    if (isStarterOrEmpty && starterCodes[langId]) {
        editor.setValue(starterCodes[langId]);
    }

    document.getElementById("lang-hint").textContent =
        (languages.find(function (l) { return l.id === langId; }) || {}).name || langId;
}

document
    .getElementById("language-select")
    .addEventListener("change", function (e) {
        applyLanguage(e.target.value);
    });

// --- Code Execution ---

async function runCode() {
    var runBtn = document.getElementById("run-btn");
    var outputEl = document.getElementById("output");
    var langId = document.getElementById("language-select").value;
    var code = editor ? editor.getValue() : "";
    var input = document.getElementById("input").value;

    if (!code.trim()) {
        outputEl.textContent = "No code to run.";
        outputEl.className = "error";
        return;
    }

    runBtn.disabled = true;
    runBtn.textContent = "Running...";
    outputEl.textContent = "Compiling and running...";
    outputEl.className = "";

    try {
        var resp = await fetch("/api/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: langId, code: code, input: input }),
        });
        var result = await resp.json();

        if (result.success) {
            var text = result.output || "(No output)";
            if (result.error) text += "\n\nStderr:\n" + result.error;
            outputEl.textContent = text;
            outputEl.className = "";
        } else {
            outputEl.textContent = result.output || result.error || "Unknown error";
            outputEl.className = "error";
        }
    } catch (err) {
        outputEl.textContent = "Network error: " + err.message;
        outputEl.className = "error";
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = "Compile & Run";
        loadHistory();
    }
}

document.getElementById("run-btn").addEventListener("click", runCode);

// --- Save Current Code ---

async function saveCurrentCode() {
    try {
        var resp = await fetch("/api/history/recent");
        var recent = await resp.json();
        if (recent.length === 0) {
            showToast("Run code first, then save.");
            return;
        }
        var latest = recent[0];
        if (latest.is_saved) {
            showToast("Already saved.");
            return;
        }
        await fetch("/api/history/" + latest.id + "/save", { method: "POST" });
        showToast("Saved!");
        loadHistory();
    } catch {
        showToast("Failed to save.");
    }
}

document.getElementById("save-btn").addEventListener("click", saveCurrentCode);

// --- History ---

async function loadHistory() {
    try {
        var [recentResp, savedResp] = await Promise.all([
            fetch("/api/history/recent"),
            fetch("/api/history/saved"),
        ]);
        var recent = await recentResp.json();
        var saved = await savedResp.json();

        renderHistoryList("recent-list", recent, false);
        renderHistoryList("saved-list", saved, true);
    } catch {
        // silently fail
    }
}

function renderHistoryList(listId, entries, isSaved) {
    var ul = document.getElementById(listId);
    ul.innerHTML = "";

    entries.forEach(function (entry) {
        var li = document.createElement("li");
        li.className = "history-item";

        var badge = document.createElement("span");
        badge.className = "lang-badge";
        badge.textContent = entry.language;

        var preview = document.createElement("span");
        preview.className = "history-preview";
        var firstLine = (entry.code || "").split("\n")[0];
        preview.textContent =
            firstLine.length > 40 ? firstLine.substring(0, 40) + "..." : firstLine;

        var time = document.createElement("span");
        time.className = "history-time";
        time.textContent = timeAgo(entry.created_at);

        var actions = document.createElement("span");
        actions.className = "history-actions";

        var loadBtn = document.createElement("button");
        loadBtn.textContent = "Load";
        loadBtn.addEventListener("click", function () {
            loadEntry(entry);
        });
        actions.appendChild(loadBtn);

        if (isSaved) {
            var delBtn = document.createElement("button");
            delBtn.textContent = "Del";
            delBtn.className = "delete-btn";
            delBtn.addEventListener("click", function () {
                deleteEntry(entry.id);
            });
            actions.appendChild(delBtn);
        } else {
            var saveBtn = document.createElement("button");
            saveBtn.textContent = "Save";
            saveBtn.addEventListener("click", function () {
                saveEntry(entry.id);
            });
            actions.appendChild(saveBtn);
        }

        li.appendChild(badge);
        li.appendChild(preview);
        li.appendChild(time);
        li.appendChild(actions);
        ul.appendChild(li);
    });
}

function loadEntry(entry) {
    var select = document.getElementById("language-select");
    select.value = entry.language;
    applyLanguageWithoutStarterCode(entry.language);
    if (editor) editor.setValue(entry.code || "");
    document.getElementById("input").value = entry.input || "";
    showToast("Loaded!");
}

function applyLanguageWithoutStarterCode(langId) {
    if (!editor) return;
    var model = editor.getModel();
    monaco.editor.setModelLanguage(model, langMonacoMap[langId] || langId);
    document.getElementById("lang-hint").textContent =
        (languages.find(function (l) { return l.id === langId; }) || {}).name || langId;
}

async function saveEntry(id) {
    try {
        await fetch("/api/history/" + id + "/save", { method: "POST" });
        showToast("Saved!");
        loadHistory();
    } catch {
        showToast("Failed to save.");
    }
}

async function deleteEntry(id) {
    try {
        await fetch("/api/history/" + id, { method: "DELETE" });
        showToast("Deleted.");
        loadHistory();
    } catch {
        showToast("Failed to delete.");
    }
}

// --- Output Actions ---

document
    .getElementById("copy-output")
    .addEventListener("click", async function () {
        var text = document.getElementById("output").textContent;
        if (!text.trim()) return;
        try {
            await navigator.clipboard.writeText(text);
            showToast("Copied!");
        } catch {
            showToast("Copy failed.");
        }
    });

document
    .getElementById("clear-output")
    .addEventListener("click", function () {
        var el = document.getElementById("output");
        el.textContent = "Ready.";
        el.className = "";
    });

// --- Utilities ---

function showToast(message) {
    var toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(function () {
        toast.classList.remove("show");
    }, 2000);
}

function timeAgo(dateStr) {
    if (!dateStr) return "";
    var now = Date.now();
    var then = new Date(dateStr + "Z").getTime();
    var diff = Math.floor((now - then) / 1000);

    if (diff < 60) return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return Math.floor(diff / 86400) + "d ago";
}
