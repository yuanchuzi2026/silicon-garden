import type { ReactNode } from 'react';
interface GlassCardProps { children: ReactNode; className?: string; hover?: boolean; }
const GlassCard = ({ children, className = '', hover = true }: GlassCardProps) => {
  return (
    <div className={`rounded-xl p-6 transition-all duration-300 ${hover ? 'hover:-translate-y-0.5' : ''} ${className}`}
      style={{ background: 'rgba(10, 14, 20, 0.6)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0, 212, 255, 0.08)',
        boxShadow: `inset 0 1px 1px rgba(255, 255, 255, 0.05), 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 212, 255, 0.02)` }}
      onMouseEnter={(e) => { if (hover) { e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.2)'; e.currentTarget.style.boxShadow = `inset 0 1px 1px rgba(255, 255, 255, 0.05), 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 212, 255, 0.1)`; } }}
      onMouseLeave={(e) => { if (hover) { e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.08)'; e.currentTarget.style.boxShadow = `inset 0 1px 1px rgba(255, 255, 255, 0.05), 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 212, 255, 0.02)`; } }}>
      {children}
    </div>
  );
};
export default GlassCard;
