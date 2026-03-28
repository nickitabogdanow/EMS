(function () {
  const EMS = (window.EMS = window.EMS || {});

  function formatApiError(detail) {
    if (detail == null) {
      return "Ошибка сервера";
    }
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => (item && item.msg) || JSON.stringify(item)).join(" ");
    }
    return String(detail);
  }

  async function postForm(url, formData) {
    const response = await fetch(url, { method: "POST", body: formData });
    const raw = await response.text();
    let data = {};

    try {
      data = raw ? JSON.parse(raw) : {};
    } catch (error) {
      return {
        ok: false,
        nonJson: true,
        data: {},
        error: "Ответ сервера не JSON (откройте страницу с <code>http://127.0.0.1:8000</code>).",
      };
    }

    if (!response.ok) {
      return {
        ok: false,
        nonJson: false,
        data: data,
        error: formatApiError(data.detail),
      };
    }

    return { ok: true, nonJson: false, data: data, error: "" };
  }

  function requestAnalyze(formData) {
    return postForm("/api/analyze", formData);
  }

  function requestMerge(formData) {
    return postForm("/api/merge", formData);
  }

  EMS.formatApiError = formatApiError;
  EMS.requestAnalyze = requestAnalyze;
  EMS.requestMerge = requestMerge;
})();
