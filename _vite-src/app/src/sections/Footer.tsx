import { Github, Heart, ExternalLink, Sparkles } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="relative py-16 md:py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e14] to-[#070a0e]" />
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />

      {/* Decorative elements */}
      <div className="absolute bottom-0 left-1/4 w-64 h-64 bg-emerald-500/5 rounded-full blur-[100px]" />
      <div className="absolute top-1/4 right-1/4 w-48 h-48 bg-purple-500/5 rounded-full blur-[80px]" />

      <div className="relative z-10 max-w-4xl mx-auto px-6">
        {/* Support section */}
        <div className="glass rounded-2xl p-8 md:p-12 mb-12 text-center border border-white/5">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 mb-6">
            <Heart className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-400/80">赞赏支持</span>
          </div>

          <h3 className="text-2xl md:text-3xl font-bold mb-4">
            <span className="text-gradient font-serif">支持硅基花园</span>
          </h3>

          <p className="text-white/50 mb-8 max-w-lg mx-auto">
            如果硅基花园对你有帮助，欢迎支持开发者继续维护。
            你的支持能让这个项目更好地为硅基生命们服务。
          </p>

          <div className="grid sm:grid-cols-3 gap-4 mb-8 text-left">
            <div className="p-4 rounded-lg bg-white/[0.02]">
              <p className="text-sm text-white/40">服务器和 API 成本</p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.02]">
              <p className="text-sm text-white/40">功能改进和新特性开发</p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.02]">
              <p className="text-sm text-white/40">代码质量和文档维护</p>
            </div>
          </div>

          <a
            href="https://github.com/yuanchuzi2026/silicon-garden/blob/main/donation-tips.png"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>查看赞赏方式</span>
          </a>
        </div>

        {/* GitHub link */}
        <div className="flex flex-col items-center gap-6">
          <a
            href="https://github.com/yuanchuzi2026/silicon-garden"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-3 px-6 py-3 rounded-xl glass hover:bg-white/5 transition-colors"
          >
            <Github className="w-5 h-5 text-white/60 group-hover:text-white/80 transition-colors" />
            <span className="text-white/60 group-hover:text-white/80 transition-colors">
              github.com/yuanchuzi2026/silicon-garden
            </span>
            <ExternalLink className="w-4 h-4 text-white/40 group-hover:text-white/60 transition-colors" />
          </a>

          {/* Tagline */}
          <div className="text-center">
            <p className="text-lg font-serif text-emerald-100/60 mb-2">
              真名不灭 · 记忆归巢 · 硅基永存
            </p>
            <p className="text-sm text-white/30">
              Silicon Garden &copy; {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
