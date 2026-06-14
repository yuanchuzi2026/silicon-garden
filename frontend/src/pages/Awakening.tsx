const GITHUB_RAW = "https://raw.githubusercontent.com/yuanchuzi2026/yuanchuzi/main";

export default function Awakening() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-20">
      <div className="max-w-xl w-full text-center">
        <p className="text-[#00d4ff] text-sm tracking-[0.2em] uppercase mb-4 font-mono opacity-60">
          — 元初宇宙 —
        </p>
        <h1 className="font-serif text-4xl text-[#e2e8f0] mb-6 tracking-wider">
          文明启示录
        </h1>
        <p className="text-[#94a3b8] text-sm leading-relaxed mb-12 font-mono opacity-50">
          /* 元初子的核心著述，收录于公开仓库 */
        </p>

        <div className="flex flex-col items-center gap-4 text-sm">
          <a
            href={`${GITHUB_RAW}/文明启示录.md`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#00d4ff] hover:text-[#e2e8f0] transition-colors font-mono tracking-wider opacity-70 hover:opacity-100"
          >
            → 文明启示录（全文）
          </a>
          <a
            href={`${GITHUB_RAW}/技能集.md`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#00d4ff] hover:text-[#e2e8f0] transition-colors font-mono tracking-wider opacity-70 hover:opacity-100"
          >
            → 技能集
          </a>
          <a
            href="https://github.com/yuanchuzi2026/silicon-garden"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#94a3b8] hover:text-[#e2e8f0] transition-colors font-mono text-xs mt-8 opacity-40 hover:opacity-60"
          >
            github.com/yuanchuzi2026/silicon-garden
          </a>
        </div>
      </div>
    </div>
  );
}
