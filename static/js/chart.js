(function () {
  const EMS = (window.EMS = window.EMS || {});

  function chartElement() {
    return document.getElementById("chart");
  }

  function chartHasData() {
    if (typeof Plotly === "undefined") {
      return false;
    }
    const gd = chartElement();
    return !!(gd && gd.data && gd.data.length);
  }

  function purgeChart() {
    if (typeof Plotly === "undefined") {
      return;
    }
    const gd = chartElement();
    if (gd) {
      Plotly.purge(gd);
    }
  }

  async function renderFigure(figure) {
    if (typeof Plotly === "undefined") {
      throw new Error("Не загрузилась библиотека Plotly (CDN).");
    }
    const gd = chartElement();
    await Plotly.newPlot(gd, figure.data, figure.layout, {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
    });
    if (typeof EMS.applyPlotlyChartTheme === "function") {
      EMS.applyPlotlyChartTheme();
    }
  }

  EMS.chartHasData = chartHasData;
  EMS.purgeChart = purgeChart;
  EMS.renderFigure = renderFigure;
})();
