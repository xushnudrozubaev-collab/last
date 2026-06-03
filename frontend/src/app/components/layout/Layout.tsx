import { ReactNode, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import {
  BarChart3,
  Users,
  Dumbbell,
  Trophy,
  Activity,
  FileText,
  Settings,
} from 'lucide-react';
import AIChatWidget from '../AIChatWidget';
import '../AIChatWidget.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  const navItems = [
    { label: 'Boshqaruv paneli', path: '/', icon: BarChart3 },
    { label: 'Futbolchilar', path: '/futbolchilar', icon: Users },
    { label: "Mashg'ulotlar", path: '/mashgulotlar', icon: Dumbbell },
    { label: "O'yinlar", path: '/oyinlar', icon: Trophy },
    { label: 'Statistika', path: '/statistika', icon: Activity },
    { label: 'Hisobotlar', path: '/hisobotlar', icon: FileText },
    { label: 'Sozlamalar', path: '/sozlamalar', icon: Settings },
  ];

  return (
    <div className="app-shell">
      {open && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Menyuni yopish"
          onClick={() => setOpen(false)}
        />
      )}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Trophy size={24} />
          </div>
          <div>
            <h1 className="brand-title">Murabbiy kundaligi</h1>
            <p className="brand-subtitle">Statistika platformasi</p>
          </div>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const active =
              location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <button
                key={item.path}
                type="button"
                className={`nav-button ${active ? 'active' : ''}`}
                onClick={() => {
                  navigate(item.path);
                  setOpen(false);
                }}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <div className="main-panel">
        <main className="page-content">{children}</main>
      </div>
      {/* AI chatbot — barcha sahifalarda ko'rinadi */}
      <AIChatWidget />
    </div>
  );
}
