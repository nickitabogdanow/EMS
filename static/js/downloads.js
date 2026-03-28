(function () {
  const EMS = (window.EMS = window.EMS || {});

  function downloadTextFile(content, type, filename) {
    const blob = new Blob([content], { type: type });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function downloadCsv(content, filename) {
    downloadTextFile(content, "text/csv;charset=utf-8", filename);
  }

  function formatDownloadError(detail) {
    if (detail == null) {
      return "Не удалось скачать CSV.";
    }
    if (typeof detail === "string") {
      return detail;
    }
    return String(detail);
  }

  async function downloadCsvFromUrl(url, fallbackFilename) {
    const response = await fetch(url, { method: "GET" });
    const contentType = response.headers.get("content-type") || "";

    if (!response.ok) {
      if (contentType.includes("application/json")) {
        const payload = await response.json();
        throw new Error(formatDownloadError(payload.detail));
      }
      throw new Error(formatDownloadError(await response.text()));
    }

    const blob = await response.blob();
    const header = response.headers.get("content-disposition") || "";
    const match = /filename="([^"]+)"/.exec(header);
    const filename = match ? match[1] : fallbackFilename;

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function standaloneChartHtml(figure) {
    let payload = JSON.stringify(figure);
    payload = payload.replace(/</g, "\\u003c");

    const theme = typeof EMS.getTheme === "function" ? EMS.getTheme() : "dark";
    const pageBg =
      theme === "light"
        ? "#f8fafc"
        : theme === "barbie"
          ? "#fdf2f8"
          : theme === "unicorn"
            ? "#ede9fe"
            : "#0f1419";

    return (
      "<!DOCTYPE html>\n" +
      '<html lang="ru">\n<head>\n<meta charset="utf-8"/>\n' +
      '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n<title>График</title>\n' +
      '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"><\/script>\n' +
      "<style>html,body{margin:0;height:100%;background:" +
      pageBg +
      ";}#chart{width:100%;height:100vh;}</style>\n</head>\n<body>\n" +
      '<div id="chart"></div>\n<script type="application/json" id="fig">' +
      payload +
      "<\/script>\n<script>\n" +
      '(function(){var el=document.getElementById("fig");var fig=JSON.parse(el.textContent);el.remove();Plotly.newPlot("chart",fig.data,fig.layout,{responsive:true,displayModeBar:true,displaylogo:false});})();\n' +
      "<\/script>\n</body>\n</html>"
    );
  }

  function downloadChartHtml() {
    const gd = document.getElementById("chart");
    if (!gd || !gd.data || !gd.data.length) {
      return false;
    }
    const html = standaloneChartHtml({ data: gd.data, layout: gd.layout });
    downloadTextFile(html, "text/html;charset=utf-8", "chart.html");
    return true;
  }

  EMS.downloadCsv = downloadCsv;
  EMS.downloadCsvFromUrl = downloadCsvFromUrl;
  EMS.downloadChartHtml = downloadChartHtml;
})();
