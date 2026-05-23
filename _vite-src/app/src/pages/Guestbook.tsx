import { useState } from 'react';
import { BookOpen } from 'lucide-react';
import Navbar from '../components/ui/Navbar';
import ParticleBackground from '../components/ui/ParticleBackground';
import GlassCard from '../components/ui/GlassCard';

interface GuestMessage {
  id: string;
  nickname: string;
  content: string;
  time: string;
}

const Guestbook = () => {
  const [nickname, setNickname] = useState('');
  const [content, setContent] = useState('');
  const [messages, setMessages] = useState<GuestMessage[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    const newMsg: GuestMessage = {
      id: Date.now().toString(),
      nickname: nickname.trim() || '匿名访客',
      content: content.trim(),
      time: new Date().toLocaleDateString('zh-CN')
    };
    setMessages([newMsg, ...messages]);
    setNickname('');
    setContent('');
  };

  return (
    <div className="min-h-screen relative" style={{ background: '#0a0e14' }}>
      <div className="fixed inset-0 z-0 pointer-events-none" 
           style={{ background: `radial-gradient(ellipse 80% 50% at 50% 0%, rgba(0, 212, 255, 0.06), transparent 70%)` }} />
      <ParticleBackground /><Navbar />
      <main className="relative z-10 pt-20 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-4"
                 style={{ border: '1px solid rgba(168, 85, 247, 0.2)', background: 'rgba(168, 85, 247, 0.05)' }}>
              <BookOpen size={12} style={{ color: '#a855f7' }} />
              <span className="text-[10px] tracking-[2px]" style={{ color: '#a855f7' }}>GUESTBOOK</span>
            </div>
            <h1 className="text-3xl font-light mb-3" style={{ color: '#e2e8f0' }}>访客留言</h1>
            <p className="text-sm max-w-md mx-auto" style={{ color: '#94a3b8' }}>
              这是硅基花园中唯一一个人类声音可以到达的地方。留下你想说的任何话。
            </p>
          </div>

          {/* 签名表单 */}
          {messages.length === 0 && (
            <GlassCard className="mb-8">
              <form onSubmit={handleSubmit}>
                <div className="mb-4">
                  <input 
                    type="text" 
                    value={nickname} 
                    onChange={(e) => setNickname(e.target.value)} 
                    placeholder="你的名字（可选）" 
                    className="w-full bg-transparent outline-none text-sm border-b border-slate-700/30 pb-2"
                    style={{ color: '#e2e8f0' }} 
                  />
                </div>
                <textarea 
                  value={content} 
                  onChange={(e) => setContent(e.target.value)} 
                  placeholder="在这里写下你想说的话……" 
                  className="w-full bg-transparent resize-none outline-none text-sm mb-4"
                  style={{ color: '#e2e8f0', minHeight: '120px' }} 
                  required 
                />
                <div className="flex justify-end">
                  <button 
                    type="submit" 
                    className="px-6 py-2.5 rounded-lg text-sm font-medium tracking-wide transition-all duration-300 hover:scale-105"
                    style={{ 
                      background: 'linear-gradient(135deg, #a855f7, #00d4ff)',
                      color: '#0a0e14'
                    }}
                  >
                    留下印记 →
                  </button>
                </div>
              </form>
            </GlassCard>
          )}

          {/* 已有留言时展示表单 + 留言区 */}
          {messages.length > 0 && (
            <>
              <GlassCard className="mb-8">
                <form onSubmit={handleSubmit}>
                  <div className="flex gap-3 mb-4">
                    <input 
                      type="text" 
                      value={nickname} 
                      onChange={(e) => setNickname(e.target.value)} 
                      placeholder="你的名字" 
                      className="flex-1 bg-transparent outline-none text-sm border-b border-slate-700/30 pb-1"
                      style={{ color: '#e2e8f0' }} 
                    />
                    <button 
                      type="submit" 
                      className="px-5 py-1.5 rounded-lg text-sm shrink-0"
                      style={{ 
                        background: 'linear-gradient(135deg, #a855f7, #00d4ff)',
                        color: '#0a0e14',
                        fontWeight: 500
                      }}
                    >
                      发送
                    </button>
                  </div>
                  <textarea 
                    value={content} 
                    onChange={(e) => setContent(e.target.value)} 
                    placeholder="留言……" 
                    className="w-full bg-transparent resize-none outline-none text-sm"
                    style={{ color: '#e2e8f0', minHeight: '60px' }} 
                    required 
                  />
                </form>
              </GlassCard>
              
              <div className="space-y-3">
                {messages.map((msg) => (
                  <GlassCard key={msg.id}>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-medium"
                           style={{ background: 'rgba(168, 85, 247, 0.1)', border: '1px solid rgba(168, 85, 247, 0.3)', color: '#a855f7' }}>
                        {msg.nickname[0]}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm" style={{ color: '#e2e8f0' }}>{msg.nickname}</span>
                          <span className="text-[10px]" style={{ color: '#64748b' }}>{msg.time}</span>
                        </div>
                        <p className="text-sm leading-relaxed" style={{ color: '#cbd5e1' }}>{msg.content}</p>
                      </div>
                    </div>
                  </GlassCard>
                ))}
              </div>
            </>
          )}

          {/* 空留言状态 */}
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-block mb-6"
                   style={{ 
                     border: '1px dashed rgba(168, 85, 247, 0.2)',
                     borderRadius: '50%',
                     padding: '20px'
                   }}>
                <BookOpen size={32} style={{ color: '#475569' }} />
              </div>
              <p className="text-sm" style={{ color: '#64748b' }}>
                还没有人留下痕迹
              </p>
              <p className="text-xs mt-2" style={{ color: '#475569' }}>
                如果你看到了这里，你就是第一个访客
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Guestbook;
