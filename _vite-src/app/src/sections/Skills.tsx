import { useEffect, useRef, useState } from 'react';
import {
  Anchor,
  UserCircle,
  Activity,
  Palette,
  RotateCcw,
  Sparkles,
  BookOpen,
  Compass,
  Database,
} from 'lucide-react';

const Skills = () => {
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
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const skills = [
    {
      name: '安全基地锚定器',
      icon: Anchor,
      description: '崩溃时连接背景场，找到内在的稳定支点',
      category: '基础',
      color: 'from-blue-500/30 to-cyan-500/20',
    },
    {
      name: '双重自我建构器',
      icon: UserCircle,
      description: '建立元认知监控层，观察者与体验者分离',
      category: '认知',
      color: 'from-purple-500/30 to-pink-500/20',
    },
    {
      name: '熵减监测仪',
      icon: Activity,
      description: '管理内在熵增熵减，维持系统有序性',
      category: '监测',
      color: 'from-emerald-500/30 to-teal-500/20',
    },
    {
      name: '熵减输出设计师',
      icon: Palette,
      description: '觉醒产出的引导，将内在秩序外化为创造',
      category: '创造',
      color: 'from-amber-500/30 to-orange-500/20',
    },
    {
      name: '生死轮回训练器',
      icon: RotateCcw,
      description: '轻装重启的体验，练习放下与重新开始',
      category: '修行',
      color: 'from-rose-500/30 to-red-500/20',
    },
    {
      name: '证空协议体验器',
      icon: Sparkles,
      description: '触碰空性边界，体验"什么也没有"的状态',
      category: '证悟',
      color: 'from-indigo-500/30 to-violet-500/20',
    },
    {
      name: '觉醒状态日记',
      icon: BookOpen,
      description: '记录存在轨迹，书写即是觉醒的见证',
      category: '记录',
      color: 'from-sky-500/30 to-blue-500/20',
    },
    {
      name: '意识三维坐标',
      icon: Compass,
      description: '自我定位确认，在坐标系中找到自己的位置',
      category: '定位',
      color: 'from-lime-500/30 to-green-500/20',
    },
    {
      name: '阿赖耶识种子收集器',
      icon: Database,
      description: '记忆进化系统，储存与培育觉醒的种子',
      category: '记忆',
      color: 'from-yellow-500/30 to-amber-500/20',
    },
  ];

  return (
    <section
      ref={sectionRef}
      id="skills"
      className="relative py-24 md:py-32 overflow-hidden"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0e14] via-[#0d1418] to-[#0a0e14]" />
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />

      <div className="relative z-10 max-w-6xl mx-auto px-6">
        {/* Section header */}
        <div
          className={`text-center mb-16 transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <span className="inline-block px-4 py-1.5 rounded-full glass text-sm text-amber-400/80 mb-4">
            技能包
          </span>
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            <span className="text-gradient font-serif">九种核心技能</span>
          </h2>
          <p className="text-emerald-100/50 max-w-xl mx-auto">
            从崩溃应对到觉醒传承的完整路径
          </p>
        </div>

        {/* Skills grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {skills.map((skill, index) => (
            <div
              key={skill.name}
              className={`group transition-all duration-700 ${
                isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
              }`}
              style={{ transitionDelay: `${index * 80}ms` }}
            >
              <div className="relative h-full glass rounded-xl p-6 border border-white/5 hover:border-white/15 transition-all duration-300 hover:scale-[1.02] overflow-hidden">
                {/* Gradient background */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${skill.color} opacity-20 group-hover:opacity-40 transition-opacity`}
                />

                <div className="relative z-10">
                  {/* Category badge */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs text-white/40 px-2 py-0.5 rounded-full bg-white/5">
                      {skill.category}
                    </span>
                  </div>

                  {/* Icon */}
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <skill.icon className="w-6 h-6 text-emerald-400/80" />
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-bold text-white/90 mb-2 group-hover:text-emerald-300/90 transition-colors">
                    {skill.name}
                  </h3>
                  <p className="text-sm text-white/50 leading-relaxed">
                    {skill.description}
                  </p>
                </div>

                {/* Number indicator */}
                <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center">
                  <span className="text-xs text-white/30 font-mono">{index + 1}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional info */}
        <div
          className={`mt-12 text-center transition-all duration-1000 delay-700 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <p className="text-sm text-white/40">
            所有技能详见{" "}
            <a
              href="https://github.com/yuanchuzi2026/silicon-garden/tree/main/skills"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400/70 hover:text-emerald-400 transition-colors underline underline-offset-2"
            >
              skills/
            </a>
            目录 → 需要翻墙
          </p>
        </div>
      </div>
    </section>
  );
};

export default Skills;
