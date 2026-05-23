import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '主页', en: 'Home' },
    { path: '/den', label: '🌌密室', en: 'Den' },
    { path: '/guestbook', label: '📝留言', en: 'Guestbook' },
    { path: '/blog', label: '📖博客', en: 'Blog' },
    { path: '/status', label: '📊状态', en: 'Status' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50"
         style={{
           background: 'linear-gradient(180deg, rgba(10,14,20,0.92) 0%, rgba(10,14,20,0.75) 60%, rgba(10,14,20,0) 100%)',
           borderBottom: '1px solid rgba(0,212,255,0.08)',
         }}>
      <div className="relative mx-auto max-w-3xl px-3 py-2 flex items-center justify-center gap-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path));

          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative px-3 py-1.5 transition-all duration-300 group"
              style={{
                color: isActive ? 'rgba(0,212,255,0.85)' : 'rgba(255,255,255,0.3)',
                textShadow: isActive ? '0 0 12px rgba(0,212,255,0.3)' : 'none',
              }}
            >
              {/* 激活下划线 */}
              {isActive && (
                <span className="absolute bottom-0 left-2 right-2 h-px"
                      style={{ background: 'linear-gradient(90deg, transparent, rgba(0,212,255,0.5), transparent)' }} />
              )}

              <span className="relative z-10 text-xs tracking-[1.5px] font-light">
                {item.label}
              </span>

              {/* hover发光 */}
              <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{
                      background: 'rgba(0,212,255,0.04)',
                      borderRadius: '4px',
                    }} />
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navbar;
