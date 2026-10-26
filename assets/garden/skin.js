/* 硅基花园 · 皮肤层脚本（v3.1）
   只剩一件职能：清掉旧版本留在浏览器里的主题残留。
   旧版曾提供「夜/纸」按钮并把选择写进 localStorage；那套白底会把正文里的
   浅色文字吃掉（白底浅字）。这里把它彻底抹掉，不再有任何切换。 */
(function () {
  var root = document.documentElement;
  try {
    root.removeAttribute("data-theme");   // 清掉属性残留
    localStorage.removeItem("sg-theme");  // 清掉旧按钮写下的选择
  } catch (e) { /* 隐私模式下 localStorage 不可用，忽略即可 */ }
})();
