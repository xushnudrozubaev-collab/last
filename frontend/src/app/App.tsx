import { CSSProperties, createContext, FormEvent, ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import {
  Activity,
  ArrowLeft,
  BarChart3,
  CalendarDays,
  Check,
  ClipboardList,
  Clock,
  Download,
  Dumbbell,
  Edit,
  FileText,
  Filter,
  LogOut,
  MapPin,
  MoreVertical,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings,
  ShieldAlert,
  Moon,
  Sun,
  Trash2,
  Trophy,
  UserRound,
  Users,
  X,
} from 'lucide-react';
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router';
import {
  AttendanceRecord,
  DashboardData,
  Match,
  MatchStats,
  AttendanceTrendPoint,
  GoalAssistPoint,
  Player,
  PlayerPayload,
  ReportData,
  ReportParams,
  StatisticsData,
  StatisticsPlayerRow,
  StatisticsRankings,
  Training,
  User,
  authAPI,
  dashboardAPI,
  getApiError,
  matchesAPI,
  playersAPI,
  reportsAPI,
  settingsAPI,
  statisticsAPI,
  tokenStore,
  trainingsAPI,
} from './services/api';
import {
  positions,
  trainingTypes,
  matchStatuses,
  attendanceStatuses,
  physicalConditions,
  activityLevels,
  disciplineChoices,
  injuryStatuses,
} from './constants';
import { Layout } from './components/layout/Layout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import TrainingsListPage from '../pages/TrainingsPage';
import RedesignedPlayerDetailPage from '../pages/PlayerDetailPage';

const today = () => new Date().toISOString().slice(0, 10);
const PROJECT_CLUB_NAME = 'Bunyodkor';

type Toast = { id: number; message: string; type: 'success' | 'error' };

const ToastContext = createContext<(message: string, type?: 'success' | 'error') => void>(() => undefined);

function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = Date.now();
    setToasts((items) => [...items, { id, message, type }]);
    setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 3500);
  }, []);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="toast-stack">
        {toasts.map((toast) => (
          <div className={`toast ${toast.type}`} key={toast.id}>
            <span className="toast-icon">
              {toast.type === 'success' ? <Check size={18} /> : <ShieldAlert size={18} />}
            </span>
            <div className="toast-content">
              <strong>{toast.type === 'success' ? 'Muvaffaqiyat' : 'Xatolik'}</strong>
              <div className="small muted">{toast.message}</div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const useToast = () => useContext(ToastContext);

type ThemeMode = 'dark' | 'light';

const ThemeContext = createContext<{
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
}>({
  theme: 'dark',
  setTheme: () => undefined,
});

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const savedTheme = localStorage.getItem('coach-theme');
    return savedTheme === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('coach-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme: setThemeState }}>
      {children}
    </ThemeContext.Provider>
  );
}

const useTheme = () => useContext(ThemeContext);

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenLoading />;
  if (!user) return <Navigate to="/kirish" replace />;
  return <>{children}</>;
}

function FullScreenLoading() {
  return (
    <div className="app-shell loading-state">
      <div>
        <RefreshCw style={{ margin: '0 auto', display: 'block' }} />
        <p>Yuklanmoqda...</p>
      </div>
    </div>
  );
}

function formatDate(value?: string) {
  if (!value) return '-';
  return new Intl.DateTimeFormat('uz-UZ', { year: 'numeric', month: 'short', day: '2-digit' }).format(new Date(value));
}

function formatTime(value?: string) {
  return value ? value.slice(0, 5) : '-';
}

function formatDateShort(value?: string) {
  if (!value) return '-';
  try {
    const d = new Date(value);
    const months = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
    return `${d.getDate()} ${months[d.getMonth()]}`;
  } catch {
    return value;
  }
}

function percent(value: number) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function shortDisplayName(value?: string) {
  if (!value) return '-';
  const parts = value.trim().split(/\s+/);
  if (parts.length < 2) return value;
  return `${parts[0][0]}. ${parts.slice(1).join(' ')}`;
}

function dayStamp(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate()).getTime();
}

function relativeDayLabel(value?: string) {
  if (!value) return '';
  const target = dayStamp(new Date(value));
  const current = dayStamp(new Date());
  const days = Math.round((current - target) / 86400000);
  if (days === 0) return 'Bugun';
  if (days === 1) return 'Kecha';
  if (days > 1 && days < 7) return `${days} kun oldin`;
  return formatDateShort(value);
}

function averageAttendance(trainings: Training[]) {
  if (!trainings.length) return 0;
  return Math.round(trainings.reduce((sum, training) => sum + Number(training.attendance_percent || 0), 0) / trainings.length);
}

function weeklyAttendanceSummary(trainings: Training[]) {
  const now = dayStamp(new Date());
  const currentWeekStart = now - 6 * 86400000;
  const previousWeekStart = currentWeekStart - 7 * 86400000;
  const current = trainings.filter((training) => {
    const stamp = dayStamp(new Date(training.training_date));
    return stamp >= currentWeekStart && stamp <= now;
  });
  const previous = trainings.filter((training) => {
    const stamp = dayStamp(new Date(training.training_date));
    return stamp >= previousWeekStart && stamp < currentWeekStart;
  });
  const currentAverage = averageAttendance(current.length ? current : trainings);
  const previousAverage = averageAttendance(previous);
  return {
    average: currentAverage,
    trend: previous.length ? currentAverage - previousAverage : 0,
  };
}

function Field({
  label,
  children,
  wide,
}: {
  label: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="field" style={wide ? { gridColumn: '1 / -1' } : undefined}>
      <label>{label}</label>
      {children}
    </div>
  );
}

function Modal({
  title,
  children,
  onClose,
  action,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  action?: ReactNode;
}) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <h2 className="card-title">{title}</h2>
          <div className="toolbar" style={{ margin: 0 }}>
            {action}
            <button className="button icon ghost" onClick={onClose} title="Yopish">
              <X size={18} />
            </button>
          </div>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

function ConfirmModal({
  title,
  text,
  onCancel,
  onConfirm,
}: {
  title: string;
  text: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p className="muted">{text}</p>
      <div className="form-actions">
        <button className="button ghost" onClick={onCancel}>
          Bekor qilish
        </button>
        <button className="button danger" onClick={onConfirm}>
          <Trash2 size={18} /> O'chirish
        </button>
      </div>
    </Modal>
  );
}

function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  note,
  tone = 'blue',
}: {
  icon: typeof Users;
  label: string;
  value: string | number;
  note?: string;
  tone?: 'blue' | 'green' | 'yellow' | 'red';
}) {
  return (
    <div className="card stat-card">
      <div className="stat-top">
        <div className={`stat-icon ${tone}`}>
          <Icon size={22} />
        </div>
        <span className={`badge ${tone}`}>{label}</span>
      </div>
      <p className="stat-value">{value}</p>
      {note && <div className="small muted">{note}</div>}
    </div>
  );
}

function Progress({ value }: { value: number }) {
  return (
    <div className="progress-track">
      <div className="progress-fill" style={{ width: `${percent(value)}%` }} />
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text?: string }) {
  return (
    <div className="empty-state">
      <div>
        <Search size={34} />
        <h3>{title}</h3>
        {text && <p>{text}</p>}
      </div>
    </div>
  );
}

function ErrorState({ text, retry }: { text: string; retry?: () => void }) {
  return (
    <div className="error-state">
      <div>
        <ShieldAlert size={36} />
        <p>{text}</p>
        {retry && (
          <button className="button primary" onClick={retry}>
            <RefreshCw size={18} /> Qayta urinish
          </button>
        )}
      </div>
    </div>
  );
}

const navItems = [
  { label: 'Boshqaruv paneli', path: '/', icon: BarChart3 },
  { label: 'Futbolchilar', path: '/futbolchilar', icon: Users },
  { label: "Mashg'ulotlar", path: '/mashgulotlar', icon: Dumbbell },
  { label: "O'yinlar", path: '/oyinlar', icon: Trophy },
  { label: 'Statistika', path: '/statistika', icon: Activity },
  { label: 'Hisobotlar', path: '/hisobotlar', icon: FileText },
  { label: 'Sozlamalar', path: '/sozlamalar', icon: Settings },
];

function AuthPage() {
  const { user, login } = useAuth();
  const notify = useToast();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    username: '',
    password: '',
  });

  if (user) return <Navigate to="/" replace />;

  const update = (key: string, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form.username || !form.password) {
      notify('Login va parol majburiy.', 'error');
      return;
    }
    setLoading(true);
    try {
      await login(form.username, form.password);
      notify('Tizimga kirildi.');
    } catch (error) {
      notify(getApiError(error, "Ma'lumotlarni tekshiring."), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-info">
          <div className="auth-logo" aria-hidden="true">
            <Trophy size={30} />
          </div>
          <h1 className="auth-title">Futbol murabbiylari platformasi</h1>
          <p className="auth-description">
            Raqamli kundalik, mashg'ulotlar va futbolchi ma'lumotlarini boshqarish tizimi.
          </p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <h2 className="auth-form-title">Tizimga kirish</h2>
          <div className="grid" style={{ gap: 14 }}>
            <Field label="Foydalanuvchi nomi">
              <input className="input auth-input" value={form.username} onChange={(event) => update('username', event.target.value)} placeholder="Foydalanuvchi nomi" autoComplete="username" />
            </Field>
            <Field label="Parol">
              <input className="input auth-input" type="password" value={form.password} onChange={(event) => update('password', event.target.value)} placeholder="Parol" autoComplete="current-password" />
            </Field>
            <button className="button primary auth-submit" disabled={loading}>
              {loading ? 'Kutilmoqda...' : 'Kirish'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DashboardPage() {
  type DashboardPeriod = 'week' | 'month' | 'season';

  const [data, setData] = useState<DashboardData | null>(null);
  const [period, setPeriod] = useState<DashboardPeriod>('season');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setData(await dashboardAPI.get(period));
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [period]);

  if (loading) return <div className="loading-state">Yuklanmoqda...</div>;
  if (error) return <ErrorState text={error} retry={load} />;
  if (!data) return <EmptyState title="Ma'lumot topilmadi" />;

  const periodStats = data.period_stats;
  const periodOptions: Array<{ value: DashboardPeriod; label: string }> = [
    { value: 'week', label: 'Bu hafta' },
    { value: 'month', label: 'Bu oy' },
    { value: 'season', label: 'Bu mavsum' },
  ];
  const trendText = (value?: number, suffix = '%') => {
    const current = Number(value || 0);
    if (!current) return "O'zgarish yo'q";
    return `${current > 0 ? '+' : ''}${current}${suffix} o'tgan davrdan`;
  };
  const trendTone = (value?: number) => (Number(value || 0) < 0 ? 'down' : 'up');
  const recentTrainingSummary = weeklyAttendanceSummary(data.recent_trainings);
  const recentTrainingTrend = recentTrainingSummary.trend;
  const dashboardStats = [
    {
      className: 'metric-blue',
      icon: Users,
      label: 'Futbolchilar',
      value: data.total_players,
      note: "Jami ro'yxatda",
      trend: 'Tarkib nazorati',
      trendTone: 'up',
    },
    {
      className: 'metric-green',
      icon: Dumbbell,
      label: "Mashg'ulotlar",
      value: periodStats?.trainings_count ?? data.recent_trainings.length,
      note: `${data.period_label || 'Tanlangan davr'} bo'yicha`,
      trend: trendText(periodStats?.trends.trainings),
      trendTone: trendTone(periodStats?.trends.trainings),
    },
    {
      className: 'metric-purple',
      icon: Activity,
      label: "O'rtacha davomad",
      value: `${periodStats?.average_attendance_percent ?? data.team_attendance_percent}%`,
      note: `${data.period_label || 'Davr'} faol yozuvlari`,
      trend: trendText(periodStats?.trends.attendance),
      trendTone: trendTone(periodStats?.trends.attendance),
    },
    {
      className: 'metric-cyan',
      icon: BarChart3,
      label: "O'rtacha baho",
      value: periodStats?.average_rating ?? data.team_average_rating,
      note: `${data.period_label || 'Davr'} mashg'ulotlari`,
      trend: trendText(periodStats?.trends.rating, ''),
      trendTone: trendTone(periodStats?.trends.rating),
    },
    {
      className: 'metric-green',
      icon: Trophy,
      label: "O'yinlar",
      value: periodStats?.matches_count ?? data.recent_matches.length,
      note: `Bu davr: ${periodStats?.match_record.wins ?? 0}G ${periodStats?.match_record.draws ?? 0}D ${periodStats?.match_record.losses ?? 0}M`,
      trend: trendText(periodStats?.trends.matches),
      trendTone: trendTone(periodStats?.trends.matches),
    },
    {
      className: 'metric-blue',
      icon: BarChart3,
      label: 'Gollar',
      value: periodStats?.goals ?? 0,
      note: `${data.period_label || 'Davr'} yakunlangan o'yinlari`,
      trend: trendText(periodStats?.trends.goals),
      trendTone: trendTone(periodStats?.trends.goals),
    },
    {
      className: 'metric-purple',
      icon: Trophy,
      label: 'Eng faol futbolchi',
      value: shortDisplayName(data.top_recent_active_player?.player_name),
      note: data.top_recent_active_player ? `Avg faollik: ${data.top_recent_active_player.average_activity}/10` : "So'nggi 5 mashg'ulot",
      trend: "So'nggi 5 mashg'ulot",
      trendTone: 'up',
    },
    {
      className: 'metric-red',
      icon: ShieldAlert,
      label: 'Jarohat',
      value: periodStats?.injury_related_count ?? data.injured_players.length,
      note: "So'nggi attendance bo'yicha",
      trend: 'Nazorat',
      trendTone: 'down',
    },
  ];

  return (
    <Layout>
      <section className="dashboard-mini">
        <div className="dashboard-mini-head">
          <div>
            <h1>Boshqaruv paneli</h1>
            <p className="muted">Jamoa holati, trendlar va ogohlantirishlar tanlangan davr bo'yicha shakllanadi.</p>
          </div>
          <div className="dashboard-period">
            <span>Ko'rsatish:</span>
            {periodOptions.map((option) => (
              <button
                className={period === option.value ? 'active' : ''}
                key={option.value}
                onClick={() => setPeriod(option.value)}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="dashboard-metric-grid">
          {/* KARTA 1 — JAMOA */}
          <button
            type="button"
            className="mini-metric metric-blue"
            onClick={() => navigate('/futbolchilar')}
            aria-label="Futbolchilar bo'limiga o'tish"
          >
            <div className="dmc-header">
              <Users size={16} className="dmc-icon" />
              <span className="dmc-label">JAMOA</span>
            </div>
            <strong className="dmc-value">{data.total_players}</strong>
            <p className="dmc-note">Jami futbolchilar</p>
            <div className="dmc-divider" />
            <div className="dmc-rows">
              <div className="dmc-row">
                <Trophy size={13} />
                <span>O'yinlar</span>
                <b>{periodStats?.matches_count ?? data.recent_matches.length}</b>
              </div>
              <div className="dmc-row">
                <Activity size={13} />
                <span>Gollar</span>
                <b>{periodStats?.goals ?? 0}</b>
              </div>
            </div>
          </button>

          {/* KARTA 2 — MASHG'ULOTLAR */}
          <button
            type="button"
            className="mini-metric metric-green"
            onClick={() => navigate('/mashgulotlar')}
            aria-label="Mashg'ulotlar bo'limiga o'tish"
          >
            <div className="dmc-header">
              <Dumbbell size={16} className="dmc-icon" />
              <span className="dmc-label">MASHG'ULOTLAR</span>
            </div>
            <strong className="dmc-value">{periodStats?.trainings_count ?? data.recent_trainings.length}</strong>
            <p className="dmc-note">{data.period_label || 'Tanlangan davr'} bo'yicha</p>
            <div className="dmc-divider" />
            <div className="dmc-rows">
              <div className="dmc-row">
                <Users size={13} />
                <span>Davomat</span>
                <b>{periodStats?.average_attendance_percent ?? data.team_attendance_percent}%</b>
              </div>
              <div className="dmc-row">
                <BarChart3 size={13} />
                <span>O'rt. baho</span>
                <b>{periodStats?.average_rating ?? data.team_average_rating}</b>
              </div>
            </div>
          </button>

          {/* KARTA 3 — NATIJALAR */}
          <button
            type="button"
            className="mini-metric metric-purple"
            onClick={() => navigate('/oyinlar')}
            aria-label="O'yinlar va natijalar bo'limiga o'tish"
          >
            <div className="dmc-header">
              <Trophy size={16} className="dmc-icon" />
              <span className="dmc-label">NATIJALAR</span>
            </div>
            <strong className="dmc-value" style={{ fontSize: 20 }}>
              {periodStats?.match_record.wins ?? 0}G &nbsp;
              {periodStats?.match_record.draws ?? 0}D &nbsp;
              {periodStats?.match_record.losses ?? 0}M
            </strong>
            <p className="dmc-note">G'alaba / Durang / Mag'lubiyat</p>
            <div className="dmc-divider" />
            <div className="dmc-rows">
              <div className="dmc-row">
                <span style={{ color: '#4ade80' }}>●</span>
                <span>G'alaba</span>
                <b>{periodStats?.match_record.wins ?? 0}</b>
              </div>
              <div className="dmc-row">
                <span style={{ color: '#fbbf24' }}>●</span>
                <span>Durang</span>
                <b>{periodStats?.match_record.draws ?? 0}</b>
              </div>
              <div className="dmc-row">
                <span style={{ color: '#f87171' }}>●</span>
                <span>Mag'lubiyat</span>
                <b>{periodStats?.match_record.losses ?? 0}</b>
              </div>
            </div>
          </button>

          {/* KARTA 4 — HOLAT */}
          <button
            type="button"
            className="mini-metric metric-cyan"
            onClick={() => navigate('/statistika')}
            aria-label="Statistika va holat bo'limiga o'tish"
          >
            <div className="dmc-header">
              <ShieldAlert size={16} className="dmc-icon" />
              <span className="dmc-label">HOLAT</span>
            </div>
            <strong className="dmc-value" style={{ fontSize: 18 }}>
              {shortDisplayName(data.top_recent_active_player?.player_name) || '—'}
            </strong>
            <p className="dmc-note">
              {data.top_recent_active_player
                ? `Faollik: ${data.top_recent_active_player.average_activity}/10`
                : "Ma'lumot yo'q"}
            </p>
            <div className="dmc-divider" />
            <div className="dmc-rows">
              <div className="dmc-row">
                <span style={{ color: '#4ade80' }}>●</span>
                <span>Jarohat</span>
                <b>{periodStats?.injury_related_count ?? data.injured_players.length}</b>
              </div>
              <div className="dmc-row">
                <Users size={13} />
                <span>Eng faol</span>
                <b>{shortDisplayName(data.top_recent_active_player?.player_name) || '—'}</b>
              </div>
            </div>
          </button>
        </div>
      </section>

      <div className="grid dashboard-lists dashboard-recent-grid" style={{ marginTop: 18 }}>
        <section className="card dashboard-list-card dashboard-recent-card">
          <div className="dashboard-recent-head">
            <div className="dashboard-recent-heading">
              <span className="dashboard-recent-head-icon green"><Dumbbell size={20} /></span>
              <div>
                <h2 className="card-title">Oxirgi mashg'ulotlar</h2>
                <p>So'nggi mashg'ulotlar va qatnashuv ko'rsatkichi</p>
              </div>
            </div>
            <button className="dashboard-recent-link" onClick={() => navigate('/mashgulotlar')} title="Batafsil ko'rish">
              <ArrowLeft size={18} />
            </button>
          </div>

          {data.recent_trainings.length ? (
            <>
              <div className="dashboard-training-list">
                {data.recent_trainings.slice(0, 4).map((training) => (
                  <article className="dashboard-training-item" key={training.id}>
                    <span className="dashboard-training-icon"><Activity size={20} /></span>
                    <div className="dashboard-training-copy">
                      <strong title={training.title}>{training.title}</strong>
                      <p>
                        <span><CalendarDays size={14} /> {formatDateShort(training.training_date)}</span>
                        {relativeDayLabel(training.training_date) && <i>{relativeDayLabel(training.training_date)}</i>}
                      </p>
                    </div>
                    <div className="dashboard-training-attendance">
                      <b>{training.attendance_present}/{training.attendance_total || training.marked_count || 0}</b>
                      <span><Users size={14} /> {Math.round(training.attendance_percent)}% qatnashdi</span>
                    </div>
                  </article>
                ))}
              </div>
              <article className="dashboard-attendance-summary">
                <div className="dashboard-attendance-ring" style={{ '--attendance': `${recentTrainingSummary.average}%` } as CSSProperties}>
                  <strong>{recentTrainingSummary.average}%</strong>
                </div>
                <div>
                  <strong>Umumiy qatnashuv</strong>
                  <p>Haftalik o'rtacha ko'rsatkich</p>
                </div>
                <span className={recentTrainingTrend < 0 ? 'down' : 'up'}>
                  {recentTrainingTrend > 0 ? '↑' : recentTrainingTrend < 0 ? '↓' : '•'} {recentTrainingTrend > 0 ? '+' : ''}{recentTrainingTrend}%
                  <small>O'tgan haftaga nisbatan</small>
                </span>
              </article>
            </>
          ) : (
            <EmptyState title="Mashg'ulotlar hali kiritilmagan" />
          )}
        </section>

        <section className="card dashboard-list-card dashboard-recent-card">
          <div className="dashboard-recent-head">
            <div className="dashboard-recent-heading">
              <span className="dashboard-recent-head-icon blue"><Trophy size={20} /></span>
              <div>
                <h2 className="card-title">Oxirgi o'yinlar</h2>
                <p>Bunyodkor uchrashuvlari va joriy holat</p>
              </div>
            </div>
            <button className="dashboard-recent-link" onClick={() => navigate('/oyinlar')} title="Batafsil ko'rish">
              <ArrowLeft size={18} />
            </button>
          </div>

          {data.recent_matches.length ? (
            <>
              <div className="dashboard-match-list">
                {data.recent_matches.slice(0, 5).map((match) => {
                  const fixture = getProjectClubFixture(match);
                  const result = getMatchResultForTeam(match);
                  const scoreReady = fixture.left.score !== null && fixture.right.score !== null;
                  return (
                    <article className="dashboard-match-item" key={match.id}>
                      <div className="dashboard-match-fixture">
                        <span className="dashboard-match-logos">
                          <TeamLogo teamName={fixture.left.name} logoUrl={fixture.left.logoUrl} size="sm" />
                          <TeamLogo teamName={fixture.right.name} logoUrl={fixture.right.logoUrl} size="sm" />
                        </span>
                        <div>
                          <strong title={`${fixture.left.name} vs ${fixture.right.name}`}>
                            {fixture.left.name} <i>vs</i> {fixture.right.name}
                          </strong>
                          <p>
                            <span><CalendarDays size={14} /> {formatDateShort(match.match_date)}</span>
                            <span><MapPin size={14} /> {match.stadium}</span>
                          </p>
                        </div>
                      </div>
                      <div className="dashboard-match-badges">
                        {match.status === 'upcoming' && <span className="dashboard-match-badge upcoming">Rejalashtirilgan</span>}
                        {match.status === 'live' && <span className="dashboard-match-badge live"><i /> Jonli</span>}
                        {match.status === 'played' && <span className="dashboard-match-badge finished">Yakunlangan</span>}
                        {match.status !== 'upcoming' && <span className={`dashboard-match-badge result ${matchResultTone(result)}`}>{result}</span>}
                      </div>
                      <strong className={`dashboard-match-score ${scoreReady ? 'ready' : 'empty'}`}>{scoreReady ? `${fixture.left.score}:${fixture.right.score}` : "Hisob yo'q"}</strong>
                      <button className="dashboard-match-menu" type="button" title="Qo'shimcha">
                        <MoreVertical size={18} />
                      </button>
                    </article>
                  );
                })}
              </div>
            </>
          ) : (
            <EmptyState title="O'yinlar hali kiritilmagan" />
          )}
        </section>
      </div>

      <section className="dashboard-alert-band">
        <ShieldAlert size={18} />
        <div>
          {data.warnings.length ? (
            data.warnings.slice(0, 3).map((item, index) => (
              <p key={`${item.message}-${index}`}>
                <strong>{item.type}:</strong> {item.message}
              </p>
            ))
          ) : (
            <p>Hozircha muhim ogohlantirish yo'q.</p>
          )}
        </div>
      </section>

    </Layout>
  );
}

function playerFormDefaults(): Partial<Player> {
  return {
    full_name: '',
    shirt_number: 1,
    position: 'forward',
    age: 18,
    nationality: "O'zbekiston",
    height: '1.75',
    weight: 70,
    join_date: today(),
    short_note: '',
  };
}

type PlayerFormValues = PlayerPayload & {
  photoPreview?: string;
};

function PlayerForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial: Partial<Player>;
  onSubmit: (data: PlayerPayload) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<PlayerFormValues>({ ...initial, photoPreview: initial.photo_url });
  const set = (key: keyof PlayerFormValues, value: string | number | File | null) => setForm((current) => ({ ...current, [key]: value }));
  const currentPhoto = form.photo instanceof File ? form.photoPreview : initial.photo_url;

  const setPhoto = (file: File | null) => {
    setForm((current) => {
      if (current.photoPreview?.startsWith('blob:')) {
        URL.revokeObjectURL(current.photoPreview);
      }
      return {
        ...current,
        photo: file,
        photoPreview: file ? URL.createObjectURL(file) : initial.photo_url,
      };
    });
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      ...form,
      shirt_number: Number(form.shirt_number || 1),
      age: Number(form.age || 18),
      weight: Number(form.weight || 70),
    });
  };

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        <Field label="F.I.Sh.">
          <input className="input" required value={form.full_name || ''} onChange={(event) => set('full_name', event.target.value)} />
        </Field>
        <Field label="Forma raqami">
          <input className="input" type="number" min={1} required value={form.shirt_number || 1} onChange={(event) => set('shirt_number', Number(event.target.value))} />
        </Field>
        <Field label="Pozitsiya">
          <select className="select" required value={form.position || 'forward'} onChange={(event) => set('position', event.target.value)}>
            {positions.filter((item) => item.value).map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Yosh">
          <input className="input" type="number" min={5} required value={form.age || 18} onChange={(event) => set('age', Number(event.target.value))} />
        </Field>
        <Field label="Millati">
          <input className="input" required value={form.nationality || ''} onChange={(event) => set('nationality', event.target.value)} />
        </Field>
        <Field label="Bo'yi, metr">
          <input className="input" required value={form.height || ''} onChange={(event) => set('height', event.target.value)} />
        </Field>
        <Field label="Vazni, kg">
          <input className="input" type="number" min={20} required value={form.weight || 70} onChange={(event) => set('weight', Number(event.target.value))} />
        </Field>
        <Field label="Jamoaga qo'shilgan sana">
          <input className="input" type="date" required value={form.join_date || today()} onChange={(event) => set('join_date', event.target.value)} />
        </Field>
        <Field label="Futbolchi rasmi" wide>
          <div className="profile-row">
            {currentPhoto ? (
              <img className="avatar avatar-lg" src={currentPhoto} alt={form.full_name || 'Futbolchi rasmi'} />
            ) : (
              <span className="avatar avatar-lg">{getPlayerInitials(form.full_name || 'PL')}</span>
            )}
            <input
              className="input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => setPhoto(event.target.files?.[0] || null)}
            />
          </div>
        </Field>
        <Field label="Murabbiy qaydi" wide>
          <textarea className="textarea" value={form.short_note || ''} onChange={(event) => set('short_note', event.target.value)} />
        </Field>
      </div>
      <div className="form-actions">
        <button className="button ghost" type="button" onClick={onCancel}>
          Bekor qilish
        </button>
        <button className="button primary">
          <Save size={18} /> Saqlash
        </button>
      </div>
    </form>
  );
}

function getPlayerInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [position, setPosition] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<Player | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<Player | null>(null);
  const notify = useToast();
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setPlayers(await playersAPI.list({ search, position }));
      const next = new URLSearchParams();
      if (search) next.set('search', search);
      setSearchParams(next, { replace: true });
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [position]);

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    load();
  };

  const save = async (data: PlayerPayload) => {
    try {
      if (editing) {
        await playersAPI.update(editing.id, data);
        notify("Futbolchi ma'lumotlari yangilandi.");
      } else {
        await playersAPI.create(data);
        notify("Futbolchi qo'shildi.");
      }
      setEditing(null);
      setCreating(false);
      load();
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  const remove = async () => {
    if (!deleting) return;
    try {
      await playersAPI.remove(deleting.id);
      notify("Futbolchi o'chirildi.");
      setDeleting(null);
      load();
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  return (
    <Layout>
      <PageHeader
        title="Futbolchilar"
        description="Futbolchilarni qo'shing, tahrirlang, qidiring va mashg'ulot tarixi orqali holatini kuzating."
        action={
          <button className="button primary" onClick={() => setCreating(true)}>
            <Plus size={18} /> Qo'shish
          </button>
        }
      />
      <form className="toolbar" onSubmit={submitSearch}>
        <div style={{ flex: 1, minWidth: 240 }}>
          <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Qidirish" />
        </div>
        <select className="select" style={{ width: 220 }} value={position} onChange={(event) => setPosition(event.target.value)}>
          {positions.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <button className="button">
          <Search size={18} /> Qidirish
        </button>
        <button type="button" className="button ghost" onClick={load}>
          <RefreshCw size={18} /> Yangilash
        </button>
      </form>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Futbolchilar ro'yxati</h2>
          <span className="badge blue">{players.length} ta futbolchi</span>
        </div>
        {loading ? (
          <div className="loading-state">Yuklanmoqda...</div>
        ) : error ? (
          <ErrorState text={error} retry={load} />
        ) : players.length ? (
          <div className="players-grid">
            {players.map((player) => (
              <article className={`player-card ${Number(player.average_rating || 0) >= 8 ? 'player-card-featured' : ''}`} key={player.id}>
                <div className="player-card-top">
                  <span className="player-number">#{player.shirt_number}</span>
                  <div className="player-card-actions">
                    <button className="button icon ghost action-icon" aria-label="Batafsil ko'rish" title="Batafsil ko'rish" onClick={() => navigate(`/futbolchilar/${player.id}`)}>
                      <UserRound size={17} />
                    </button>
                    <button className="button icon ghost action-icon" title="Tahrirlash" onClick={() => setEditing(player)}>
                      <Edit size={17} />
                    </button>
                    <button className="button icon ghost action-icon danger-action" title="O'chirish" onClick={() => setDeleting(player)}>
                      <Trash2 size={17} />
                    </button>
                  </div>
                </div>

                <button className="player-card-main" type="button" onClick={() => navigate(`/futbolchilar/${player.id}`)}>
                  <span className="player-avatar">
                    {player.photo_url ? <img src={player.photo_url} alt={player.full_name} /> : <span>{getPlayerInitials(player.full_name)}</span>}
                  </span>
                  <span className="player-card-header">
                    <strong>{player.full_name}</strong>
                    <span className="player-meta-line">
                      <span className={`position-pill position-${player.position}`}>{player.position_display}</span>
                      <span className="player-age">{player.age} yosh</span>
                    </span>
                    <span className="small muted">{player.short_note || player.nationality}</span>
                  </span>
                </button>

                <div className="player-attendance">
                  <div className="profile-row" style={{ justifyContent: 'space-between' }}>
                    <span className="small muted">Qatnashuv</span>
                    <strong>{player.attendance_percent}%</strong>
                  </div>
                  <Progress value={player.attendance_percent} />
                </div>

                <div className="mini-stats three-col">
                  <div className="mini-stat-block">
                    <Trophy size={18} />
                    <strong>{player.game_statistics?.matches_played || 0}</strong>
                    <span>O'yin</span>
                  </div>
                  <div className="mini-stat-block">
                    <Activity size={18} />
                    <strong>{player.game_statistics?.goals || 0}</strong>
                    <span>Gol</span>
                  </div>
                  <div className="mini-stat-block">
                    <ClipboardList size={18} />
                    <strong>{player.game_statistics?.assists || 0}</strong>
                    <span>Assist</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="Futbolchi topilmadi" text="Qidiruv yoki filtrni o'zgartiring." />
        )}
      </div>
      {(creating || editing) && (
        <Modal title={editing ? 'Futbolchini tahrirlash' : "Futbolchi qo'shish"} onClose={() => { setCreating(false); setEditing(null); }}>
          <PlayerForm initial={editing || playerFormDefaults()} onSubmit={save} onCancel={() => { setCreating(false); setEditing(null); }} />
        </Modal>
      )}
      {deleting && (
        <ConfirmModal
          title="Futbolchini o'chirish"
          text={`${deleting.full_name} ma'lumotlari o'chiriladi. Davom etasizmi?`}
          onCancel={() => setDeleting(null)}
          onConfirm={remove}
        />
      )}
    </Layout>
  );
}


function trainingFormDefaults(): Partial<Training> {
  return {
    title: '',
    training_type: 'tactics',
    training_date: today(),
    start_time: '09:00',
    end_time: '11:00',
    location: 'Asosiy maydon',
    note: '',
  };
}

function TrainingForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial: Partial<Training>;
  onSubmit: (data: Partial<Training>) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<Partial<Training>>(initial);
  const set = (key: keyof Training, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        <Field label="Mashg'ulot nomi">
          <input className="input" required value={form.title || ''} onChange={(event) => set('title', event.target.value)} />
        </Field>
        <Field label="Turi">
          <select className="select" required value={form.training_type || 'tactics'} onChange={(event) => set('training_type', event.target.value)}>
            {trainingTypes.filter((item) => item.value).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </Field>
        <Field label="Sana">
          <input className="input" type="date" required value={form.training_date || today()} onChange={(event) => set('training_date', event.target.value)} />
        </Field>
        <Field label="Boshlanish vaqti">
          <input className="input" type="time" required value={formatTime(form.start_time)} onChange={(event) => set('start_time', event.target.value)} />
        </Field>
        <Field label="Tugash vaqti">
          <input className="input" type="time" required value={formatTime(form.end_time)} onChange={(event) => set('end_time', event.target.value)} />
        </Field>
        <Field label="Joy">
          <input className="input" required value={form.location || ''} onChange={(event) => set('location', event.target.value)} />
        </Field>
        <Field label="Reja va izoh" wide>
          <textarea className="textarea" value={form.note || ''} onChange={(event) => set('note', event.target.value)} />
        </Field>
      </div>
      <div className="form-actions">
        <button className="button ghost" type="button" onClick={onCancel}>Bekor qilish</button>
        <button className="button primary"><Save size={18} /> Saqlash</button>
      </div>
    </form>
  );
}


function TrainingDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const [training, setTraining] = useState<Training | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [editingRecord, setEditingRecord] = useState<AttendanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const data = await trainingsAPI.attendance(Number(id));
      setTraining(data.training);
      setRecords(data.records);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const updateEditingRecord = (key: keyof AttendanceRecord, value: string | number | null) => {
    setEditingRecord((current) => (current ? { ...current, [key]: value } : current));
  };

  const numberOrNull = (value: string) => (value === '' ? null : Number(value));
  const decimalOrNull = (value: string) => (value === '' ? null : value);

  const changeAttendanceStatus = (value: string) => {
    setEditingRecord((current) => {
      if (!current) return current;
      if (value === 'Qatnashmadi') {
        return {
          ...current,
          attendance_status: value,
          attended_minutes: 0,
          fatigue_level: 1,
          pain_level: 1,
          sleep_quality: 7,
          heart_rate: null,
          blood_pressure: '',
          body_temperature: null,
          measured_weight: null,
          measured_height: null,
          oxygen_saturation: null,
          respiratory_rate: null,
        };
      }
      return {
        ...current,
        attendance_status: value,
        attended_minutes: current.attended_minutes || current.training_duration_minutes || 90,
      };
    });
  };

  const changeInjuryStatus = (value: string) => {
    setEditingRecord((current) => {
      if (!current) return current;
      return {
        ...current,
        injury_status: value,
        injury_note: value === "Yo'q" ? '' : current.injury_note,
      };
    });
  };

  const openEditingRecord = (record: AttendanceRecord) => {
    setEditingRecord({
      ...record,
      attendance_status: record.attendance_status === 'Qatnashdi' ? 'Qatnashdi' : 'Qatnashmadi',
    });
  };

  const normalizeAttendanceRecord = (record: AttendanceRecord): AttendanceRecord => {
    const isActive = record.attendance_status === 'Qatnashdi';
    return {
      ...record,
      attendance_status: isActive ? 'Qatnashdi' : 'Qatnashmadi',
      attended_minutes: isActive ? record.attended_minutes : 0,
      fatigue_level: isActive ? record.fatigue_level || 1 : 1,
      pain_level: isActive ? record.pain_level || 1 : 1,
      sleep_quality: isActive ? record.sleep_quality || 7 : 7,
      heart_rate: isActive ? record.heart_rate : null,
      blood_pressure: isActive ? record.blood_pressure || '' : '',
      body_temperature: isActive ? record.body_temperature : null,
      measured_weight: isActive ? record.measured_weight : null,
      measured_height: isActive ? record.measured_height : null,
      oxygen_saturation: isActive ? record.oxygen_saturation : null,
      respiratory_rate: isActive ? record.respiratory_rate : null,
      injury_note: record.injury_status === "Yo'q" ? '' : record.injury_note || '',
      rating: record.rating || 7,
      activity_score: record.activity_score || 7,
    };
  };

  const saveEditingRecord = async () => {
    if (!id || !editingRecord) return;
    if (editingRecord.injury_status !== "Yo'q" && !editingRecord.injury_note?.trim()) {
      notify('Jarohat bor bo‘lsa tavsif yozing.', 'error');
      return;
    }
    setSaving(true);
    try {
      const nextRecords = records.map((record) => normalizeAttendanceRecord(record.player === editingRecord.player ? editingRecord : record));
      const saved = await trainingsAPI.saveAttendance(Number(id), nextRecords);
      setRecords(saved);
      const refreshed = await trainingsAPI.attendance(Number(id));
      setTraining(refreshed.training);
      setRecords(refreshed.records);
      setEditingRecord(null);
      notify(`${editingRecord.player_detail.full_name} holati saqlandi va statistika yangilandi.`);
    } catch (err) {
      notify(getApiError(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Layout><div className="loading-state">Yuklanmoqda...</div></Layout>;
  if (error) return <Layout><ErrorState text={error} retry={load} /></Layout>;
  if (!training) return <Layout><EmptyState title="Mashg'ulot topilmadi" /></Layout>;

  const isEditingActive = editingRecord?.attendance_status === 'Qatnashdi';
  const showInjuryNote = editingRecord?.injury_status === 'Bor' || editingRecord?.injury_status === 'Tiklanmoqda';

  return (
    <Layout>
      <PageHeader
        title={training.title}
        description={`${formatDate(training.training_date)} | ${formatTime(training.start_time)} - ${formatTime(training.end_time)} | ${training.location}`}
        action={
          <div className="toolbar">
            <button className="button ghost" onClick={() => navigate('/mashgulotlar')}><ArrowLeft size={18} /> Orqaga qaytish</button>
            <button className="button ghost" onClick={load}><RefreshCw size={18} /> Yangilash</button>
          </div>
        }
      />
      <div className="grid grid-4">
        <StatCard icon={Users} label="Belgilanganlar" value={training.attendance_total} />
        <StatCard icon={Check} label="Kelganlar" value={training.attendance_present} tone="green" />
        <StatCard icon={Activity} label="Qatnashuv" value={`${training.attendance_percent}%`} />
        <StatCard icon={BarChart3} label="O'rtacha baho" value={training.average_rating || 0} tone="yellow" />
      </div>
      <div className="card" style={{ marginTop: 18 }}>
        <div className="card-header">
          <h2 className="card-title">Futbolchilar holati</h2>
          <span className="badge blue">{records.length} ta yozuv</span>
        </div>
        <div className="table-wrap">
          <table className="table" style={{ minWidth: 1120 }}>
            <thead>
              <tr>
                <th>Futbolchi</th>
                <th>Qatnashuv</th>
                <th>Jismoniy holat</th>
                <th>Faollik</th>
                <th>Intizom</th>
                <th>Baho</th>
                <th>Jarohat</th>
                <th>Murabbiy izohi</th>
                <th>Amal</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.player} onClick={() => openEditingRecord(record)} style={{ cursor: 'pointer' }}>
                  <td>
                    <div className="profile-row">
                      <img className="avatar" src={record.player_detail.photo_url} alt={record.player_detail.full_name} />
                      <div>
                        <strong>#{record.player_detail.shirt_number} {record.player_detail.full_name}</strong>
                        <div className="small muted">{record.player_detail.position_display}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge ${record.attendance_status === 'Qatnashdi' ? 'green' : 'red'}`}>{record.attendance_status_display}</span></td>
                  <td>{record.physical_condition_display}</td>
                  <td>{record.activity_level_display}</td>
                  <td>{record.discipline_display}</td>
                  <td><strong>{record.rating}/10</strong></td>
                  <td><span className={`badge ${record.injury_status === 'Bor' ? 'red' : record.injury_status === 'Tiklanmoqda' ? 'yellow' : 'green'}`}>{record.injury_status_display}</span></td>
                  <td>{record.coach_note || record.injury_note || '-'}</td>
                  <td>
                    <button
                      className="button icon ghost"
                      title="Tahrirlash"
                      onClick={(event) => {
                        event.stopPropagation();
                        openEditingRecord(record);
                      }}
                    >
                      <Edit size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {editingRecord && (
        <Modal
          title={`${editingRecord.player_detail.full_name} holatini tahrirlash`}
          onClose={() => setEditingRecord(null)}
          action={
            <button className="button primary" onClick={saveEditingRecord} disabled={saving}>
              <Save size={18} /> {saving ? 'Saqlanmoqda...' : 'Saqlash'}
            </button>
          }
        >
          <div className="attendance-modal-profile">
            <img className="avatar" src={editingRecord.player_detail.photo_url} alt={editingRecord.player_detail.full_name} />
            <div>
              <strong>#{editingRecord.player_detail.shirt_number} {editingRecord.player_detail.full_name}</strong>
              <div className="small muted">{editingRecord.player_detail.position_display}</div>
            </div>
            <span className={`badge ${isEditingActive ? 'green' : 'red'}`}>{isEditingActive ? 'Keldi' : 'Qatnashmadi'}</span>
          </div>
          <div className="medical-modal-grid">
            <section className="medical-section">
              <div className="medical-section-head">
                <span>1</span>
                <div>
                  <h3>Qatnashuv</h3>
                  <p>Futbolchining mashg'ulotdagi ishtiroki va davomiyligi.</p>
                </div>
              </div>
              <div className="form-grid">
                <Field label="Qatnashuv holati">
                  <select className="select" value={editingRecord.attendance_status} onChange={(event) => changeAttendanceStatus(event.target.value)}>
                    {attendanceStatuses.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                </Field>
                <Field label="Qatnashgan daqiqa">
                  <input
                    className="input"
                    type="number"
                    min={0}
                    max={editingRecord.training_duration_minutes}
                    disabled={!isEditingActive}
                    value={editingRecord.attended_minutes}
                    onChange={(event) => updateEditingRecord('attended_minutes', Number(event.target.value))}
                  />
                </Field>
              </div>
            </section>

            {isEditingActive && (
              <>
                <section className="medical-section">
                  <div className="medical-section-head">
                    <span>2</span>
                    <div>
                      <h3>Jismoniy holat</h3>
                      <p>Holat, intizom va subyektiv charchoq ko'rsatkichlari.</p>
                    </div>
                  </div>
                  <div className="form-grid">
                    <Field label="Jismoniy holat">
                      <select className="select" value={editingRecord.physical_condition} onChange={(event) => updateEditingRecord('physical_condition', event.target.value)}>
                        {physicalConditions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </Field>
                    <Field label="Faollik holati">
                      <select className="select" value={editingRecord.activity_level} onChange={(event) => updateEditingRecord('activity_level', event.target.value)}>
                        {activityLevels.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </Field>
                    <Field label="Intizom">
                      <select className="select" value={editingRecord.discipline} onChange={(event) => updateEditingRecord('discipline', event.target.value)}>
                        {disciplineChoices.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </Field>
                    <Field label="Charchoq darajasi">
                      <input className="input" type="number" min={1} max={10} value={editingRecord.fatigue_level} onChange={(event) => updateEditingRecord('fatigue_level', Number(event.target.value))} />
                    </Field>
                    <Field label="Og'riq darajasi">
                      <input className="input" type="number" min={1} max={10} value={editingRecord.pain_level} onChange={(event) => updateEditingRecord('pain_level', Number(event.target.value))} />
                    </Field>
                    <Field label="Uyqu sifati">
                      <input className="input" type="number" min={1} max={10} value={editingRecord.sleep_quality} onChange={(event) => updateEditingRecord('sleep_quality', Number(event.target.value))} />
                    </Field>
                  </div>
                </section>

                <section className="medical-section">
                  <div className="medical-section-head">
                    <span>3</span>
                    <div>
                      <h3>Tibbiy ko'rsatkichlar</h3>
                      <p>Yurak urishi, qon bosimi, harorat va nafas olish ko'rsatkichlari.</p>
                    </div>
                  </div>
                  <div className="form-grid">
                    <Field label="Yurak urishi (bpm)">
                      <input className="input" type="number" min={30} max={240} value={editingRecord.heart_rate ?? ''} onChange={(event) => updateEditingRecord('heart_rate', numberOrNull(event.target.value))} />
                    </Field>
                    <Field label="Qon bosimi">
                      <input className="input" placeholder="120/80" value={editingRecord.blood_pressure || ''} onChange={(event) => updateEditingRecord('blood_pressure', event.target.value)} />
                    </Field>
                    <Field label="Tana harorati">
                      <input className="input" type="number" step="0.1" value={editingRecord.body_temperature ?? ''} onChange={(event) => updateEditingRecord('body_temperature', decimalOrNull(event.target.value))} />
                    </Field>
                    <Field label="Kislorod (%)">
                      <input className="input" type="number" min={50} max={100} value={editingRecord.oxygen_saturation ?? ''} onChange={(event) => updateEditingRecord('oxygen_saturation', numberOrNull(event.target.value))} />
                    </Field>
                    <Field label="Nafas olish (marta/min)">
                      <input className="input" type="number" min={5} max={80} value={editingRecord.respiratory_rate ?? ''} onChange={(event) => updateEditingRecord('respiratory_rate', numberOrNull(event.target.value))} />
                    </Field>
                    <Field label="Vazn (kg)">
                      <input className="input" type="number" step="0.1" value={editingRecord.measured_weight ?? ''} onChange={(event) => updateEditingRecord('measured_weight', decimalOrNull(event.target.value))} />
                    </Field>
                    <Field label="Bo'y (sm)">
                      <input className="input" type="number" min={80} max={230} value={editingRecord.measured_height ?? ''} onChange={(event) => updateEditingRecord('measured_height', numberOrNull(event.target.value))} />
                    </Field>
                  </div>
                </section>
              </>
            )}

            <section className="medical-section">
              <div className="medical-section-head">
                <span>4</span>
                <div>
                  <h3>Jarohat va izohlar</h3>
                  <p>Jarohat tavsifi faqat jarohat bor yoki tiklanmoqda holatida kiritiladi.</p>
                </div>
              </div>
              <div className="form-grid">
                <Field label="Jarohat holati">
                  <select className="select" value={editingRecord.injury_status} onChange={(event) => changeInjuryStatus(event.target.value)}>
                    {injuryStatuses.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                </Field>
                {showInjuryNote && (
                  <Field label="Jarohat tavsifi">
                    <input className="input" value={editingRecord.injury_note || ''} onChange={(event) => updateEditingRecord('injury_note', event.target.value)} />
                  </Field>
                )}
                <Field label="Murabbiy izohi" wide>
                  <textarea className="textarea" value={editingRecord.coach_note || ''} onChange={(event) => updateEditingRecord('coach_note', event.target.value)} />
                </Field>
              </div>
            </section>
          </div>
        </Modal>
      )}
    </Layout>
  );
}

function matchFormDefaults(): Partial<Match> {
  return {
    home_team: PROJECT_CLUB_NAME,
    away_team: '',
    home_logo_url: '',
    away_logo_url: '',
    match_date: today(),
    match_time: '18:00',
    stadium: 'Asosiy stadion',
    status: 'upcoming',
    home_score: null,
    away_score: null,
    attendance: null,
    referee: '',
    possession_percent: 50,
    shots: 0,
    shots_on_target: 0,
    corners: 0,
    yellow_cards: 0,
    red_cards: 0,
    note: '',
  };
}

function MatchForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial: Partial<Match>;
  onSubmit: (data: Partial<Match>) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<Partial<Match>>(initial);
  const set = (key: keyof Match, value: string | number | null) => setForm((current) => ({ ...current, [key]: value }));

  const numberOrNull = (value: string) => (value === '' ? null : Number(value));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      ...form,
      home_score: numberOrNull(String(form.home_score ?? '')),
      away_score: numberOrNull(String(form.away_score ?? '')),
      attendance: numberOrNull(String(form.attendance ?? '')),
      possession_percent: Number(form.possession_percent || 0),
      shots: Number(form.shots || 0),
      shots_on_target: Number(form.shots_on_target || 0),
      corners: Number(form.corners || 0),
      yellow_cards: Number(form.yellow_cards || 0),
      red_cards: Number(form.red_cards || 0),
    });
  };

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        <Field label="Bizning jamoa">
          <input className="input" required value={form.home_team || ''} onChange={(event) => set('home_team', event.target.value)} />
        </Field>
        <Field label="Raqib jamoa">
          <input className="input" required value={form.away_team || ''} onChange={(event) => set('away_team', event.target.value)} />
        </Field>
        <Field label="Uy jamoa logo URL">
          <input className="input" type="url" value={form.home_logo_url || ''} onChange={(event) => set('home_logo_url', event.target.value)} />
        </Field>
        <Field label="Mehmon jamoa logo URL">
          <input className="input" type="url" value={form.away_logo_url || ''} onChange={(event) => set('away_logo_url', event.target.value)} />
        </Field>
        <Field label="Sana">
          <input className="input" type="date" required value={form.match_date || today()} onChange={(event) => set('match_date', event.target.value)} />
        </Field>
        <Field label="Vaqt">
          <input className="input" type="time" required value={formatTime(form.match_time)} onChange={(event) => set('match_time', event.target.value)} />
        </Field>
        <Field label="Joy">
          <input className="input" required value={form.stadium || ''} onChange={(event) => set('stadium', event.target.value)} />
        </Field>
        <Field label="Holat">
          <select className="select" value={form.status || 'upcoming'} onChange={(event) => set('status', event.target.value)}>
            {matchStatuses.filter((item) => item.value).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </Field>
        <Field label="Bizning hisob">
          <input className="input" type="number" min={0} value={form.home_score ?? ''} onChange={(event) => set('home_score', numberOrNull(event.target.value))} />
        </Field>
        <Field label="Raqib hisob">
          <input className="input" type="number" min={0} value={form.away_score ?? ''} onChange={(event) => set('away_score', numberOrNull(event.target.value))} />
        </Field>
        <Field label="Tomoshabin">
          <input className="input" type="number" min={0} value={form.attendance ?? ''} onChange={(event) => set('attendance', numberOrNull(event.target.value))} />
        </Field>
        <Field label="Hakam">
          <input className="input" value={form.referee || ''} onChange={(event) => set('referee', event.target.value)} />
        </Field>
        <Field label="To'p nazorati, %">
          <input className="input" type="number" min={0} max={100} value={form.possession_percent || 0} onChange={(event) => set('possession_percent', Number(event.target.value))} />
        </Field>
        <Field label="Zarbalar">
          <input className="input" type="number" min={0} value={form.shots || 0} onChange={(event) => set('shots', Number(event.target.value))} />
        </Field>
        <Field label="Aniq zarbalar">
          <input className="input" type="number" min={0} value={form.shots_on_target || 0} onChange={(event) => set('shots_on_target', Number(event.target.value))} />
        </Field>
        <Field label="Burchak zarbalari">
          <input className="input" type="number" min={0} value={form.corners || 0} onChange={(event) => set('corners', Number(event.target.value))} />
        </Field>
        <Field label="Sariq kartochka">
          <input className="input" type="number" min={0} value={form.yellow_cards || 0} onChange={(event) => set('yellow_cards', Number(event.target.value))} />
        </Field>
        <Field label="Qizil kartochka">
          <input className="input" type="number" min={0} value={form.red_cards || 0} onChange={(event) => set('red_cards', Number(event.target.value))} />
        </Field>
        <Field label="O'yin izohi" wide>
          <textarea className="textarea" value={form.note || ''} onChange={(event) => set('note', event.target.value)} />
        </Field>
      </div>
      <div className="form-actions">
        <button className="button ghost" type="button" onClick={onCancel}>Bekor qilish</button>
        <button className="button primary"><Save size={18} /> Saqlash</button>
      </div>
    </form>
  );
}

function getTeamInitials(teamName: string) {
  return teamName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

const LOCAL_TEAM_LOGOS: Record<string, string> = {
  paxtakor: '/team-logos/pakhtakor.png',
  nasaf: '/team-logos/nasaf.png',
  navbahor: '/team-logos/navbahor.png',
  neftchi: '/team-logos/neftchi.png',
  okmk: '/team-logos/okmk.png',
  bunyodkor: '/team-logos/bunyodkor.png',
  "so'g'diyona": '/team-logos/sogdiyona.png',
  sogdiyona: '/team-logos/sogdiyona.png',
  qizilqum: '/team-logos/qizilqum.png',
  surxon: '/team-logos/surxon.png',
  andijon: '/team-logos/andijon.png',
  metallurg: '/team-logos/metallurg.png',
  dinamo: '/team-logos/dinamo.png',
  lokomotiv: '/team-logos/lokomotiv.png',
  "mash'al": '/team-logos/mashal.png',
  mashal: '/team-logos/mashal.png',
  "sho'rtan": '/team-logos/shortan.png',
  shortan: '/team-logos/shortan.png',
  "qo'qon-1912": '/team-logos/qoqon-1912.png',
  'qoqon-1912': '/team-logos/qoqon-1912.png',
  xorazm: '/team-logos/xorazm.png',
};

function normalizeTeamLogoKey(teamName: string) {
  return teamName
    .trim()
    .toLocaleLowerCase('uz-UZ')
    .replace(/[ʻʼ’`]/g, "'")
    .replace(/\s+/g, ' ');
}

function getTeamLogoUrl(teamName: string, logoUrl?: string) {
  const localLogo = LOCAL_TEAM_LOGOS[normalizeTeamLogoKey(teamName)];
  if (localLogo) return localLogo;
  if (logoUrl?.includes('google.com/s2/favicons')) return undefined;
  return logoUrl;
}

function TeamLogo({ teamName, logoUrl, size = 'md' }: { teamName: string; logoUrl?: string; size?: 'sm' | 'md' | 'lg' }) {
  const [failed, setFailed] = useState(false);
  const sizeClass = `avatar-${size}`;
  const resolvedLogoUrl = getTeamLogoUrl(teamName, logoUrl);
  useEffect(() => {
    setFailed(false);
  }, [resolvedLogoUrl]);

  return (
    <div className={`avatar ${sizeClass}`} style={{ background: '#e0e7ff', color: '#4f46e5', fontWeight: 600, fontSize: '0.875rem' }}>
      {resolvedLogoUrl && !failed ? (
        <img src={resolvedLogoUrl} alt={teamName} onError={() => setFailed(true)} style={{ width: '100%', height: '100%', objectFit: 'contain', padding: 2 }} />
      ) : (
        <span>{getTeamInitials(teamName)}</span>
      )}
    </div>
  );
}

type MatchResultLabel = "G'alaba" | 'Durang' | "Mag'lubiyat" | 'Rejalashtirilgan';

function isProjectClubTeam(teamName: string) {
  return normalizeTeamLogoKey(teamName) === normalizeTeamLogoKey(PROJECT_CLUB_NAME);
}

function getProjectClubFixture(match: Match) {
  const projectClubIsAway = isProjectClubTeam(match.away_team) && !isProjectClubTeam(match.home_team);

  if (projectClubIsAway) {
    return {
      left: {
        name: match.away_team,
        logoUrl: match.away_logo_url,
        score: match.away_score,
        label: 'Mehmon jamoa',
      },
      right: {
        name: match.home_team,
        logoUrl: match.home_logo_url,
        score: match.home_score,
        label: 'Uy jamoasi',
      },
      leftPossession: 100 - Number(match.possession_percent || 0),
      rightPossession: Number(match.possession_percent || 0),
    };
  }

  return {
    left: {
      name: match.home_team,
      logoUrl: match.home_logo_url,
      score: match.home_score,
      label: 'Uy jamoasi',
    },
    right: {
      name: match.away_team,
      logoUrl: match.away_logo_url,
      score: match.away_score,
      label: 'Mehmon jamoa',
    },
    leftPossession: Number(match.possession_percent || 0),
    rightPossession: 100 - Number(match.possession_percent || 0),
  };
}

function getMatchResultForTeam(match: Match, clubName = PROJECT_CLUB_NAME): MatchResultLabel {
  if (match.home_score === null || match.away_score === null) return 'Rejalashtirilgan';
  if (match.home_score === match.away_score) return 'Durang';
  const clubIsAway = Boolean(clubName && normalizeTeamLogoKey(match.away_team) === normalizeTeamLogoKey(clubName));
  const won = clubIsAway ? match.away_score > match.home_score : match.home_score > match.away_score;
  return won ? "G'alaba" : "Mag'lubiyat";
}

function matchResultTone(label: MatchResultLabel) {
  if (label === "G'alaba") return 'green';
  if (label === "Mag'lubiyat") return 'red';
  if (label === 'Durang') return 'yellow';
  return '';
}

function MatchStatusBadge({ match }: { match: Match }) {
  if (match.status === 'live') {
    return <span className="badge yellow match-live-status"><i /> Jonli</span>;
  }
  if (match.status === 'upcoming') {
    return <span className="badge blue">Kutilmoqda</span>;
  }
  return <span className="match-past-status">Yakunlangan</span>;
}

function MatchScore({ match }: { match: Match }) {
  const fixture = getProjectClubFixture(match);
  if (fixture.left.score === null || fixture.right.score === null) return <span className="match-score-empty">-</span>;
  return <span className="match-score-pill">{fixture.left.score} - {fixture.right.score}</span>;
}

function MatchesPage() {
  const PAGE_SIZE = 7;
  const [matches, setMatches] = useState<Match[]>([]);
  const [stats, setStats] = useState<MatchStats>({ total: 0, wins: 0, draws: 0, losses: 0 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [ordering, setOrdering] = useState('match_date');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const notify = useToast();
  const navigate = useNavigate();

  const filters = { search, status: statusFilter, date: dateFilter, ordering };
  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [matchRows, matchStats] = await Promise.all([matchesAPI.list(filters), matchesAPI.stats(filters)]);
      setMatches(matchRows);
      setStats(matchStats);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
    load();
  }, [search, statusFilter, dateFilter, ordering]);

  const save = async (data: Partial<Match>) => {
    try {
      await matchesAPI.create(data);
      notify("O'yin yaratildi.");
      setCreating(false);
      load();
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  const totalPages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
  const visiblePage = Math.min(page, totalPages);
  const pageMatches = matches.slice((visiblePage - 1) * PAGE_SIZE, visiblePage * PAGE_SIZE);
  const start = matches.length ? (visiblePage - 1) * PAGE_SIZE + 1 : 0;
  const end = Math.min(visiblePage * PAGE_SIZE, matches.length);
  const statusOptions = [
    { value: '', label: 'Hammasi' },
    { value: 'upcoming', label: 'Rejalashtirilgan' },
    { value: 'live', label: 'Jonli' },
    { value: 'played', label: "O'tgan" },
  ];

  return (
    <Layout>
      <PageHeader
        title={<span className="matches-page-title"><Trophy size={26} /> O'yinlar</span>}
        description="Raqib, sana, stadion, hisob va o'yin statistikasi real bazaga saqlanadi."
        action={<button className="button primary" onClick={() => setCreating(true)}><Plus size={18} /> O'yin qo'shish</button>}
      />

      <div className="matches-toolbar">
        <div className="roster-search">
          <Search size={18} />
          <input className="input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Jamoani qidirish..." />
        </div>
        <div className="match-filter-tabs">
          {statusOptions.map((option) => (
            <button className={statusFilter === option.value ? 'active' : ''} key={option.value} type="button" onClick={() => setStatusFilter(option.value)}>
              {option.value === 'live' && <i className="match-live-dot" />}
              {option.label}
            </button>
          ))}
        </div>
        <label className="match-date-sort">
          <CalendarDays size={17} />
          <input className="input" type="date" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} />
        </label>
        <button className="button ghost match-order" type="button" onClick={() => setOrdering((current) => current === '-match_date' ? 'match_date' : '-match_date')}>
          <RefreshCw size={16} /> {ordering === '-match_date' ? 'Yangi avval' : 'Eski avval'}
        </button>
      </div>

      <div className="match-summary-grid">
        <article className="match-summary-card"><strong>{stats.total}</strong><span>Jami o'yin</span></article>
        <article className="match-summary-card win"><strong>{stats.wins}</strong><span>G'alaba</span></article>
        <article className="match-summary-card draw"><strong>{stats.draws}</strong><span>Durang</span></article>
        <article className="match-summary-card loss"><strong>{stats.losses}</strong><span>Mag'lubiyat</span></article>
      </div>

      <div className="card matches-table-card">
        {loading ? (
          <div className="loading-state">Yuklanmoqda...</div>
        ) : error ? (
          <ErrorState text={error} retry={load} />
        ) : matches.length ? (
          <>
            <div className="table-wrap">
              <table className="table matches-table">
                <thead>
                  <tr>
                    <th>O'yin</th>
                    <th>Sana</th>
                    <th>Stadion</th>
                    <th>Hisob</th>
                    <th>Natija</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {pageMatches.map((match) => {
                    const result = getMatchResultForTeam(match);
                    const fixture = getProjectClubFixture(match);
                    return (
                      <tr className="matches-row" key={match.id} onClick={() => navigate(`/oyinlar/${match.id}`)}>
                        <td>
                          <div className="match-fixture">
                            <span className="match-fixture-team">
                              <TeamLogo teamName={fixture.left.name} logoUrl={fixture.left.logoUrl} size="sm" />
                              <strong className="match-fixture-name">{fixture.left.name}</strong>
                            </span>
                            <span className="match-fixture-vs muted">vs</span>
                            <span className="match-fixture-team">
                              <TeamLogo teamName={fixture.right.name} logoUrl={fixture.right.logoUrl} size="sm" />
                              <span className="match-fixture-name">{fixture.right.name}</span>
                            </span>
                          </div>
                        </td>
                        <td>{formatDateShort(match.match_date)}</td>
                        <td>{match.stadium}</td>
                        <td><MatchScore match={match} /></td>
                        <td><span className={`badge ${matchResultTone(result)}`}>{result}</span></td>
                        <td><MatchStatusBadge match={match} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="match-pagination">
              <span>Jami {matches.length} ta o'yin, {start}-{end} ko'rsatilmoqda</span>
              <div>
                <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={visiblePage === 1}>Oldingi</button>
                {Array.from({ length: totalPages }, (_, index) => index + 1).slice(0, 3).map((item) => (
                  <button className={visiblePage === item ? 'active' : ''} key={item} type="button" onClick={() => setPage(item)}>{item}</button>
                ))}
                <button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={visiblePage === totalPages}>Keyingi</button>
              </div>
            </div>
          </>
        ) : (
          <EmptyState title="O'yin topilmadi" text="Birinchi o'yinni qo'shing." />
        )}
      </div>

      {creating && (
        <Modal title="O'yin qo'shish" onClose={() => setCreating(false)}>
          <MatchForm initial={matchFormDefaults()} onSubmit={save} onCancel={() => setCreating(false)} />
        </Modal>
      )}
    </Layout>
  );
}

function MatchDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const [match, setMatch] = useState<Match | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      setMatch(await matchesAPI.detail(Number(id)));
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const save = async (data: Partial<Match>) => {
    if (!match) return;
    try {
      await matchesAPI.update(match.id, data);
      notify("O'yin ma'lumotlari yangilandi.");
      setEditing(false);
      load();
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  if (loading) return <Layout><div className="loading-state">Yuklanmoqda...</div></Layout>;
  if (error) return <Layout><ErrorState text={error} retry={load} /></Layout>;
  if (!match) return <Layout><EmptyState title="O'yin topilmadi" /></Layout>;

  const result = getMatchResultForTeam(match);
  const fixture = getProjectClubFixture(match);
  const pendingMatch = match.status === 'upcoming';
  const detailStat = (value: number | null | undefined) => (pendingMatch ? '-' : value || 0);
  const shotAccuracy = pendingMatch
    ? '-'
    : match.shots
      ? `${Math.round((Number(match.shots_on_target || 0) / Number(match.shots)) * 100)}%`
      : '0%';
  const attackIndex = pendingMatch
    ? '-'
    : percent(Math.round((Number(match.shots || 0) * 4 + Number(match.shots_on_target || 0) * 7 + Number(match.corners || 0) * 5) / 1.8));

  return (
    <Layout>
      <div className="match-detail-page">
        <PageHeader
          title={<span className="match-detail-title"><button className="button ghost match-back-button" onClick={() => navigate('/oyinlar')}><ArrowLeft size={15} /> Orqaga</button> <span>O'yin tafsiloti</span></span>}
          action={<button className="button ghost match-edit-button" onClick={() => setEditing(true)}><Edit size={17} /> Tahrirlash</button>}
        />

        <section className="card match-header-card">
          <div className="match-team">
            <TeamLogo teamName={fixture.left.name} logoUrl={fixture.left.logoUrl} size="lg" />
            <strong>{fixture.left.name}</strong>
            <span>{fixture.left.label}</span>
          </div>
          <div className="match-scoreboard">
            <strong>{fixture.left.score ?? '-'} - {fixture.right.score ?? '-'}</strong>
            <span className={`badge ${matchResultTone(result)}`}>{result}</span>
          </div>
          <div className="match-team">
            <TeamLogo teamName={fixture.right.name} logoUrl={fixture.right.logoUrl} size="lg" />
            <strong>{fixture.right.name}</strong>
            <span>{fixture.right.label}</span>
          </div>
          <div className="match-meta-line">
            <span><CalendarDays size={15} /> {formatDate(match.match_date)}</span>
            <span><Clock size={15} /> {formatTime(match.match_time)}</span>
            <span><MapPin size={15} /> {match.stadium}</span>
            <span><Users size={15} /> {match.attendance ? Number(match.attendance).toLocaleString() : '-'} tomoshabin</span>
            <span><UserRound size={15} /> {match.referee || '-'}</span>
          </div>
        </section>

        <div className="match-detail-stats">
          <article className="match-summary-card"><strong>{detailStat(match.shots)}</strong><span>Zarba soni</span></article>
          <article className="match-summary-card"><strong>{detailStat(match.shots_on_target)}</strong><span>Darvozaga zarba</span></article>
          <article className="match-summary-card"><strong>{detailStat(match.corners)}</strong><span>Burchak zarbalari</span></article>
          <article className="match-summary-card draw"><strong>{detailStat(match.yellow_cards)}</strong><span>Sariq karta</span></article>
        </div>

        <div className="grid match-extra-grid">
          <section className="card match-facts">
            <h2 className="card-title">Qo'shimcha info</h2>
            <p><span>Qizil karta</span><strong>{detailStat(match.red_cards)}</strong></p>
            <p><span>Hakam</span><strong>{match.referee || '-'}</strong></p>
            <p><span>Tomoshabin</span><strong>{match.attendance ? Number(match.attendance).toLocaleString() : '-'}</strong></p>
          </section>
          <section className="card match-possession">
            <h2 className="card-title">To'p egallash</h2>
            <div className="match-possession-row"><strong>{fixture.leftPossession}%</strong><span>{fixture.left.name}</span><span>{fixture.right.name}</span><strong>{fixture.rightPossession}%</strong></div>
            <div className="match-possession-track"><i style={{ width: `${fixture.leftPossession}%` }} /></div>
            <div className="match-possession-mini">
              <span><b>{detailStat(match.shots_on_target)}</b> Aniq zarba</span>
              <span><b>{shotAccuracy}</b> Aniqlik</span>
              <span><b>{attackIndex}</b> Hujum indeksi</span>
            </div>
          </section>
        </div>

        {match.note && (
          <section className="card match-note-card">
            <h2 className="card-title">Murabbiy izohi</h2>
            <p>{match.note}</p>
          </section>
        )}
      </div>

      {editing && (
        <Modal title="O'yinni tahrirlash" onClose={() => setEditing(false)}>
          <MatchForm initial={match} onSubmit={save} onCancel={() => setEditing(false)} />
        </Modal>
      )}
    </Layout>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="profile-row" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>
      <Progress value={value} />
    </div>
  );
}

function StatisticsAttendanceChart({ rows }: { rows: AttendanceTrendPoint[] }) {
  const maxTotal = Math.max(1, ...rows.map((row) => row.total));
  const averagePercent = rows.length
    ? Math.round(rows.reduce((sum, row) => sum + (row.total ? (row.present / row.total) * 100 : 0), 0) / rows.length)
    : 0;
  const bestPoint = rows.reduce<AttendanceTrendPoint | null>((best, row) => {
    if (!best) return row;
    const bestPercent = best.total ? best.present / best.total : 0;
    const rowPercent = row.total ? row.present / row.total : 0;
    return rowPercent > bestPercent ? row : best;
  }, null);
  const latestPoint = rows[rows.length - 1];
  const formatChartDate = (value: string) => {
    return formatDateShort(value);
  };

  return (
    <section className="card statistics-chart-card">
      <h2>Davomad dinamikasi</h2>
      {rows.length ? (
        <div className="attendance-insight">
          <div className="attendance-insight-summary" aria-label="Davomad xulosasi">
            <span>
              <strong>{averagePercent}%</strong>
              <small>o'rtacha davomad</small>
            </span>
            <span>
              <strong>{latestPoint?.present ?? 0}/{latestPoint?.total ?? 0}</strong>
              <small>oxirgi mashg'ulot</small>
            </span>
            <span>
              <strong>{bestPoint ? `${bestPoint.present}/${bestPoint.total}` : '0/0'}</strong>
              <small>eng yaxshi kun</small>
            </span>
          </div>

          <div className="attendance-column-chart" role="img" aria-label="Qatnashganlar soni bo'yicha ustunli grafik">
            <div className="attendance-y-axis" aria-hidden="true">
              <span>{maxTotal}</span>
              <span>{Math.round(maxTotal / 2)}</span>
              <span>0</span>
            </div>
            <div className="attendance-plot">
              <span className="attendance-grid-line top" />
              <span className="attendance-grid-line middle" />
              <span className="attendance-grid-line bottom" />
              {rows.map((row, index) => {
                const totalHeight = Math.max(8, (row.total / maxTotal) * 100);
                const presentHeight = row.total ? Math.max(6, (row.present / row.total) * totalHeight) : 0;
                const percent = row.total ? Math.round((row.present / row.total) * 100) : 0;
                return (
                  <div
                    className="attendance-bar-group"
                    key={`${row.date}-${index}`}
                    style={{
                      '--total-height': `${totalHeight}%`,
                      '--present-height': `${presentHeight}%`,
                    } as CSSProperties}
                    title={`${formatChartDate(row.date)}: ${row.present}/${row.total} (${percent}%)`}
                  >
                    <strong>{row.present}</strong>
                    <span className="attendance-bar-shell">
                      <span className="attendance-bar-fill" />
                    </span>
                    <small>{formatChartDate(row.date)}</small>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="statistics-legend"><i className="blue" /> Qatnashganlar soni <i className="muted" /> Jami ro'yxat</p>
        </div>
      ) : (
        <EmptyState title="Davomad dinamikasi yo'q" />
      )}
    </section>
  );
}

function StatisticsGoalsChart({ rows }: { rows: GoalAssistPoint[] }) {
  const maxValue = Math.max(1, ...rows.flatMap((row) => [row.goals, row.assists]));
  const chartWidth = Math.max(300, rows.length * 58 + 42);
  const chartHeight = 210;
  const left = 28;
  const right = chartWidth - 14;
  const top = 28;
  const bottom = 164;
  const width = rows.length ? (right - left) / rows.length : 0;
  const barHeight = (value: number) => (value / maxValue) * 112;

  return (
    <section className="card statistics-chart-card">
      <h2>Gol va assist taqqoslash</h2>
      {rows.length ? (
        <>
          <div className="statistics-chart-scroll">
            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img" aria-label="Gol va assist taqqoslash" style={{ width: `${chartWidth}px` }}>
              {[0, 1, 2, 3].map((item) => {
                const y = top + ((bottom - top) / 3) * item;
                const label = Math.round(maxValue - (maxValue / 3) * item);
                return <g key={item}><line x1={left} x2={right} y1={y} y2={y} /><text x="6" y={y + 3}>{label}</text></g>;
              })}
              {rows.map((row, index) => {
                const center = left + width * index + width / 2;
                const goalHeight = barHeight(row.goals);
                const assistHeight = barHeight(row.assists);
                return (
                  <g key={row.player_id}>
                    <rect className="statistics-goal-bar" x={center - 16} y={bottom - goalHeight} width="13" height={goalHeight} rx="3" />
                    <rect className="statistics-assist-bar" x={center + 4} y={bottom - assistHeight} width="13" height={assistHeight} rx="3" />
                    {row.goals > 0 && <text className="statistics-goal-value" x={center - 9.5} y={bottom - goalHeight - 7}>{row.goals}</text>}
                    {row.assists > 0 && <text className="statistics-assist-value" x={center + 10.5} y={bottom - assistHeight - 7}>{row.assists}</text>}
                    <text x={center} y="194">{row.player_name.split(' ')[0]}</text>
                  </g>
                );
              })}
            </svg>
          </div>
          <p className="statistics-legend"><i className="green" /> Gol <i className="yellow" /> Assist</p>
        </>
      ) : (
        <EmptyState title="Gol va assist ma'lumoti yo'q" />
      )}
    </section>
  );
}

function StatisticsRankingCard({
  title,
  rows,
  mode,
}: {
  title: string;
  rows: StatisticsPlayerRow[];
  mode: 'attendance' | 'rating';
}) {
  return (
    <section className="card statistics-ranking-card">
      <h2>{title}</h2>
      <div>
        {rows.length ? rows.map((row, index) => {
          const value = mode === 'attendance' ? row.attendance_percent : Math.min((row.avg_rating / 10) * 100, 100);
          return (
            <article key={row.player_id}>
              <span className={index < 2 ? 'rank hot' : 'rank'}>{index + 1}</span>
              <span className="statistics-initials">{row.initials}</span>
              <strong>{row.short_name}</strong>
              <span className="statistics-rank-track"><i style={{ width: `${value}%` }} /></span>
              <b>{mode === 'attendance' ? `${row.present}/${row.total}` : row.avg_rating}</b>
            </article>
          );
        }) : <EmptyState title="Reyting uchun ma'lumot yo'q" />}
      </div>
    </section>
  );
}

function StatisticsPage() {
  type StatisticsPeriod = 'week' | 'month' | 'season';
  const [period, setPeriod] = useState<StatisticsPeriod>('season');
  const [summary, setSummary] = useState<StatisticsData | null>(null);
  const [trend, setTrend] = useState<AttendanceTrendPoint[]>([]);
  const [goals, setGoals] = useState<GoalAssistPoint[]>([]);
  const [rankings, setRankings] = useState<StatisticsRankings>({ most_present: [], top_rated: [] });
  const [players, setPlayers] = useState<StatisticsPlayerRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, trendData, goalsData, rankingData, playerData] = await Promise.all([
        statisticsAPI.get(period),
        statisticsAPI.attendanceTrend(period),
        statisticsAPI.goalsAssists(period),
        statisticsAPI.rankings(period),
        statisticsAPI.players(period),
      ]);
      setSummary(statsData);
      setTrend(trendData);
      setGoals(goalsData);
      setRankings(rankingData);
      setPlayers(playerData);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [period]);

  if (loading) return <Layout><div className="loading-state">Yuklanmoqda...</div></Layout>;
  if (error) return <Layout><ErrorState text={error} retry={load} /></Layout>;
  if (!summary?.summary) return <Layout><EmptyState title="Statistika topilmadi" /></Layout>;

  const data = summary.summary;
  const pastLabel = period === 'week' ? "o'tgan haftadan" : period === 'season' ? "o'tgan mavsumdan" : "o'tgan oydan";
  const trendMark = (value: number) => value > 0 ? 'up' : value < 0 ? 'down' : 'flat';
  const trendCopy = (value: number, suffix = '') => value ? `${value > 0 ? '↑' : '↓'} ${Math.abs(value)}${suffix} ${pastLabel}` : `- ${pastLabel}`;
  const positionCode = (position: string) => ({
    forward: 'Hujumchi',
    midfielder: 'Yarim himoyachi',
    defender: 'Himoyachi',
    goalkeeper: 'Darvozabon',
  }[position] || position);
  const periodOptions: Array<{ value: StatisticsPeriod; label: string }> = [
    { value: 'week', label: 'Bu hafta' },
    { value: 'month', label: 'Bu oy' },
    { value: 'season', label: 'Bu mavsum' },
  ];
  const cards = [
    { label: "O'rtacha davomad", value: `${data.attendance_percent}%`, note: `${data.trainings_count} mashg'ulot`, trend: data.trends.attendance, suffix: '%' },
    { label: "O'rtacha baho", value: data.average_rating, note: 'Qatnashganlar bahosi', trend: data.trends.rating, suffix: '' },
    { label: "O'rtacha faollik", value: data.average_activity, note: 'Qatnashganlar orasida', trend: data.trends.activity, suffix: '' },
    { label: 'Jarohatlar', value: data.injury_count, note: 'Hozir jarohatda', trend: data.trends.injury, suffix: '', danger: true },
  ];

  return (
    <Layout>
      <PageHeader
        title="Statistika"
        action={
          <div className="statistics-period">
            {periodOptions.map((option) => <button className={period === option.value ? 'active' : ''} key={option.value} onClick={() => setPeriod(option.value)}>{option.label}</button>)}
          </div>
        }
      />

      <div className="statistics-kpi-grid">
        {cards.map((card) => (
          <article className={`statistics-kpi ${card.danger ? 'danger' : ''}`} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.note}</p>
            <small className={trendMark(card.trend)}>{trendCopy(card.trend, card.suffix)}</small>
          </article>
        ))}
      </div>

      <div className="statistics-visual-grid">
        <StatisticsAttendanceChart rows={trend} />
        <StatisticsGoalsChart rows={goals} />
      </div>

      <div className="statistics-rankings-grid">
        <StatisticsRankingCard title="Eng ko'p qatnashgan" rows={rankings.most_present} mode="attendance" />
        <StatisticsRankingCard title="Eng yuqori baho" rows={rankings.top_rated} mode="rating" />
      </div>

      <section className="card statistics-players-card">
        <h2>Futbolchilar jadvali</h2>
        <div className="table-wrap">
          <table className="table statistics-players-table">
            <thead><tr><th>Futbolchi</th><th>Pozitsiya</th><th>Davomad</th><th>Avg baho</th><th>Faollik</th><th>Gol</th><th>Assist</th><th>Davomad %</th></tr></thead>
            <tbody>
              {players.map((row) => (
                <tr key={row.player_id} onClick={() => navigate(`/futbolchilar/${row.player_id}`)}>
                  <td><span className="statistics-player"><i>{row.initials}</i><strong>{row.short_name}</strong></span></td>
                  <td><span className={`position-stat ${row.position}`}>{positionCode(row.position)}</span></td>
                  <td><b>{row.present}/{row.total}</b></td>
                  <td><strong className={row.avg_rating >= 7.5 ? 'rating-good' : row.avg_rating < 6 && row.avg_rating ? 'rating-low' : ''}>{row.avg_rating}</strong></td>
                  <td>{row.avg_activity}</td>
                  <td>{row.goals > 0 ? <b>{row.goals}</b> : row.goals}</td>
                  <td>{row.assists > 0 ? <b>{row.assists}</b> : row.assists}</td>
                  <td><span className="statistics-attendance-cell"><i><b style={{ width: `${row.attendance_percent}%` }} /></i>{row.attendance_percent}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </Layout>
  );
}

function ReportsPage() {
  const [reportType, setReportType] = useState<'attendance' | 'performance' | 'matches'>('attendance');
  const [startDate, setStartDate] = useState(() => today().slice(0, 8) + '01');
  const [endDate, setEndDate] = useState(today());
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const notify = useToast();
  const reportParams = (): ReportParams => ({ report_type: reportType, start_date: startDate, end_date: endDate });

  const build = async () => {
    setLoading(true);
    try {
      setReport(await reportsAPI.get(reportParams()));
    } catch (err) {
      notify(getApiError(err), 'error');
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    if (!report) return;
    setDownloading(true);
    try {
      const blob = await reportsAPI.download(reportParams());
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `hisobot-${reportType}-${startDate}-${endDate}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      notify('Hisobot PDF yuklab olindi.');
    } catch (err) {
      notify(getApiError(err, 'PDF yuklab olishda xatolik yuz berdi.'), 'error');
    } finally {
      setDownloading(false);
    }
  };

  useEffect(() => {
    build();
  }, [reportType]);

  const choices = [
    {
      value: 'attendance' as const,
      title: 'Davomad hisoboti',
      text: "Har bir futbolchi va mashg'ulot bo'yicha to'liq davomad ma'lumoti",
      icon: ClipboardList,
      tone: 'blue',
    },
    {
      value: 'performance' as const,
      title: 'Samaradorlik hisoboti',
      text: "Baho, faollik, intizom va jismoniy ko'rsatkichlar",
      icon: Activity,
      tone: 'green',
    },
    {
      value: 'matches' as const,
      title: "O'yinlar hisoboti",
      text: "O'yinlar natijalari, gol, assist va o'yin statistikasi",
      icon: Trophy,
      tone: 'yellow',
    },
  ];

  return (
    <Layout>
      <div className="reports-page">
        <PageHeader
          title={<span className="report-page-title"><FileText size={26} /> Hisobotlar</span>}
        />
        <div className="report-date-toolbar no-print">
          <div className="report-date-group">
            <label className="report-date-field">
              <span>Boshlanish</span>
              <span className="report-date-control">
                <CalendarDays size={16} />
                <input className="input" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
              </span>
            </label>
            <label className="report-date-field">
              <span>Tugash</span>
              <span className="report-date-control">
                <CalendarDays size={16} />
                <input className="input" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
              </span>
            </label>
            <button className="button primary report-update-button" onClick={build} disabled={loading}><RefreshCw size={17} /> {loading ? 'Yuklanmoqda...' : 'Yangilash'}</button>
          </div>
          <button className="button ghost report-download-button" onClick={downloadPdf} disabled={!report || loading || downloading}>
            <Download size={17} /> {downloading ? 'Tayyorlanmoqda...' : 'Yuklab olish'}
          </button>
        </div>

        <section className="report-selector no-print">
          <p>Hisobot turi</p>
          <div className="report-choice-grid">
            {choices.map((choice) => {
              const Icon = choice.icon;
              return (
                <button className={`report-choice-card ${reportType === choice.value ? 'active' : ''}`} key={choice.value} type="button" onClick={() => setReportType(choice.value)} aria-pressed={reportType === choice.value}>
                  <span className={`report-choice-icon ${choice.tone}`}><Icon size={20} /></span>
                  <strong>{choice.title}</strong>
                  <span>{choice.text}</span>
                </button>
              );
            })}
          </div>
        </section>

        <div className="report-output">
          {report ? <ReportSurface report={report} /> : <div className="card"><EmptyState title="Hisobot topilmadi" text="Sana oralig'ini tekshirib yangilang." /></div>}
        </div>
      </div>
    </Layout>
  );
}

function ReportSurface({ report }: { report: ReportData }) {
  if (report.report_type === 'attendance') return <AttendanceReportSurface report={report} />;
  if (report.report_type === 'performance') return <PerformanceReportSurface report={report} />;
  if (report.report_type === 'matches') return <MatchesReportSurface report={report} />;
  const headers = report.rows[0] ? Object.keys(report.rows[0]) : [];
  return (
    <div className="report-surface">
      <h1>{report.title}</h1>
      <p>{report.subtitle}</p>
      <div className="grid grid-4" style={{ marginTop: 18 }}>
        {report.summary.map((item) => (
          <div className="card" key={item.label} style={{ background: '#fff', color: '#111827', borderColor: '#cbd5e1' }}>
            <div className="small muted">{item.label}</div>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
      <div className="table-wrap" style={{ marginTop: 18 }}>
        <table className="table">
          <thead>
            <tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr>
          </thead>
          <tbody>
            {report.rows.map((row, index) => (
              <tr key={index}>
                {headers.map((header) => <td key={header}>{row[header]}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function reportNumber(row: Record<string, string | number>, key: string) {
  return Number(row[key] || 0);
}

function reportText(row: Record<string, string | number>, key: string) {
  return String(row[key] ?? '');
}

function ReportSummary({ report }: { report: ReportData }) {
  return (
    <div className="report-summary-grid">
      {report.summary.map((item) => (
        <article className="report-summary-card" key={item.label}>
          <strong>{item.value}</strong>
          <span>{item.label}</span>
        </article>
      ))}
    </div>
  );
}

function ReportHeading({ report }: { report: ReportData }) {
  return (
    <header className="report-table-heading">
      <h2>{report.title}</h2>
      <span>{report.subtitle}</span>
    </header>
  );
}

function ReportPercent({ value }: { value: number }) {
  const tone = value >= 80 ? 'green' : value >= 60 ? 'yellow' : 'red';
  return (
    <span className="report-percent">
      <i className={tone}><b style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></i>
      {value}%
    </span>
  );
}

function ReportStatus({ label, tone }: { label: string; tone: string }) {
  return <span className={`badge report-badge ${tone}`}>{label}</span>;
}

function AttendanceReportSurface({ report }: { report: ReportData }) {
  const injuryPlayers = report.injury_overview?.players ?? [];
  const healthyCount = report.injury_overview?.healthy_count ?? 0;
  const injuredCount = injuryPlayers.filter((item) => item.tone === 'red' || item.status.toLowerCase().includes('bor')).length;
  const recoveringCount = injuryPlayers.filter((item) => item.tone === 'yellow' || item.status.toLowerCase().includes('tiklan')).length;

  return (
    <div className="report-surface report-modern-surface">
      <ReportSummary report={report} />
      <section className="report-table-card">
        <ReportHeading report={report} />
        <div className="table-wrap">
          <table className="table report-table">
            <thead>
              <tr>
                <th>Futbolchi</th>
                <th>Keldi</th>
                <th>Kelmadi</th>
                <th>Davomad %</th>
                <th>O'rtacha baho</th>
                <th>O'rtacha faollik</th>
                <th>Holat</th>
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row) => (
                <tr key={reportNumber(row, 'player_id')}>
                  <td>
                    <span className="report-player">
                      <span className="report-initials">{reportText(row, 'initials')}</span>
                      {reportText(row, 'short_name') || reportText(row, 'full_name')}
                    </span>
                  </td>
                  <td>{reportNumber(row, 'present')}</td>
                  <td>{reportNumber(row, 'absent')}</td>
                  <td><ReportPercent value={reportNumber(row, 'attendance_percent')} /></td>
                  <td className={reportNumber(row, 'avg_rating') < 6 && reportNumber(row, 'avg_rating') > 0 ? 'report-low-score' : ''}>{reportNumber(row, 'avg_rating')}</td>
                  <td>{reportNumber(row, 'avg_activity')}</td>
                  <td><ReportStatus label={reportText(row, 'status_label')} tone={reportText(row, 'status_tone')} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="report-side-grid">
        <article className="report-side-card">
          <div className="report-side-card-head">
            <h3>Ko'p qolgan futbolchilar</h3>
            <span>Davomad nazorati</span>
          </div>
          <div className="report-side-list">
            {report.most_absent?.length ? report.most_absent.map((item) => (
              <div className="report-side-row" key={item.player_id}><span>{item.player_name}</span><strong className="report-danger-value">{item.absent} marta</strong></div>
            )) : <p className="muted">Kelmagan futbolchi yo'q.</p>}
          </div>
        </article>
        <article className="report-side-card report-injury-card">
          <div className="report-side-card-head">
            <h3>Jarohat holati</h3>
            <span>{healthyCount + injuryPlayers.length} futbolchi</span>
          </div>
          <div className="report-injury-stats">
            <span><b>{injuredCount}</b> Jarohatli</span>
            <span><b>{healthyCount}</b> Sog'lom</span>
            <span><b>{recoveringCount}</b> Tiklanmoqda</span>
          </div>
          <div className="report-side-list">
            {injuryPlayers.map((item) => (
              <div className="report-side-row" key={item.player_id}><span>{item.player_name}</span><ReportStatus label={item.status} tone={item.tone} /></div>
            ))}
            {!injuryPlayers.length && <p className="muted">Jarohat qayd etilmagan.</p>}
            <div className="report-side-row"><span>Qolgan {healthyCount} ta</span><ReportStatus label="Sog'lom" tone="green" /></div>
          </div>
        </article>
      </div>
    </div>
  );
}

function PerformanceReportSurface({ report }: { report: ReportData }) {
  return (
    <div className="report-surface report-modern-surface">
      <ReportSummary report={report} />
      <section className="report-table-card">
        <ReportHeading report={report} />
        <div className="table-wrap">
          <table className="table report-table">
            <thead><tr><th>Futbolchi</th><th>Pozitsiya</th><th>Mashg'ulot</th><th>O'rtacha baho</th><th>O'rtacha faollik</th><th>Intizom</th><th>Holat</th></tr></thead>
            <tbody>
              {report.rows.map((row) => (
                <tr key={reportNumber(row, 'player_id')}>
                  <td><span className="report-player"><span className="report-initials">{reportText(row, 'initials')}</span>{reportText(row, 'short_name')}</span></td>
                  <td>{reportText(row, 'position_display')}</td>
                  <td>{reportNumber(row, 'present')}</td>
                  <td>{reportNumber(row, 'avg_rating')}</td>
                  <td>{reportNumber(row, 'avg_activity')}</td>
                  <td>{reportNumber(row, 'discipline_issues')}</td>
                  <td><ReportStatus label={reportText(row, 'status_label')} tone={reportText(row, 'status_tone')} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="report-side-grid">
        <ReportRankList title="Eng yuqori baho" rows={report.top_rating || []} />
        <ReportRankList title="Eng faol futbolchilar" rows={report.top_activity || []} />
      </div>
    </div>
  );
}

function ReportRankList({ title, rows }: { title: string; rows: Array<{ player_id: number; player_name: string; value: number }> }) {
  return (
    <article className="report-side-card">
      <h3>{title}</h3>
      {rows.length ? rows.map((item) => (
        <div className="report-side-row" key={item.player_id}><span>{item.player_name}</span><strong>{item.value}</strong></div>
      )) : <p className="muted">Ma'lumot yo'q.</p>}
    </article>
  );
}

function MatchesReportSurface({ report }: { report: ReportData }) {
  return (
    <div className="report-surface report-modern-surface">
      <ReportSummary report={report} />
      <section className="report-table-card">
        <ReportHeading report={report} />
        <div className="table-wrap">
          <table className="table report-table">
            <thead><tr><th>Sana</th><th>O'yin</th><th>Stadion</th><th>Hisob</th><th>Natija</th><th>Status</th><th>Zarba</th><th>Burchak</th></tr></thead>
            <tbody>
              {report.rows.map((row) => (
                <tr key={reportNumber(row, 'id')}>
                  <td>{formatDateShort(reportText(row, 'date'))}</td>
                  <td><strong>{reportText(row, 'fixture')}</strong></td>
                  <td>{reportText(row, 'stadium')}</td>
                  <td>{reportText(row, 'score')}</td>
                  <td><ReportStatus label={reportText(row, 'result')} tone={reportText(row, 'result') === "G'alaba" ? 'green' : reportText(row, 'result') === "Mag'lubiyat" ? 'red' : 'yellow'} /></td>
                  <td>{reportText(row, 'status')}</td>
                  <td>{reportNumber(row, 'shots')} / {reportNumber(row, 'shots_on_target')}</td>
                  <td>{reportNumber(row, 'corners')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function SettingsPage() {
  const { user, setUser, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [form, setForm] = useState<Partial<User>>(user || {});
  const [savedProfile, setSavedProfile] = useState<Partial<User>>(user || {});
  const [profileEditing, setProfileEditing] = useState(false);
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' });
  const notify = useToast();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await settingsAPI.get();
        setForm(data);
        setSavedProfile(data);
        setUser(data);
      } catch (err) {
        notify(getApiError(err), 'error');
      }
    };
    load();
  }, []);

  const set = (key: keyof User, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const profileFields: (keyof User)[] = ['first_name', 'last_name', 'email', 'phone', 'club_name', 'role'];
  const profileChanged = profileFields.some((key) => (form[key] || '') !== (savedProfile[key] || ''));

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!profileEditing || !profileChanged) return;
    try {
      const updated = await settingsAPI.update(form);
      setForm(updated);
      setSavedProfile(updated);
      setProfileEditing(false);
      setUser(updated);
      notify('Sozlamalar saqlandi.');
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  const changePassword = async (event: FormEvent) => {
    event.preventDefault();
    if (!passwords.current_password || !passwords.new_password) {
      notify('Parol maydonlari majburiy.', 'error');
      return;
    }
    try {
      await settingsAPI.changePassword(passwords.current_password, passwords.new_password);
      setPasswords({ current_password: '', new_password: '' });
      notify('Parol yangilandi.');
    } catch (err) {
      notify(getApiError(err), 'error');
    }
  };

  return (
    <Layout>
      <PageHeader
        title="Sozlamalar"
        description="Murabbiy profili, jamoa nomi va parol sozlamalarini boshqaring."
      />
      <div className="settings-page-stack">
        <div className="settings-primary-grid">
          <form className="card settings-card settings-profile-card" onSubmit={save}>
            <div className="settings-section-head">
              <div>
                <h2 className="card-title">Profil sozlamalari</h2>
                <p className="muted">Murabbiy profili va klub ma'lumotlarini yangilang.</p>
              </div>
            </div>
            <div className="form-grid settings-profile-grid">
              <Field label="Ism">
                <input className="input" disabled={!profileEditing} value={form.first_name || ''} onChange={(event) => set('first_name', event.target.value)} />
              </Field>
              <Field label="Familiya">
                <input className="input" disabled={!profileEditing} value={form.last_name || ''} onChange={(event) => set('last_name', event.target.value)} />
              </Field>
              <Field label="Elektron pochta">
                <input className="input" disabled={!profileEditing} type="email" value={form.email || ''} onChange={(event) => set('email', event.target.value)} />
              </Field>
              <Field label="Telefon">
                <input className="input" disabled={!profileEditing} value={form.phone || ''} onChange={(event) => set('phone', event.target.value)} />
              </Field>
              <Field label="Jamoa nomi">
                <input className="input" disabled={!profileEditing} value={form.club_name || ''} onChange={(event) => set('club_name', event.target.value)} />
              </Field>
              <Field label="Lavozim">
                <input className="input" disabled={!profileEditing} value={form.role || ''} onChange={(event) => set('role', event.target.value)} />
              </Field>
            </div>
            <div className="settings-profile-actions">
              {!profileEditing ? (
                <button type="button" className="button primary" onClick={() => setProfileEditing(true)}><Edit size={18} /> Tahrirlash</button>
              ) : profileChanged ? (
                <>
                  <button
                    type="button"
                    className="button ghost"
                    onClick={() => {
                      setForm(savedProfile);
                      setProfileEditing(false);
                    }}
                  >
                    <X size={18} /> Bekor qilish
                  </button>
                  <button className="button success"><Save size={18} /> Saqlash</button>
                </>
              ) : (
                <button
                  type="button"
                  className="button ghost"
                  onClick={() => {
                    setForm(savedProfile);
                    setProfileEditing(false);
                  }}
                >
                  <X size={18} /> Bekor qilish
                </button>
              )}
            </div>
          </form>

          <form className="card settings-card settings-mini-card" onSubmit={changePassword}>
            <div className="settings-section-head compact">
              <div>
                <h2 className="card-title">Parol yangilash</h2>
                <p className="muted">Hisobingiz uchun yangi parol kiriting.</p>
              </div>
            </div>
            <div className="settings-form-stack">
              <Field label="Amaldagi parol">
                <input className="input" type="password" value={passwords.current_password} onChange={(event) => setPasswords((current) => ({ ...current, current_password: event.target.value }))} />
              </Field>
              <Field label="Yangi parol">
                <input className="input" type="password" value={passwords.new_password} onChange={(event) => setPasswords((current) => ({ ...current, new_password: event.target.value }))} />
              </Field>
              <button className="button warning settings-full-button"><ShieldAlert size={18} /> Parolni saqlash</button>
            </div>
          </form>

          <div className="settings-side-stack">
            <div className="card settings-card settings-mini-card">
              <div className="settings-section-head compact">
                <div>
                  <h2 className="card-title">Xavfsizlik</h2>
                  <p className="muted">Sessiya va kirish holati nazorati.</p>
                </div>
              </div>
              <div className="settings-security-list">
                <div className="security-item">
                  <ShieldAlert size={18} />
                  <span>
                    <strong>Faol sessiya</strong>
                    <small>{user?.username || 'Murabbiy'} sifatida tizimga kirilgan</small>
                  </span>
                </div>
                <button className="button ghost settings-full-button" onClick={logout}><LogOut size={18} /> Tizimdan chiqish</button>
              </div>
            </div>

            <div className="card settings-card settings-mini-card">
              <div className="settings-section-head compact">
                <div>
                  <h2 className="card-title">Ko'rinish rejimi</h2>
                  <p className="muted">Ish muhitiga mos rang rejimini tanlang.</p>
                </div>
              </div>
              <div className="theme-choice settings-theme-choice">
                <button
                  type="button"
                  className={`theme-option ${theme === 'light' ? 'active' : ''}`}
                  onClick={() => setTheme('light')}
                >
                  <Sun size={20} />
                  <span>
                    <strong>Kunduzgi</strong>
                    <small>Oq ko'rinish</small>
                  </span>
                </button>
                <button
                  type="button"
                  className={`theme-option ${theme === 'dark' ? 'active' : ''}`}
                  onClick={() => setTheme('dark')}
                >
                  <Moon size={20} />
                  <span>
                    <strong>Tungi</strong>
                    <small>Qorong'i ko'rinish</small>
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/kirish" element={<AuthPage />} />
      <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/futbolchilar" element={<ProtectedRoute><PlayersPage /></ProtectedRoute>} />
      <Route path="/futbolchilar/:id" element={<ProtectedRoute><RedesignedPlayerDetailPage /></ProtectedRoute>} />
      <Route path="/mashgulotlar" element={<ProtectedRoute><TrainingsListPage /></ProtectedRoute>} />
      <Route path="/mashgulotlar/:id" element={<ProtectedRoute><TrainingDetailPage /></ProtectedRoute>} />
      <Route path="/oyinlar" element={<ProtectedRoute><MatchesPage /></ProtectedRoute>} />
      <Route path="/oyinlar/:id" element={<ProtectedRoute><MatchDetailPage /></ProtectedRoute>} />
      <Route path="/statistika" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
      <Route path="/hisobotlar" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
      <Route path="/sozlamalar" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </ToastProvider>
  );
}
