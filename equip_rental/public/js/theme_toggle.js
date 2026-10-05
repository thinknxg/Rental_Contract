(function () {
  const ORDER = ["light", "dark", "automatic"];
  const LABEL = { light: "Light", dark: "Dark", automatic: "Automatic" };
  const ICON = { light: "☀", dark: "☾", automatic: "◐" };
  const root = document.documentElement;

  function currentMode() {
    const m = (root.getAttribute("data-theme-mode") || "automatic").toLowerCase();
    return ORDER.includes(m) ? m : "automatic";
  }

  function applyMode(mode) {
    const dark =
      mode === "dark" ||
      (mode === "automatic" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    root.setAttribute("data-theme-mode", mode);
    root.setAttribute("data-theme", dark ? "dark" : "light");
  }

  function paint(btn) {
    const mode = currentMode();
    btn.attr("title", "Theme: " + LABEL[mode] + " (click to change)");
    btn.find(".er-theme-icon").text(ICON[mode]);
  }

  function cycle(btn) {
    const next = ORDER[(ORDER.indexOf(currentMode()) + 1) % ORDER.length];
    applyMode(next);
    paint(btn);
    frappe.call({
      method: "frappe.core.doctype.user.user.switch_theme",
      args: { theme: LABEL[next] },
    });
  }

  function build() {
    return $(
      '<li class="nav-item" id="er-theme-toggle">' +
        '<a class="nav-link er-theme-btn" href="#" role="button">' +
        '<span class="er-theme-icon"></span></a></li>'
    );
  }

  function wire(btn) {
    btn.find("a").on("click", function (e) {
      e.preventDefault();
      cycle(btn);
    });
    paint(btn);
  }

  function mountInNavbar() {
    if (document.getElementById("er-theme-toggle")) return true;
    const notif = $(".navbar .dropdown-notifications").first();
    const nav = $(".navbar .navbar-nav").last();
    if (!notif.length && !nav.length) return false;
    const btn = build();
    if (notif.length) notif.before(btn);
    else nav.prepend(btn);
    wire(btn);
    return true;
  }

  function mountFloating() {
    if (document.getElementById("er-theme-toggle")) return;
    const btn = $(
      '<div id="er-theme-toggle" style="position:fixed;top:10px;right:80px;z-index:2000;' +
        'background:var(--card-bg);border:1px solid var(--border-color);border-radius:8px;">' +
        '<a class="er-theme-btn" href="#" role="button"><span class="er-theme-icon"></span></a></div>'
    );
    $("body").append(btn);
    wire(btn);
  }

  function start() {
    if (window.frappe && frappe.session && frappe.session.user === "Guest") return;
    let tries = 0;
    const timer = setInterval(function () {
      tries += 1;
      if (mountInNavbar()) return clearInterval(timer);
      if (tries > 40) {
        clearInterval(timer);
        mountFloating();
      }
    }, 500);
  }

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", function () {
      if (currentMode() === "automatic") applyMode("automatic");
    });

  $(document).ready(start);
})();
