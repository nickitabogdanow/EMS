(function () {
  const EMS = (window.EMS = window.EMS || {});

  function formatApiError(payload) {
    if (payload == null) {
      return "Ошибка сервера";
    }
    if (typeof payload === "string") {
      return payload;
    }
    if (payload.error && typeof payload.error.message === "string") {
      const requestId = payload.error.request_id || payload.request_id;
      return requestId
        ? payload.error.message + ' <span class="meta">(request id: ' + requestId + ")</span>"
        : payload.error.message;
    }
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item) => (item && item.msg) || JSON.stringify(item)).join(" ");
    }
    return String(payload);
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
        error: formatApiError(data),
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
