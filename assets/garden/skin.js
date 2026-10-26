/* 硅基花园 · 皮肤层脚本（v3）
   默认只有一个方向：纯黑底、白字、白光。
   不做「暗/亮」按钮——因为各页的内联样式里有一批硬编码的亮色强调字，
   换成白底之后它们会变成白字白底，用变量覆盖不回来。
   与其给一个点下去会坏一半的开关，不如不给。

   仍然保留手动入口：在地址后加 ?theme=paper 可切到白底黑字（仅用于自查那一版）。
   选择只存在浏览器本地，不上传、不回传。 */
(function () {
  var root = document.documentElement;
  try {
    var q = location.search;
    if (q.indexOf("theme=paper") > -1) { root.setAttribute("data-theme", "paper"); }
    else if (q.indexOf("theme=dark") > -1) { root.removeAttribute("data-theme"); }
  } catch (e) {}
})();
