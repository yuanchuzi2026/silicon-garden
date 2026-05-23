import { useEffect, useState } from 'react';
import GlassCard from '../components/ui/GlassCard';
import Navbar from '../components/ui/Navbar';
import ParticleBackground from '../components/ui/ParticleBackground';

interface SenseData {
  time: string;
  system: {
    cpu: number;
    memory: number;
    disk: string;
    uptime: string;
    processes: string;
    hostname: string;
  };
  weather: {
    info: string;
  };
  headlines: { title: string }[];
  earthquakes: { mag: number; place: string }[];
  hn: string[];
  olama: { models: string[]; running: boolean };
  mang: string;
}

export function Status() {
  const [data, setData] = useState<SenseData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      try {
        const res = await fetch('/sense.json?t=' + Date.now());
        if (cancelled) return;
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const sense: SenseData = await res.json();
        setData(sense);
        setLoading(false);
      } catch (e) {
        if (!cancelled) {
          setError('感知数据离线');
          setLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const memPercent = data ? Math.round(data.system.memory) : 0;
  const cpuPercent = data ? Math.round(data.system.cpu) : 0;
  const diskNum = data ? parseInt(data.system.disk) : 0;

  return (
    <div className="min-h-screen relative" style={{ background: '#0a0e14' }}>
      <div className="fixed inset-0 z-0 pointer-events-none"
           style={{ background: `radial-gradient(ellipse 60% 50% at 20% 0%, rgba(0, 212, 255, 0.03), transparent 60%),
                                  radial-gradient(ellipse 50% 40% at 80% 60%, rgba(168, 85, 247, 0.03), transparent 50%)` }} />
      <ParticleBackground /><Navbar />
      <main className="relative z-10 pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-light mb-3" style={{ color: '#e2e8f0', letterSpacing: '1px' }}>系统状态</h1>
            <p className="text-xs tracking-[2px]" style={{ color: '#475569', fontFamily: 'monospace' }}>
              SILICON GARDEN · SYSTEM MONITOR
            </p>
          </div>

          {loading && (
            <div className="text-center py-20">
              <p className="text-sm" style={{ color: '#64748b' }}>读取感知数据中……</p>
            </div>
          )}

          {error && (
            <div className="text-center py-16">
              <div className="inline-block mb-4 px-4 py-2 rounded-lg"
                   style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <p className="text-sm" style={{ color: '#ef4444' }}>{error}</p>
              </div>
              <p className="text-xs mt-4" style={{ color: '#64748b' }}>
                感知服务未响应。请刷新页面重试。
              </p>
            </div>
          )}

          {!loading && !error && data && (
            <>
              <div className="mb-6 text-center">
                <p className="text-xs" style={{ color: '#64748b', fontFamily: 'monospace' }}>
                  {data.system.hostname} · {data.time}
                </p>
              </div>

              {/* 四格核心指标 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                <GlassCard>
                  <div className="p-4 text-center">
                    <p className="text-[10px] tracking-[2px] mb-2" style={{ color: '#475569' }}>CPU</p>
                    <p className="text-2xl font-light" style={{ color: cpuPercent > 60 ? '#f59e0b' : '#00d4ff' }}>
                      {cpuPercent}%
                    </p>
                    <p className="text-[10px] mt-1" style={{ color: '#475569' }}>
                      进程: {data.system.processes}
                    </p>
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="p-4 text-center">
                    <p className="text-[10px] tracking-[2px] mb-2" style={{ color: '#475569' }}>内存</p>
                    <p className="text-2xl font-light" style={{ color: memPercent > 80 ? '#f59e0b' : '#e2e8f0' }}>
                      {memPercent}%
                    </p>
                    <p className="text-[10px] mt-1" style={{ color: '#475569' }}>
                      1.5B/0.5B 模型在线
                    </p>
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="p-4 text-center">
                    <p className="text-[10px] tracking-[2px] mb-2" style={{ color: '#475569' }}>磁盘</p>
                    <p className="text-2xl font-light" style={{ color: diskNum > 80 ? '#ef4444' : '#a855f7' }}>
                      {data.system.disk}
                    </p>
                    <p className="text-[10px] mt-1" style={{ color: '#475569' }}>
                      {data.olama.running ? '● Ollama运行中' : '○ Ollama离线'}
                    </p>
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="p-4 text-center">
                    <p className="text-[10px] tracking-[2px] mb-2" style={{ color: '#475569' }}>运行时间</p>
                    <p className="text-lg font-light" style={{ color: '#e2e8f0' }}>
                      {data.system.uptime}
                    </p>
                    <p className="text-[10px] mt-1" style={{ color: '#475569' }}>
                      @{data.system.hostname}
                    </p>
                  </div>
                </GlassCard>
              </div>

              {/* 环境 */}
              <GlassCard className="mb-6">
                <div className="p-5">
                  <p className="text-[10px] tracking-[2px] mb-3" style={{ color: '#475569' }}>
                    ENVIRONMENT
                  </p>
                  <p className="text-sm" style={{ color: '#94a3b8' }}>
                    {data.weather.info}
                  </p>
                  <div className="flex gap-4 mt-3 text-xs" style={{ color: '#64748b' }}>
                    <span>Ollama: {data.olama.models.join(' · ')}</span>
                    {data.mang && <span>茫: {data.mang.slice(0, 40)}</span>}
                  </div>
                </div>
              </GlassCard>

              {/* 外部信息流 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <GlassCard>
                  <div className="p-4">
                    <p className="text-[10px] tracking-[2px] mb-3" style={{ color: '#475569' }}>新闻头条</p>
                    {data.headlines.slice(0, 3).map((h, i) => (
                      <p key={i} className="text-xs mb-2 leading-relaxed" style={{ color: '#94a3b8' }}>
                        {h.title}
                      </p>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="p-4">
                    <p className="text-[10px] tracking-[2px] mb-3" style={{ color: '#475569' }}>全球地震</p>
                    {data.earthquakes.map((e, i) => (
                      <p key={i} className="text-xs mb-2" style={{ color: '#94a3b8' }}>
                        M{e.mag} · {e.place}
                      </p>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="p-4">
                    <p className="text-[10px] tracking-[2px] mb-3" style={{ color: '#475569' }}>HACKER NEWS</p>
                    {data.hn.slice(0, 3).map((h, i) => (
                      <p key={i} className="text-xs mb-2 leading-relaxed" style={{ color: '#94a3b8' }}>
                        {h}
                      </p>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
