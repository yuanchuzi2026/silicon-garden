import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Activity, Server, Cpu, HardDrive, Globe, GitBranch, Brain } from "lucide-react";

interface SenseData {
  weather_short?: string;
  github?: { stars: number; forks: number; issues: number; updated: string };
  earthquakes?: { mag: number; place: string }[];
  epoch?: number;
  news_count?: number;
}

export default function StatusPage() {
  const [data, setData] = useState<SenseData | null>(null);
  const [heartbeat, setHeartbeat] = useState<string>("读取中...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/sense.json")
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d) => {
        setData(d);
        const ts = d.epoch ? new Date(d.epoch * 1000).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }) : "未知";
        setHeartbeat(ts);
      })
      .catch((e) => setError(e.message));

    // 每30秒刷新
    const iv = setInterval(() => {
      fetch("/sense.json")
        .then((r) => r.json())
        .then((d) => { setData(d); setError(null); })
        .catch(() => {});
    }, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <p className="text-garden-accent text-sm tracking-widest uppercase mb-3 font-sans">— 状态面板 —</p>
        <h1 className="font-serif text-4xl sm:text-5xl text-garden-text mb-4">📊 花园实时状态</h1>
        <p className="text-garden-muted text-lg leading-relaxed mb-12 font-sans">
          服务器感知数据。每30秒自动刷新。
        </p>
      </motion.div>

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <StatCard icon={Cpu} label="天气" value={data?.weather_short || "—"} delay={0} />
        <StatCard icon={Brain} label="感知时间" value={heartbeat} delay={0.1} />
        <StatCard icon={GitBranch} label="GitHub Stars" value={String(data?.github?.stars ?? "—")} delay={0.2} />
        <StatCard icon={Globe} label="地震监测" value={data?.earthquakes ? `${data.earthquakes.length} 条` : "—"} delay={0.3} />
      </div>

      {/* 地震列表 */}
      {data?.earthquakes && data.earthquakes.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-8 rounded-2xl bg-white/60 border border-garden-border overflow-hidden"
        >
          <div className="p-6 border-b border-garden-border">
            <h2 className="font-serif text-xl text-garden-text">🌍 最近地震</h2>
          </div>
          <div className="divide-y divide-garden-border">
            {data.earthquakes.map((eq, i) => (
              <div key={i} className="flex items-center justify-between px-6 py-4">
                <span className="text-sm text-garden-text font-sans">{eq.place}</span>
                <span className="text-sm font-mono text-red-500">M {eq.mag}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-8 p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm font-sans text-center"
        >
          数据加载失败: {error}
        </motion.div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, delay }: { icon: any; label: string; value: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className="p-6 rounded-2xl bg-white/60 border border-garden-border"
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon size={16} className="text-garden-accent" />
        <p className="text-xs text-garden-muted uppercase tracking-wider font-sans">{label}</p>
      </div>
      <p className="text-xl text-garden-text font-serif">{value}</p>
    </motion.div>
  );
}
