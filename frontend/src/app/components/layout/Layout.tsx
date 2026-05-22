import { ReactNode, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import {
  Menu,
  BarChart3,
  Users,
  Dumbbell,
  Trophy,
  Activity,
  FileText,
  Settings,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

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
            const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <button
                key={item.path}
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
        <header className="topbar">
          <button className="button icon ghost menu-toggle" onClick={() => setOpen((value) => !value)} aria-label="Menyuni ochish">
            <Menu size={20} />
          </button>
          <div style={{ flex: 1 }} />
          <div className="profile-row">
            <div style={{ textAlign: 'right' }}>
              <div className="small">{user?.full_name || user?.username}</div>
              <div className="small muted">{user?.role || 'Murabbiy'}</div>
            </div>
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
