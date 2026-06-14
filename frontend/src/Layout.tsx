import { useEffect, useRef } from "react";
import { Outlet } from "react-router-dom";

/**
 * 深邃呼吸星空
 */
function DeepBreathingStars() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let anim: number;
    let time = 0;

    // 大星星（带光晕）
    const bigStars: { x: number; y: number; size: number; phase: number; speed: number; hue: number }[] = [];
    for (let i = 0; i < 25; i++) {
      bigStars.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: 1.5 + Math.random() * 3,
        phase: Math.random() * Math.PI * 2,
        speed: 0.002 + Math.random() * 0.006,
        hue: 200 + Math.random() * 60, // 蓝白到紫蓝
      });
    }

    // 小星星
    const smallStars: { x: number; y: number; size: number; phase: number; speed: number; hue: number }[] = [];
    for (let i = 0; i < 80; i++) {
      smallStars.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: 0.5 + Math.random() * 1.0,
        phase: Math.random() * Math.PI * 2,
        speed: 0.003 + Math.random() * 0.008,
        hue: 210 + Math.random() * 50,
      });
    }

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }

    resize();
    window.addEventListener("resize", resize);

    function draw() {
      if (!canvas || !ctx) return;
      const w = canvas.width;
      const h = canvas.height;
      time += 1;

      // — 深邃渐变深空 —
      // 上部深蓝紫 → 下部深暖棕
      for (let y = 0; y < h; y += 2) {
        const t = y / h;
        const r = 8 + t * 5;
        const g = 6 + t * 4;
        const b = 10 + t * 2;
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.fillRect(0, y, w, 2);
      }

      // — 呼吸星云光晕 —
      // 好几团微弱的大光晕，缓慢呼吸
      const nebulaPositions = [
        { x: w * 0.2, y: h * 0.3, hue: 220 },
        { x: w * 0.7, y: h * 0.6, hue: 260 },
        { x: w * 0.5, y: h * 0.2, hue: 200 },
        { x: w * 0.8, y: h * 0.4, hue: 240 },
      ];

      for (let ni = 0; ni < nebulaPositions.length; ni++) {
        const np = nebulaPositions[ni];
        const nb = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(time * 0.003 + ni * 1.5));
        const grad = ctx.createRadialGradient(np.x, np.y, 0, np.x, np.y, Math.min(w, h) * 0.35);
        grad.addColorStop(0, `hsla(${np.hue}, 30%, 50%, ${nb * 0.04})`);
        grad.addColorStop(0.5, `hsla(${np.hue}, 25%, 40%, ${nb * 0.02})`);
        grad.addColorStop(1, `hsla(${np.hue}, 20%, 30%, 0)`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }

      // — 大星星 —
      for (const star of bigStars) {
        const breathe = 0.5 + 0.5 * Math.sin(time * star.speed + star.phase);
        const core = 0.3 + 0.7 * breathe;
        const glow = 0.1 + 0.4 * breathe;

        // 光晕（外层）
        const grad = ctx.createRadialGradient(star.x, star.y, 0, star.x, star.y, star.size * 8);
        grad.addColorStop(0, `hsla(${star.hue}, 40%, 75%, ${glow * 0.3})`);
        grad.addColorStop(0.3, `hsla(${star.hue}, 35%, 65%, ${glow * 0.1})`);
        grad.addColorStop(1, `hsla(${star.hue}, 30%, 50%, 0)`);
        ctx.fillStyle = grad;
        ctx.fillRect(star.x - star.size * 8, star.y - star.size * 8, star.size * 16, star.size * 16);

        // 星核
        ctx.shadowBlur = star.size * 6;
        ctx.shadowColor = `hsla(${star.hue}, 50%, 80%, ${core * 0.5})`;
        ctx.fillStyle = `hsla(${star.hue}, 30%, 90%, ${core})`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size * core, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0;

      // — 小星星 —
      for (const star of smallStars) {
        const breathe = 0.5 + 0.5 * Math.sin(time * star.speed + star.phase);
        const alpha = 0.15 + 0.7 * breathe;
        ctx.fillStyle = `hsla(${star.hue}, 25%, 80%, ${alpha})`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
      }

      anim = requestAnimationFrame(draw);
    }

    anim = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(anim);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none z-0"
    />
  );
}

/**
 * 玻璃质感覆盖层
 */
function GlassOverlay() {
  return (
    <div
      className="fixed inset-0 w-full h-full pointer-events-none z-[1]"
      style={{
        background: `
          linear-gradient(
            135deg,
            rgba(200, 210, 255, 0.015) 0%,
            rgba(180, 190, 230, 0.008) 30%,
            rgba(160, 170, 200, 0.005) 50%,
            rgba(180, 190, 230, 0.008) 70%,
            rgba(200, 210, 255, 0.015) 100%
          )
        `,
        backdropFilter: "blur(1px)",
        WebkitBackdropFilter: "blur(1px)",
        // 轻微光泽条纹
        boxShadow: "inset 0 0 80px rgba(180, 200, 255, 0.02)",
      }}
    />
  );
}

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#0a0806] text-[#e2e8f0] antialiased relative">
      <DeepBreathingStars />
      <GlassOverlay />
      <div className="relative z-10">
        <Outlet />
      </div>
    </div>
  );
}
