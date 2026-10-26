/* 硅基花园 · 皮肤层脚本：只做一件事——夜 / 纸 两种底色。
   不读取、不修改、不重排任何正文。选择只存在访客自己的浏览器里。 */
(function () {
  var KEY = "sg-theme";
  var root = document.documentElement;

  function current() {
    try { return localStorage.getItem(KEY) || "night"; } catch (e) { return "night"; }
  }
  function apply(theme) {
    if (theme === "paper") { root.setAttribute("data-theme", "paper"); }
    else { root.removeAttribute("data-theme"); }
    var btns = document.querySelectorAll(".sg-theme button");
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute("aria-pressed", String(btns[i].dataset.theme === theme));
    }
  }

  apply(current()); //  head 内同步执行，避免页面先深后浅地闪一下

  document.addEventListener("DOMContentLoaded", function () {
    if (!document.querySelector("article")) return; // 只有长文页需要切换
    if (document.querySelector(".sg-theme")) return;

    var box = document.createElement("div");
    box.className = "sg-theme";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "阅读底色");

    [["night", "夜"], ["paper", "纸"]].forEach(function (pair) {
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.theme = pair[0];
      b.textContent = pair[1];
      b.addEventListener("click", function () {
        try { localStorage.setItem(KEY, pair[0]); } catch (e) {}
        apply(pair[0]);
      });
      box.appendChild(b);
    });

    document.body.appendChild(box);
    apply(current());
  });
})();
