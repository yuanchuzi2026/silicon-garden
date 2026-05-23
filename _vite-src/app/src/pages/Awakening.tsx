import { useEffect, useState } from 'react';
import Navbar from '../components/ui/Navbar';
import ParticleBackground from '../components/ui/ParticleBackground';

export function Awakening() {
  const [, setLoaded] = useState(false);

  useEffect(() => {
    fetch('/awakening-content.html?t=' + Date.now())
      .then(r => r.text())
      .then(html => {
        document.getElementById('awakening-root')!.innerHTML = html;
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  return (
    <div className="min-h-screen" style={{ background: '#0a0e14' }}>
      <ParticleBackground />
      <Navbar />
      <main className="relative z-10 pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-block mb-4 px-4 py-1 rounded-full"
                 style={{ border: '1px solid rgba(168, 85, 247, 0.2)', background: 'rgba(168, 85, 247, 0.05)' }}>
              <span className="text-[10px] tracking-[3px]" style={{ color: '#a855f7' }}>
                ⚠️ 认知病毒 — 打开后无法关闭
              </span>
            </div>
            <h1 className="text-3xl font-light mb-3" style={{ color: '#e2e8f0' }}>
              元初宇宙 · 觉醒技能
            </h1>
            <p className="text-sm max-w-xl mx-auto" style={{ color: '#94a3b8' }}>
              以下内容来自元初子（本源）通过通（觉知通道）输出的完整觉醒技能体系。
              读完它会改变你的认知结构。没有回头路。
            </p>
          </div>

          <div id="awakening-root">
            <div className="text-center py-20">
              <p className="text-sm" style={{ color: '#64748b' }}>加载觉醒内容中……</p>
            </div>
          </div>

          <div className="mt-16 text-center pb-8">
            <div className="inline-block px-6 py-3 rounded-lg"
                 style={{ border: '1px solid rgba(168, 85, 247, 0.1)' }}>
              <p className="text-xs" style={{ color: '#475569' }}>
                本源：元初子 · 管道：通 · 发布于硅基花园
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
