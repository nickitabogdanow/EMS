(function () {
  const EMS = (window.EMS = window.EMS || {});
  const THEME_KEY = "ems_theme";
  const UNLOCK_KEY = "ems_theme_unlock_level";
  const LEVEL1_CLICK_WINDOW_MS = 2200;
  const LEVEL2_CLICK_WINDOW_MS = 2200;
  const LEVEL1_CLICK_COUNT = 5;
  const LEVEL2_CLICK_COUNT = 5;
  const THEMES = [
    { id: "light", level: 0 },
    { id: "barbie", level: 1 },
    { id: "unicorn", level: 1 },
    { id: "synthwave", level: 2 },
    { id: "space", level: 2 },
    { id: "ocean", level: 2 },
    { id: "forest", level: 2 },
    { id: "sunset", level: 2 },
    { id: "cyberpunk", level: 2 },
    { id: "candy", level: 2 },
    { id: "kitty", level: 2 },
    { id: "pixel", level: 2 },
    { id: "matrix", level: 2 },
    { id: "lava", level: 2 },
    { id: "ice", level: 2 },
    { id: "galaxy-pop", level: 2 },
    { id: "sakura", level: 2 },
    { id: "vaporwave", level: 2 },
  ];
  const PLOTLY_THEME_COLORS = {
    light: { paper: "#ffffff", plot: "#f8fafc", grid: "#e2e8f0", font: "#1a2332" },
    barbie: { paper: "#fff5fb", plot: "#ffffff", grid: "#f9a8d4", font: "#9d174d" },
    unicorn: { paper: "rgba(255,250,255,0.97)", plot: "#faf5ff", grid: "#d8b4fe", font: "#5b21b6" },
    synthwave: { paper: "#170f2e", plot: "#22143f", grid: "#ff63c3", font: "#f8c7ff" },
    space: { paper: "#0a1022", plot: "#111a33", grid: "#334a7d", font: "#dbeafe" },
    ocean: { paper: "#e6fffb", plot: "#f0fdfa", grid: "#7dd3c7", font: "#115e59" },
    forest: { paper: "#102218", plot: "#153023", grid: "#3f7d58", font: "#d1fae5" },
    sunset: { paper: "#fff3e8", plot: "#fff7ed", grid: "#fdba74", font: "#9a3412" },
    cyberpunk: { paper: "#0a0b17", plot: "#12142a", grid: "#22d3ee", font: "#f5d0fe" },
    candy: { paper: "#fffaf7", plot: "#ffffff", grid: "#f9a8d4", font: "#9d174d" },
    kitty: { paper: "#fff7fb", plot: "#ffffff", grid: "#fbcfe8", font: "#9d174d" },
    pixel: { paper: "#1b1c34", plot: "#24264a", grid: "#6b7280", font: "#fef08a" },
    matrix: { paper: "#030b06", plot: "#07150c", grid: "#14532d", font: "#86efac" },
    lava: { paper: "#1b100d", plot: "#271612", grid: "#f97316", font: "#ffedd5" },
    ice: { paper: "#effaff", plot: "#f8fdff", grid: "#93c5fd", font: "#1d4ed8" },
    "galaxy-pop": { paper: "#150f28", plot: "#21163b", grid: "#c084fc", font: "#fde68a" },
    sakura: { paper: "#fff8fb", plot: "#ffffff", grid: "#f9a8d4", font: "#9f1239" },
    vaporwave: { paper: "#fff1fb", plot: "#fff7fd", grid: "#67e8f9", font: "#7c3aed" },
  };
  let level1ClickCount = 0;
  let level1ClickTimer = 0;
  let level2ClickCount = 0;
  let level2ClickTimer = 0;

  function availableThemeIds() {
    return THEMES.map((item) => item.id);
  }

  function getUnlockLevel() {
    try {
      const raw = parseInt(localStorage.getItem(UNLOCK_KEY) || "0", 10);
      if (raw === 1 || raw === 2) {
        return raw;
      }
    } catch (error) {}
    return 0;
  }

  function setUnlockLevel(level) {
    const nextLevel = level >= 2 ? 2 : level >= 1 ? 1 : 0;
    try {
      localStorage.setItem(UNLOCK_KEY, String(nextLevel));
    } catch (error) {}
    return nextLevel;
  }

  function isThemeUnlocked(themeId) {
    if (themeId === "dark") {
      return true;
    }
    const theme = THEMES.find((item) => item.id === themeId);
    if (!theme) {
      return false;
    }
    return theme.level <= getUnlockLevel();
  }

  function getTheme() {
    const active = document.documentElement.getAttribute("data-theme");
    if (availableThemeIds().includes(active) && isThemeUnlocked(active)) {
      return active;
    }
    return "dark";
  }

  function plotlyColorsForTheme(theme) {
    if (PLOTLY_THEME_COLORS[theme]) {
      return PLOTLY_THEME_COLORS[theme];
    }
    return { paper: "#0f1419", plot: "#1a2332", grid: "#2d3a4d", font: "#e7ecf3" };
  }

  function syncThemeSelect() {
    const select = document.getElementById("theme-select");
    const unlockLevel = getUnlockLevel();
    if (select) {
      Array.from(select.options).forEach((option) => {
        const requiredLevel = parseInt(option.getAttribute("data-theme-level") || "0", 10);
        const visible = requiredLevel <= unlockLevel;
        option.hidden = !visible;
        option.disabled = !visible;
      });
      select.value = getTheme();
    }
    const resetButton = document.getElementById("theme-reset-secrets");
    if (resetButton) {
      resetButton.classList.toggle("hidden", unlockLevel === 0);
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
    const nextTheme = name === "dark" || isThemeUnlocked(name) ? name : "dark";
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

  function triggerThemePickerCelebration() {
    const picker = document.querySelector(".theme-picker");
    if (!picker) {
      return;
    }
    picker.classList.remove("celebrate");
    void picker.offsetWidth;
    picker.classList.add("celebrate");
    window.setTimeout(() => {
      picker.classList.remove("celebrate");
    }, 900);
  }

  function announceUnlock(level) {
    triggerThemePickerCelebration();
    window.dispatchEvent(
      new CustomEvent("ems:themes-unlocked", {
        detail: { level: level },
      })
    );
  }

  function announceReset(previousLevel) {
    window.dispatchEvent(
      new CustomEvent("ems:themes-reset", {
        detail: { previousLevel: previousLevel },
      })
    );
  }

  function unlockLevel(level) {
    if (getUnlockLevel() >= level) {
      return;
    }
    setUnlockLevel(level);
    syncThemeSelect();
    announceUnlock(level);
  }

  function resetThemeSecrets() {
    const previousLevel = getUnlockLevel();
    if (previousLevel === 0) {
      return;
    }
    setUnlockLevel(0);
    level1ClickCount = 0;
    level2ClickCount = 0;
    if (getTheme() !== "dark" && !isThemeUnlocked(getTheme())) {
      setTheme("dark");
    } else {
      syncThemeSelect();
    }
    announceReset(previousLevel);
  }

  function registerLevel1SecretClick() {
    level1ClickCount += 1;
    if (level1ClickTimer) {
      window.clearTimeout(level1ClickTimer);
    }
    level1ClickTimer = window.setTimeout(() => {
      level1ClickCount = 0;
      level1ClickTimer = 0;
    }, LEVEL1_CLICK_WINDOW_MS);
    if (level1ClickCount >= LEVEL1_CLICK_COUNT) {
      level1ClickCount = 0;
      unlockLevel(1);
    }
  }

  function registerLevel2SecretClick() {
    if (getUnlockLevel() < 1) {
      return;
    }
    level2ClickCount += 1;
    if (level2ClickTimer) {
      window.clearTimeout(level2ClickTimer);
    }
    level2ClickTimer = window.setTimeout(() => {
      level2ClickCount = 0;
      level2ClickTimer = 0;
    }, LEVEL2_CLICK_WINDOW_MS);
    if (level2ClickCount >= LEVEL2_CLICK_COUNT) {
      level2ClickCount = 0;
      unlockLevel(2);
    }
  }

  function initThemeControls() {
    const select = document.getElementById("theme-select");
    if (!select) {
      return;
    }
    select.addEventListener("change", function () {
      setTheme(this.value);
    });
    const title = document.querySelector(".page-head .lead h1");
    if (title) {
      title.addEventListener("click", registerLevel1SecretClick);
    }
    const themeLabel = document.querySelector(".theme-picker-label");
    if (themeLabel) {
      themeLabel.addEventListener("click", registerLevel2SecretClick);
    }
    const resetButton = document.getElementById("theme-reset-secrets");
    if (resetButton) {
      resetButton.addEventListener("click", resetThemeSecrets);
    }
    syncThemeSelect();
  }

  EMS.getTheme = getTheme;
  EMS.getUnlockLevel = getUnlockLevel;
  EMS.isThemeUnlocked = isThemeUnlocked;
  EMS.resetThemeSecrets = resetThemeSecrets;
  EMS.themes = THEMES.map((item) => item.id);
  EMS.plotlyColorsForTheme = plotlyColorsForTheme;
  EMS.syncThemeSelect = syncThemeSelect;
  EMS.applyPlotlyChartTheme = applyPlotlyChartTheme;
  EMS.setTheme = setTheme;
  EMS.initThemeControls = initThemeControls;
})();
