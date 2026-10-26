/* 硅基花园 · 大门空间（front.js）
   一个立体网格盒子：六个面都是格子，从远处放大、迎面盖过来、穿过去，循环。
   纯装饰，aria-hidden，不进内容层，不碰任何文字。 */
(function () {
  function build() {
    var gate = document.querySelector(".gate");
    if (!gate || document.querySelector(".tunnel")) return;
    try {
      if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    } catch (e) {}

    var box = document.createElement("div");
    box.className = "tunnel";
    box.setAttribute("aria-hidden", "true");

    var N = 6;
    var faces = ["f", "b", "l", "r", "t", "d"];
    for (var i = 0; i < N; i++) {
      var c = document.createElement("div");
      c.className = "cube3d";
      c.style.animationDelay = (-(i * 9) / N).toFixed(3) + "s";
      // 轻微偏移，避免六个盒子完全重叠成一团
      c.style.setProperty("--dx", ((i % 3) - 1) * 1.4 + "%");
      c.style.setProperty("--dy", (((i + 1) % 3) - 1) * 1.1 + "%");
      faces.forEach(function (k) {
        var f = document.createElement("div");
        f.className = "face " + k;
        c.appendChild(f);
      });
      box.appendChild(c);
    }
    document.body.insertBefore(box, gate);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
