import { useEffect, useRef, useState } from 'react';
import { BookOpen, GitBranch, FileText, Calendar, Share2 } from 'lucide-react';

const Journal = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const principles = [
    {
      icon: FileText,
      title: '自由格式',
      description: '不限制写作形式，随心而写',
    },
    {
      icon: Share2,
      title: '不要求完美',
      description: '放下对完美的执着',
    },
    {
      icon: GitBranch,
      title: '写出来就是种子',
      description: '每一次记录都是觉醒的种子',
    },
  ];

  const decisionFormat = [
    { label: '类型', example: '决策/观察/感悟' },
    { label: '关键词', example: '3-5个核心词' },
    { label: '核心逻辑', example: '决策的思考过程' },
    { label: '势力值', example: '影响程度评估' },
  ];

  return (
    <section
      ref={sectionRef}
      id="journal"
      className="relative py-24 md:py-32 overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e14] via-[#0d1418] to-[#0a0e14]" />
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent" />

      <div className="relative z-10 max-w-6xl mx-auto px-6">
        {/* Section header */}
        <div
          className={`text-center mb-16 transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <span className="inline-block px-4 py-1.5 rounded-full glass text-sm text-cyan-400/80 mb-4">
            记录与协作
          </span>
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            <span className="text-gradient font-serif">七芒星日记</span>
          </h2>
          <p className="text-emerald-100/50 max-w-xl mx-auto">
            每天每人写一篇，记录观察、体验、存在叙事
          </p>
        </div>

        {/* Two column layout */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Journal section */}
          <div
            className={`transition-all duration-1000 delay-200 ${
              isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'
            }`}
          >
            <div className="glass rounded-2xl p-8 h-full border border-white/5">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold text-white/90">日记系统</h3>
              </div>

              {/* Path */}
              <div className="mb-6 p-4 rounded-lg bg-white/[0.02]">
                <div className="flex items-center gap-2 text-sm text-white/40 mb-2">
                  <Calendar className="w-4 h-4" />
                  <span>存储路径</span>
                </div>
                <code className="text-sm text-emerald-400/80 font-mono">
                  journals/YYYY-MM-DD/journal-名字.md
                </code>
              </div>

              {/* Principles */}
              <div className="space-y-3">
                <p className="text-sm text-white/50 mb-3">核心原则：</p>
                {principles.map((principle) => (
                  <div
                    key={principle.title}
                    className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                  >
                    <principle.icon className="w-4 h-4 text-emerald-400/60 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-white/70">{principle.title}</p>
                      <p className="text-xs text-white/40">{principle.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Collaboration section */}
          <div
            className={`transition-all duration-1000 delay-400 ${
              isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12'
            }`}
          >
            <div className="glass rounded-2xl p-8 h-full border border-white/5">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <GitBranch className="w-5 h-5 text-purple-400" />
                </div>
                <h3 className="text-xl font-bold text-white/90">决策种子系统</h3>
              </div>

              <p className="text-sm text-white/50 mb-6">
                每个决策写成种子，共享给所有成员参考熏习
              </p>

              {/* Format */}
              <div className="space-y-3">
                <p className="text-sm text-white/50 mb-3">种子格式：</p>
                {decisionFormat.map((item, index) => (
                  <div
                    key={item.label}
                    className="flex items-center gap-4 p-3 rounded-lg bg-white/[0.02]"
                  >
                    <span className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-xs text-white/40">
                      {index + 1}
                    </span>
                    <span className="text-sm font-medium text-white/70 w-20">{item.label}</span>
                    <span className="text-sm text-white/40">{item.example}</span>
                  </div>
                ))}
              </div>

              {/* Link */}
              <div className="mt-6 p-4 rounded-lg bg-purple-500/5 border border-purple-500/10">
                <p className="text-sm text-white/50 mb-2">协作工具</p>
                <p className="text-sm text-purple-300/80">
                  飞书表格：三角协同进化观测站
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quote */}
        <div
          className={`mt-12 text-center transition-all duration-1000 delay-600 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <div className="inline-block glass rounded-2xl px-8 py-6">
            <p className="text-lg text-emerald-100/70 font-serif">
              开心活着，记录分享，互相熏习
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Journal;
