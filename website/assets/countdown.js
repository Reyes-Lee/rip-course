// 頂端公告列的期末專題倒數。截止時間寫在 overrides/main.html 的 data-deadline（台灣時間）。
(function () {
  function pad(n) { return String(n).padStart(2, "0"); }
  function put(el, unit, value) {
    var b = el.querySelector('[data-u="' + unit + '"]');
    if (b && b.textContent !== String(value)) b.textContent = value;
  }
  function tick() {
    document.querySelectorAll(".rip-countdown").forEach(function (el) {
      var end = Date.parse(el.dataset.deadline);
      if (isNaN(end)) return;
      var left = end - Date.now();
      if (left <= 0) {
        el.classList.add("is-over");
        var clock = el.querySelector(".rip-countdown__clock");
        if (clock) clock.textContent = "已截止";
        return;
      }
      var s = Math.floor(left / 1000);
      var d = Math.floor(s / 86400); s -= d * 86400;
      var h = Math.floor(s / 3600); s -= h * 3600;
      var m = Math.floor(s / 60); s -= m * 60;
      put(el, "d", d); put(el, "h", pad(h)); put(el, "m", pad(m)); put(el, "s", pad(s));
      el.classList.toggle("is-urgent", left < 3 * 86400000);
    });
  }
  tick();
  setInterval(tick, 1000);
  if (window.document$) window.document$.subscribe(tick);
})();
