// 移动端优化
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
if (isMobile) {
    document.documentElement.style.setProperty('--animation-speed', '40s');
    const heptagram = document.getElementById('heptagram-canvas');
    if (heptagram) heptagram.style.opacity = '0.06';
}