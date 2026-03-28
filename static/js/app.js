(function () {
  const EMS = (window.EMS = window.EMS || {});

  /** @type {{ id: string, file: File }[]} */
  let library = [];
  let fileIdSeq = 0;
  let lastResultCsv = "";
  let lastDownloadFilename = "result.csv";

  function isMergeMode() {
    const radio = document.querySelector('input[name="work_mode"]:checked');
    return !!(radio && radio.value === "merge");
  }

  function setMessage(html, type) {
    const el = document.getElementById("message");
    el.innerHTML = html;
    el.className = type ? "msg " + type : "";
    el.style.display = html ? "block" : "none";
  }

  function fmtSize(size) {
    if (size < 1024) {
      return size + " B";
    }
    if (size < 1024 * 1024) {
      return (size / 1024).toFixed(1) + " KB";
    }
    return (size / (1024 * 1024)).toFixed(1) + " MB";
  }

  function chartHasData() {
    return typeof EMS.chartHasData === "function" ? EMS.chartHasData() : false;
  }

  function updateButtons() {
    const idA = document.getElementById("sel-a").value;
    const idB = document.getElementById("sel-b").value;
    const validPair =
      idA &&
      idB &&
      idA !== idB &&
      library.some((item) => item.id === idA) &&
      library.some((item) => item.id === idB);

    document.getElementById("compute").disabled = !validPair;
    document.getElementById("download").disabled = !lastResultCsv;
    document.getElementById("download-html").disabled = !chartHasData();

    const downloadButton = document.getElementById("download");
    downloadButton.textContent = lastResultCsv
      ? "Скачать " + lastDownloadFilename
      : "Скачать CSV";
  }

  function syncModeUI() {
    const merge = isMergeMode();
    document.getElementById("subtract-extras").classList.toggle("hidden", merge);
    document.getElementById("merge-extras").classList.toggle("hidden", !merge);
    document.getElementById("lbl-chk-result").textContent = merge
      ? "Объединённый ряд"
      : "Результат вычитания";
    document.getElementById("chart-hint").textContent = merge
      ? "По умолчанию — одна кривая: только объединённый ряд."
      : "По умолчанию — одна кривая: только результат вычитания. Крупные разности: зелёные полосы (результат > 0), красные (< 0), порог ниже.";
    document.getElementById("lbl-file-a-hint").textContent = merge
      ? "(первый набор)"
      : "(уменьшаемое при A − B)";
    document.getElementById("lbl-file-b-hint").textContent = merge
      ? "(второй набор)"
      : "(вычитаемое при A − B)";
    document.getElementById("compute").textContent = merge
      ? "Объединить и построить график"
      : "Посчитать и построить график";
  }

  function renderList() {
    const ul = document.getElementById("file-list");
    ul.innerHTML = "";

    if (library.length === 0) {
      const note = document.getElementById("file-add-note");
      if (note) {
        note.textContent = "";
      }
      const li = document.createElement("li");
      li.style.border = "none";
      li.style.color = "var(--muted)";
      li.textContent = "Нет загруженных файлов";
      ul.appendChild(li);
      return;
    }

    library.forEach((item) => {
      const li = document.createElement("li");
      const left = document.createElement("span");
      left.textContent = item.file.name;
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = fmtSize(item.file.size);
      const wrap = document.createElement("span");
      wrap.appendChild(left);
      wrap.appendChild(document.createTextNode(" "));
      wrap.appendChild(meta);

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "rm";
      removeButton.textContent = "Убрать";
      removeButton.addEventListener("click", () => {
        library = library.filter((entry) => entry.id !== item.id);
        renderList();
        syncSelects();
        updateButtons();
      });

      li.appendChild(wrap);
      li.appendChild(removeButton);
      ul.appendChild(li);
    });
  }

  function syncSelects() {
    const selectA = document.getElementById("sel-a");
    const selectB = document.getElementById("sel-b");
    const prevA = selectA.value;
    const prevB = selectB.value;

    selectA.innerHTML = "";
    selectB.innerHTML = "";

    const emptyA = document.createElement("option");
    emptyA.value = "";
    emptyA.textContent = "— выберите —";
    selectA.appendChild(emptyA);

    const emptyB = document.createElement("option");
    emptyB.value = "";
    emptyB.textContent = "— выберите —";
    selectB.appendChild(emptyB);

    library.forEach((item) => {
      const optionA = document.createElement("option");
      optionA.value = item.id;
      optionA.textContent = item.file.name;
      selectA.appendChild(optionA);

      const optionB = document.createElement("option");
      optionB.value = item.id;
      optionB.textContent = item.file.name;
      selectB.appendChild(optionB);
    });

    if (prevA && library.some((item) => item.id === prevA)) {
      selectA.value = prevA;
    } else if (library[0]) {
      selectA.value = library[0].id;
    }

    if (prevB && library.some((item) => item.id === prevB)) {
      selectB.value = prevB;
    } else if (library[1]) {
      selectB.value = library[1].id;
    } else if (library.length === 1) {
      selectB.value = "";
    }
  }

  function addFiles(fileList) {
    const items = Array.isArray(fileList) ? fileList.slice() : Array.from(fileList || []);
    if (items.length === 0) {
      return;
    }

    items.forEach((file) => {
      fileIdSeq += 1;
      const id = "f-" + fileIdSeq + "-" + Math.random().toString(36).slice(2, 11);
      library.push({ id: id, file: file });
    });

    const note = document.getElementById("file-add-note");
    if (note) {
      note.textContent = "Добавлено: " + items.length + " файл(ов). Всего в списке: " + library.length + ".";
    }

    renderList();
    syncSelects();
    setMessage("");
    lastResultCsv = "";
    lastDownloadFilename = "result.csv";
    updateButtons();
  }

  function buildFormData(itemA, itemB) {
    const fd = new FormData();
    fd.append("file_a", itemA.file, itemA.file.name);
    fd.append("file_b", itemB.file, itemB.file.name);
    fd.append("show_a", document.getElementById("chk-a").checked ? "true" : "false");
    fd.append("show_b", document.getElementById("chk-b").checked ? "true" : "false");
    fd.append("show_result", document.getElementById("chk-result").checked ? "true" : "false");

    if (isMergeMode()) {
      fd.append("duplicate_policy", document.getElementById("dup-policy").value);
    } else {
      fd.append("operation", document.querySelector('input[name="op"]:checked').value);
      fd.append("highlight_threshold", document.getElementById("highlight-threshold").value || "0");
    }

    return fd;
  }

  function buildSuccessMessage(data) {
    let detail = "";
    let extra = "";

    if (data.mode === "merge") {
      detail =
        "<strong>Объединение.</strong> " +
        (data.operation_label || "") +
        ". Точек в объединённом ряду: <strong>" +
        data.merged_points +
        "</strong> (A: <strong>" +
        data.points_a +
        "</strong>, B: <strong>" +
        data.points_b +
        "</strong>). Совпавших по freq: <strong>" +
        data.duplicate_freqs +
        "</strong>.";
      extra =
        data.only_in_a > 0 || data.only_in_b > 0
          ? " Только в A: <strong>" +
            data.only_in_a +
            "</strong>, только в B: <strong>" +
            data.only_in_b +
            "</strong>."
          : "";
    } else {
      detail =
        "Операция: <strong>" +
        (data.operation_label || "") +
        "</strong>. Точек A: <strong>" +
        data.points_a +
        "</strong>, B: <strong>" +
        data.points_b +
        "</strong>. Совпало по freq: <strong>" +
        data.matched +
        "</strong>.";
      if (data.highlight_threshold > 0) {
        const positive = data.highlight_bands_positive ?? 0;
        const negative = data.highlight_bands_negative ?? 0;
        detail +=
          " Подсветка при |разность| ≥ <strong>" +
          data.highlight_threshold +
          "</strong> дБ: полос всего <strong>" +
          (data.highlight_bands ?? positive + negative) +
          "</strong> " +
          '(<span style="color:#34d399;">+</span> <strong>' +
          positive +
          '</strong>, <span style="color:#f87171;">−</span> <strong>' +
          negative +
          "</strong>).";
      } else {
        detail += " Подсветка выключена (порог 0).";
      }
      extra =
        data.only_in_a > 0 || data.only_in_b > 0
          ? " Только в A: <strong>" +
            data.only_in_a +
            "</strong>, только в B: <strong>" +
            data.only_in_b +
            "</strong>."
          : "";
    }

    let plotNote = "";
    if (data.plot_decimated) {
      plotNote =
        " <strong>График упрощён</strong> для скорости (до ~" +
        (data.plot_trace_points ?? "?") +
        " точек на кривую, лимит <strong>" +
        (data.plot_max_points ?? "?") +
        "</strong>). В CSV — все точки.";
    }

    return detail + extra + plotNote;
  }

  async function handleCompute() {
    const idA = document.getElementById("sel-a").value;
    const idB = document.getElementById("sel-b").value;
    const itemA = library.find((item) => item.id === idA);
    const itemB = library.find((item) => item.id === idB);
    if (!itemA || !itemB || idA === idB) {
      return;
    }

    const merge = isMergeMode();
    const formData = buildFormData(itemA, itemB);

    setMessage(merge ? "Объединение…" : "Загрузка и расчёт…", "ok");
    document.getElementById("compute").disabled = true;

    try {
      const result = merge
        ? await EMS.requestMerge(formData)
        : await EMS.requestAnalyze(formData);

      if (!result.ok) {
        lastResultCsv = "";
        lastDownloadFilename = "result.csv";
        setMessage(result.error, "");
        if (typeof EMS.purgeChart === "function") {
          EMS.purgeChart();
        }
        updateButtons();
        return;
      }

      const data = result.data;
      lastResultCsv = data.result_csv || "";
      lastDownloadFilename = data.mode === "merge" ? "merged.csv" : "result.csv";
      setMessage(buildSuccessMessage(data), "ok");

      if (data.figure) {
        await EMS.renderFigure(data.figure);
      }
    } catch (error) {
      lastResultCsv = "";
      lastDownloadFilename = "result.csv";
      setMessage(String(error.message || error), "");
      if (typeof EMS.purgeChart === "function") {
        EMS.purgeChart();
      }
    } finally {
      updateButtons();
    }
  }

  function initFileDrop() {
    const multiDrop = document.getElementById("multi-drop");
    const multiInput = document.getElementById("multi-input");
    multiInput.multiple = true;

    multiDrop.addEventListener("click", () => multiInput.click());
    multiDrop.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        multiInput.click();
      }
    });
    multiInput.addEventListener("click", (event) => event.stopPropagation());
    multiInput.addEventListener("change", () => {
      addFiles(Array.from(multiInput.files || []));
      multiInput.value = "";
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      multiDrop.addEventListener(eventName, (event) => {
        event.preventDefault();
        event.stopPropagation();
        multiDrop.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      multiDrop.addEventListener(eventName, (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (eventName === "dragleave" && !multiDrop.contains(event.relatedTarget)) {
          multiDrop.classList.remove("dragover");
        }
        if (eventName === "drop") {
          multiDrop.classList.remove("dragover");
        }
      });
    });

    multiDrop.addEventListener("drop", (event) => {
      const dt = event.dataTransfer;
      if (!dt || !dt.files) {
        return;
      }
      addFiles(Array.from(dt.files));
    });
  }

  function initProtocolWarning() {
    if (window.location.protocol !== "file:") {
      return;
    }
    const warning = document.getElementById("file-protocol-warn");
    warning.style.display = "block";
    warning.className = "msg";
    warning.innerHTML =
      "Страница открыта как <strong>файл</strong> — запросы к API не работают. Запустите <code>python run.py</code> и откройте <code>http://127.0.0.1:8000</code>.";
  }

  function initDownloads() {
    document.getElementById("download").addEventListener("click", () => {
      if (!lastResultCsv) {
        return;
      }
      EMS.downloadCsv(lastResultCsv, lastDownloadFilename);
    });

    document.getElementById("download-html").addEventListener("click", () => {
      const ok = EMS.downloadChartHtml();
      if (!ok) {
        setMessage("Сначала постройте график.", "");
      }
    });
  }

  function initApp() {
    initProtocolWarning();
    EMS.initThemeControls();
    initFileDrop();
    initDownloads();

    document.getElementById("sel-a").addEventListener("change", updateButtons);
    document.getElementById("sel-b").addEventListener("change", updateButtons);
    document.querySelectorAll('input[name="work_mode"]').forEach((el) => {
      el.addEventListener("change", () => {
        syncModeUI();
        updateButtons();
      });
    });
    document.getElementById("compute").addEventListener("click", handleCompute);

    renderList();
    syncSelects();
    syncModeUI();
    updateButtons();
  }

  window.addEventListener("DOMContentLoaded", initApp);
})();
