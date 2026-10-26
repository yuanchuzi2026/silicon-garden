/* 硅基花园 · 大门空间（front.js）
   生成一个装着人的空间：左右两面墙 + 一串线框立方体。
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

    // 左右两面墙（地板和天花板用的是页面原有的 .floor / .stars）
    ["left", "right"].forEach(function (side) {
      var w = document.createElement("div");
      w.className = "wall " + side;
      box.appendChild(w);
    });

    // 一串立方体：从深处浮出来，擦着人过去
    var N = 14;
    for (var i = 0; i < N; i++) {
      var c = document.createElement("i");
      c.className = "cube";
      c.style.animationDelay = (-(i * 10) / N).toFixed(3) + "s";
      c.style.setProperty("--r", (((i % 5) - 2) * 0.7).toFixed(2) + "deg");
      c.style.setProperty("--s", (1 + ((i % 3) - 1) * 0.08).toFixed(2));
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
