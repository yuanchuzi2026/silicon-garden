/* 硅基花园 · 大门空间（front.js）
   只做一件事：在大门页生成一串线框立方体，沿中轴排到透视深处。
   纯装饰，aria-hidden，不进内容层，不碰任何文字。 */
(function () {
  function build() {
    var gate = document.querySelector(".gate");
    if (!gate || document.querySelector(".tunnel")) return;
    // 尊重系统"减少动态效果"设置：不开就不要造这一层
    try {
      if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    } catch (e) {}

    var box = document.createElement("div");
    box.className = "tunnel";
    box.setAttribute("aria-hidden", "true");

    var N = 16;
    for (var i = 0; i < N; i++) {
      var c = document.createElement("i");
      c.className = "cube";
      // 相位：让它们在整个循环里均匀分布
      c.style.animationDelay = (-(i * 9) / N).toFixed(3) + "s";
      // 轻微倾斜，各自不同，才像悬浮而不是排队
      c.style.setProperty("--r", (((i % 5) - 2) * 0.9).toFixed(2) + "deg");
      c.style.setProperty("--s", (1 + ((i % 3) - 1) * 0.12).toFixed(2));
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
