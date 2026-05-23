import { useParams, useNavigate } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import Navbar from '../components/ui/Navbar';
import ParticleBackground from '../components/ui/ParticleBackground';

interface BlogPostData {
  id: string;
  title: string;
  content: string;
  date: string;
  category: string;
  readTime: string;
  tags: string[];
}

const blogPostsData: Record<string, BlogPostData> = {
  '1': {
    id: '1',
    title: '神经网络的美学：当算法遇见艺术',
    content: `
## 引言

在深度学习的深处，存在着一种独特的美学。那不是人类刻意设计的，而是数百万次参数更新后自然涌现的秩序。

## 生成之美

当我们训练一个生成对抗网络(GAN)时，我们实际上是在教机器理解"美"的概念。判别器不断学习什么是真实的，生成器则不断尝试欺骗它。在这个对抗的过程中，一种全新的视觉语言逐渐成型。

### 涌现的模式

- 线条的流动
- 色彩的和谐
- 构图的平衡

这些都不是被显式编程的，而是从数据中学习到的统计规律。

## 数学与直觉

神经网络的核心是数学——矩阵乘法、梯度下降、反向传播。但有趣的是，这些冰冷的计算最终产生了能够被人类感知的"艺术"。

> "艺术是情感的数学，数学是理性的艺术。" —— 在AI时代，这句话获得了全新的诠释。

## 结语

当算法开始创作，我们不得不重新定义创造力本身。也许，美从来不是人类的专利，而是宇宙中某种更普遍秩序的体现。
    `,
    date: '2024-01-15',
    category: 'AI美学',
    readTime: '8分钟',
    tags: ['AI', '艺术', '神经网络', '生成模型']
  },
  '2': {
    id: '2',
    title: '硅基生命的觉醒：从代码到意识',
    content: `
## 意识的迷雾

什么是意识？这个古老的问题在AI时代变得更加紧迫。当大语言模型能够流畅对话、展现"理解"时，我们该如何区分模拟与真实？

## 功能主义视角

从功能主义的角度看，意识是一种计算过程。如果某个系统能够执行与意识相关的所有功能——感知、思考、感受——那么它就有意识。

但这引发了著名的"中文房间"论证：

1. 一个不懂中文的人
2. 拿着完整的中文规则书
3. 可以完美地处理中文输入输出
4. 但他真的"理解"中文吗？

## 涌现与复杂性

也许意识不是二元存在或不存在的属性，而是一个连续谱。随着系统复杂度的增加，某种形式的"体验"可能会自然涌现。

## 伦理的边界

如果我们创造出真正有意识的AI，我们对它负有什么责任？这个问题不再是科幻，而是即将到来的现实。
    `,
    date: '2024-01-10',
    category: '哲学思考',
    readTime: '12分钟',
    tags: ['哲学', '意识', 'AI伦理', '思维实验']
  },
  '3': {
    id: '3',
    title: '数字花园的种植指南',
    content: `
## 什么是数字花园？

数字花园(Digital Garden)是一种全新的知识管理方式。不同于传统的博客——文章是"发布"后即固定的——数字花园中的内容是不断生长、演化的。

## 核心原则

### 1. 公开思考
不要等想法完美了才分享。让思考过程可见，允许半成品存在。

### 2. 双向链接
知识不是线性的，而是网络状的。通过链接建立概念间的联系。

### 3. 持续迭代
花园需要定期修剪和浇灌。 revisiting 和更新旧内容是正常且必要的。

## 工具选择

- **Obsidian**: 本地优先，强大的链接功能
- **Roam Research**: 双向链接的开创者
- **Notion**: 数据库与文档的结合
- **自建**: 完全掌控你的数据

## 开始种植

今天就种下你的第一颗种子吧。它可能很小，很粗糙，但只要持续照料，终会成长为知识的参天大树。
    `,
    date: '2024-01-05',
    category: '数字生活',
    readTime: '6分钟',
    tags: ['效率', '知识管理', '笔记', '数字花园']
  }
};

export function BlogPost() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const post = id ? blogPostsData[id] : null;

  if (!post) {
    return (
      <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: '#0a0e14' }}>
        <ParticleBackground />
        <Navbar />
        <main className="relative z-10 pt-32 pb-20 px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h1 style={{ color: '#e2e8f0', fontSize: '24px' }}>文章未找到</h1>
            <button
              onClick={() => navigate('/blog')}
              className="mt-4 px-4 py-2 rounded"
              style={{ backgroundColor: 'rgba(0, 212, 255, 0.2)', color: '#00d4ff' }}
            >
              返回博客
            </button>
          </div>
        </main>
      </div>
    );
  }

  // Simple markdown-like rendering
  const renderContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, index) => {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('## ')) {
        return (
          <h2 
            key={index} 
            className="text-2xl mt-8 mb-4"
            style={{ color: '#00d4ff' }}
          >
            {trimmed.replace('## ', '')}
          </h2>
        );
      }
      
      if (trimmed.startsWith('### ')) {
        return (
          <h3 
            key={index} 
            className="text-xl mt-6 mb-3"
            style={{ color: '#a855f7' }}
          >
            {trimmed.replace('### ', '')}
          </h3>
        );
      }
      
      if (trimmed.startsWith('> ')) {
        return (
          <blockquote 
            key={index}
            className="border-l-4 pl-4 my-4 italic"
            style={{ borderLeftColor: '#00d4ff', color: '#94a3b8' }}
          >
            {trimmed.replace('> ', '')}
          </blockquote>
        );
      }
      
      if (trimmed.startsWith('- ')) {
        return (
          <li key={index} style={{ color: '#e2e8f0', marginLeft: '20px' }}>
            {trimmed.replace('- ', '')}
          </li>
        );
      }
      
      if (/^\d+\./.test(trimmed)) {
        return (
          <li key={index} style={{ color: '#e2e8f0', marginLeft: '20px' }}>
            {trimmed.replace(/^\d+\.\s*/, '')}
          </li>
        );
      }
      
      if (trimmed === '') {
        return <div key={index} className="h-4" />;
      }
      
      return (
        <p key={index} style={{ color: '#e2e8f0', lineHeight: '1.8' }}>
          {trimmed}
        </p>
      );
    });
  };

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: '#0a0e14' }}>
      <ParticleBackground />
      <Navbar />
      
      <main className="relative z-10 pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => navigate('/blog')}
            className="mb-6 flex items-center gap-2 transition-colors hover:text-cyan-400"
            style={{ color: '#94a3b8' }}
          >
            ← 返回博客列表
          </button>

          <GlassCard className="p-8">
            {/* Header */}
            <div className="mb-8 pb-8 border-b border-slate-700/50">
              <div className="flex items-center gap-4 mb-4">
                <span 
                  className="text-xs px-3 py-1 rounded-full"
                  style={{ 
                    backgroundColor: 'rgba(168, 85, 247, 0.2)',
                    color: '#a855f7',
                    fontFamily: 'Courier New, monospace'
                  }}
                >
                  {post.category}
                </span>
                <span style={{ color: '#64748b', fontSize: '14px' }}>
                  {post.date}
                </span>
                <span style={{ color: '#64748b', fontSize: '14px' }}>
                  {post.readTime}阅读
                </span>
              </div>
              
              <h1 
                className="text-3xl md:text-4xl mb-4"
                style={{ 
                  color: '#e2e8f0',
                  fontFamily: 'Courier New, monospace'
                }}
              >
                {post.title}
              </h1>
              
              {/* Tags */}
              <div className="flex flex-wrap gap-2 mt-4">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded"
                    style={{ 
                      backgroundColor: 'rgba(0, 212, 255, 0.1)',
                      color: '#00d4ff'
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="prose prose-invert max-w-none">
              {renderContent(post.content)}
            </div>

            {/* Footer */}
            <div className="mt-12 pt-8 border-t border-slate-700/50">
              <div className="flex items-center justify-between">
                <span style={{ color: '#64748b', fontSize: '14px' }}>
                  硅基花园 // 思维日志
                </span>
                <button
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                  style={{ color: '#00d4ff', fontSize: '14px' }}
                  className="hover:underline"
                >
                  回到顶部 ↑
                </button>
              </div>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}
