(function () {
  var KEY = "er_portal_theme";
  var ORDER = ["light", "dark", "system"];
  var ICON = { light: "\u2600", dark: "\u263E", system: "\u25D0" };
  var LABEL = { light: "Light", dark: "Dark", system: "System" };
  var root = document.documentElement;

  function saved() {
    try {
      var m = localStorage.getItem(KEY);
      return ORDER.indexOf(m) > -1 ? m : "system";
    } catch (e) {
      return "system";
    }
  }

  function apply(mode) {
    if (mode === "system") {
      root.removeAttribute("data-theme");
      root.style.colorScheme = "";
    } else {
      root.setAttribute("data-theme", mode);
      root.style.colorScheme = mode;
    }
  }

  var mode = saved();
  apply(mode);

  function mount() {
    if (document.getElementById("er-portal-theme")) return;
    var btn = document.createElement("button");
    btn.id = "er-portal-theme";
    btn.type = "button";
    btn.className = "er-portal-theme";
    function paint() {
      btn.textContent = ICON[mode];
      btn.title = "Theme: " + LABEL[mode] + " (click to change)";
      btn.setAttribute("aria-label", btn.title);
    }
    btn.addEventListener("click", function () {
      mode = ORDER[(ORDER.indexOf(mode) + 1) % ORDER.length];
      try { localStorage.setItem(KEY, mode); } catch (e) {}
      apply(mode);
      paint();
    });
    paint();
    document.body.appendChild(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
