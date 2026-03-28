(function () {
  const EMS = (window.EMS = window.EMS || {});
  const THEME_KEY = "ems_theme";

  function getTheme() {
    const active = document.documentElement.getAttribute("data-theme");
    if (active === "light" || active === "barbie" || active === "unicorn") {
      return active;
    }
    return "dark";
  }

  function plotlyColorsForTheme(theme) {
    if (theme === "light") {
      return { paper: "#ffffff", plot: "#f8fafc", grid: "#e2e8f0", font: "#1a2332" };
    }
    if (theme === "barbie") {
      return { paper: "#fff5fb", plot: "#ffffff", grid: "#f9a8d4", font: "#9d174d" };
    }
    if (theme === "unicorn") {
      return { paper: "rgba(255,250,255,0.97)", plot: "#faf5ff", grid: "#d8b4fe", font: "#5b21b6" };
    }
    return { paper: "#0f1419", plot: "#1a2332", grid: "#2d3a4d", font: "#e7ecf3" };
  }

  function syncThemeSelect() {
    const select = document.getElementById("theme-select");
    if (select) {
      select.value = getTheme();
    }
  }

  function applyPlotlyChartTheme() {
    if (typeof Plotly === "undefined") {
      return;
    }
    const gd = document.getElementById("chart");
    if (!gd || !gd.layout) {
      return;
    }
    const colors = plotlyColorsForTheme(getTheme());
    Plotly.relayout(gd, {
      paper_bgcolor: colors.paper,
      plot_bgcolor: colors.plot,
      font: Object.assign({}, gd.layout.font || {}, {
        color: colors.font,
        family: "system-ui, sans-serif",
      }),
      xaxis: Object.assign({}, gd.layout.xaxis || {}, { gridcolor: colors.grid, zeroline: false }),
      yaxis: Object.assign({}, gd.layout.yaxis || {}, { gridcolor: colors.grid, zeroline: false }),
    });
  }

  function setTheme(name) {
    const nextTheme =
      name === "light" || name === "barbie" || name === "unicorn" ? name : "dark";
    if (nextTheme === "dark") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", nextTheme);
    }
    try {
      localStorage.setItem(THEME_KEY, nextTheme);
    } catch (error) {}
    syncThemeSelect();
    applyPlotlyChartTheme();
  }

  function initThemeControls() {
    const select = document.getElementById("theme-select");
    if (!select) {
      return;
    }
    select.addEventListener("change", function () {
      setTheme(this.value);
    });
    syncThemeSelect();
  }

  EMS.getTheme = getTheme;
  EMS.plotlyColorsForTheme = plotlyColorsForTheme;
  EMS.syncThemeSelect = syncThemeSelect;
  EMS.applyPlotlyChartTheme = applyPlotlyChartTheme;
  EMS.setTheme = setTheme;
  EMS.initThemeControls = initThemeControls;
})();
