import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import {
  Activity,
  ArrowLeft,
  CalendarDays,
  ClipboardList,
  Dumbbell,
  Flag,
  Hash,
  HeartPulse,
  Medal,
  Ruler,
  Star,
  Target,
  Trophy,
  UserRound,
  UserX,
  Weight,
} from 'lucide-react';
import { Layout } from '../app/components/layout/Layout';
import { getApiError } from '../app/services/api';
import { ErrorState, LoadingState } from '../components/ui/page-states';
import { getPlayerProfile } from '../services/players';
import type { PlayerProfile, PlayerTrainingHistoryItem } from '../types/players';

const monthNames = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];

function numberValue(...values: Array<number | string | undefined | null>) {
  for (const value of values) {
    const numeric = Number(value);
    if (value !== '' && value !== null && value !== undefined && Number.isFinite(numeric)) return numeric;
  }
  return 0;
}

function formatDate(value?: string, includeYear = true) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getDate()} ${monthNames[date.getMonth()]}${includeYear ? ` ${date.getFullYear()}` : ''}`;
}

function historyTitle(item: PlayerTrainingHistoryItem) {
  return item.training_title || item.training_detail?.title || "Mashg'ulot";
}

function historyDate(item: PlayerTrainingHistoryItem) {
  return item.training_date || item.training_detail?.training_date;
}

function isAbsent(item: PlayerTrainingHistoryItem) {
  const status = `${item.attendance_status} ${item.attendance_status_display || ''}`.toLowerCase();
  return status.includes('qatnashmadi') || status.includes('kelmadi') || status.includes('absent');
}

function hasInjury(item?: PlayerTrainingHistoryItem) {
  if (!item) return false;
  const injury = `${item.injury_status || ''} ${item.injury_status_display || ''}`.toLowerCase();
  return injury.includes('bor') || injury.includes('tiklanmoqda');
}

function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

function percentage(value: number) {
  return Math.max(0, Math.min(100, Math.round(value || 0)));
}

export default function PlayerDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    if (!id) {
      setError('Futbolchi topilmadi.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');
    try {
      setProfile(await getPlayerProfile(id));
    } catch (loadError) {
      setError(getApiError(loadError, 'Futbolchi profili yuklanmadi.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const summary = useMemo(() => {
    if (!profile) return null;
    const history = profile.training_history || [];
    const player = profile.player;
    const gameStatistics = profile.game_statistics || player.game_statistics || {
      matches_played: 0,
      goals: 0,
      assists: 0,
      rating: 0,
    };

    return {
      history,
      recentHistory: history.slice(0, 3),
      coachNotes: history.filter((item) => item.coach_note?.trim()).slice(0, 2),
      injury: hasInjury(history[0]),
      attendancePercent: percentage(numberValue(profile.attendance_percent, profile.stats?.attendance_percent, player.attendance_percent)),
      averageRating: numberValue(profile.average_rating, profile.stats?.average_rating, player.average_rating),
      trainingCount: numberValue(
        profile.training_count,
        profile.stats?.total_marked_trainings,
        profile.stats?.training_count,
        player.training_count,
      ),
      absentCount: numberValue(profile.absent_count, profile.stats?.absent_trainings, profile.stats?.absent_count, player.absent_count),
      gameStatistics,
    };
  }, [profile]);

  if (loading) {
    return (
      <Layout>
        <LoadingState />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <ErrorState message={error} retry={load} />
      </Layout>
    );
  }

  if (!profile || !summary) {
    return (
      <Layout>
        <ErrorState message="Futbolchi topilmadi." retry={load} />
      </Layout>
    );
  }

  const { player } = profile;
  const ratingText = summary.averageRating ? summary.averageRating.toFixed(1) : '0.0';
  const gameRating = numberValue(summary.gameStatistics.rating);

  return (
    <Layout>
      <div className="player-detail-page">
        <section className="player-detail-hero">
          <div className="player-detail-hero-main">
            {player.photo_url ? (
              <img className="player-detail-avatar photo" src={player.photo_url} alt={player.full_name} />
            ) : (
              <div className="player-detail-avatar initials">{initials(player.full_name)}</div>
            )}
            <div>
              <h1>{player.full_name}</h1>
              <div className="player-detail-meta">
                <span><Hash size={17} /> {player.shirt_number || '-'}</span>
                <span><UserRound size={17} /> {player.position_display || player.position || '-'}</span>
                <span><Flag size={17} /> {player.nationality || '-'}</span>
                <span><CalendarDays size={17} /> {player.age || '-'} yosh</span>
              </div>
            </div>
          </div>

          <div className="player-detail-hero-actions">
            <span className={`player-detail-health ${summary.injury ? 'danger' : 'healthy'}`}>
              <HeartPulse size={18} />
              {summary.injury ? 'Jarohat bor' : "Sog'lom"}
            </span>
            <button type="button" onClick={() => navigate('/futbolchilar')}>
              <ArrowLeft size={19} /> Orqaga
            </button>
          </div>
        </section>

        <section className="player-detail-kpis">
          <article className="player-kpi-card">
            <div className="player-kpi-top">
              <span className="player-kpi-icon blue"><Activity size={22} /></span>
              <span className={`player-trend ${summary.attendancePercent < 75 ? 'danger' : 'good'}`}>
                {summary.attendancePercent < 75 ? '\u2193 past' : '\u2191 yaxshi'}
              </span>
            </div>
            <strong>{summary.attendancePercent}%</strong>
            <span>Qatnashuv</span>
          </article>

          <article className="player-kpi-card">
            <div className="player-kpi-top">
              <span className="player-kpi-icon amber"><Star size={22} /></span>
              <span className="player-trend neutral">o'rtacha</span>
            </div>
            <strong>{ratingText}</strong>
            <span>O'rtacha baho</span>
          </article>

          <article className="player-kpi-card">
            <div className="player-kpi-top">
              <span className="player-kpi-icon green"><Dumbbell size={22} /></span>
              <span className="player-trend neutral">jami</span>
            </div>
            <strong>{summary.trainingCount}</strong>
            <span>Jami mashg'ulotlar</span>
          </article>

          <article className="player-kpi-card">
            <div className="player-kpi-top">
              <span className="player-kpi-icon red"><UserX size={22} /></span>
              {summary.absentCount > 0 && <span className="player-trend danger">{'\u2191 diqqat'}</span>}
            </div>
            <strong>{summary.absentCount}</strong>
            <span>Kelmagan soni</span>
          </article>

          <article className="player-kpi-card">
            <div className="player-kpi-top">
              <span className="player-kpi-icon purple"><Trophy size={22} /></span>
            </div>
            <strong>{summary.gameStatistics.matches_played || 0}</strong>
            <span>O'yinlar soni</span>
          </article>
        </section>

        <section className="player-detail-row player-detail-row-games">
          <article className="player-detail-card">
            <header>
              <h2>O'yin statistikasi</h2>
            </header>
            <div className="player-game-grid">
              <div className="player-game-stat active">
                <Trophy size={19} />
                <strong>{summary.gameStatistics.matches_played || 0}</strong>
                <span>O'yinlar</span>
              </div>
              <div className="player-game-stat">
                <Target size={19} />
                <strong>{summary.gameStatistics.goals || 0}</strong>
                <span>Gol</span>
              </div>
              <div className="player-game-stat">
                <ClipboardList size={19} />
                <strong>{summary.gameStatistics.assists || 0}</strong>
                <span>Assist</span>
              </div>
              <div className="player-game-stat">
                <Medal size={19} />
                <strong>{gameRating.toFixed(1)}</strong>
                <span>Reyting</span>
              </div>
            </div>
          </article>

          <article className="player-detail-card">
            <header>
              <h2>Jismoniy ko'rsatkichlar</h2>
            </header>
            <div className="player-facts">
              <div><span><Ruler size={17} /> Bo'yi</span><strong>{player.height || '-'} m</strong></div>
              <div><span><Weight size={17} /> Vazni</span><strong>{player.weight || '-'} kg</strong></div>
              <div><span><CalendarDays size={17} /> Qo'shilgan sana</span><strong>{formatDate(player.join_date)}</strong></div>
              <div>
                <span><HeartPulse size={17} /> Jarohat holati</span>
                <strong className={`player-detail-pill ${summary.injury ? 'danger' : 'healthy'}`}>
                  {summary.injury ? 'Jarohat bor' : "Jarohat yo'q"}
                </strong>
              </div>
            </div>
          </article>
        </section>

        <section className="player-detail-row player-detail-row-history">
          <article className="player-detail-card">
            <header>
              <h2>Mashg'ulot tarixi</h2>
              <span>So'nggi 3 ta</span>
            </header>
            {summary.recentHistory.length ? (
              <div className="player-history-list">
                {summary.recentHistory.map((item) => {
                  const absent = isAbsent(item);
                  const progress = absent ? 0 : percentage(numberValue(item.participation_percent));
                  const rating = numberValue(item.rating);

                  return (
                    <div className="player-history-row" key={`${item.id || historyTitle(item)}-${historyDate(item) || ''}`}>
                      <div className="player-history-copy">
                        <strong>{historyTitle(item)}</strong>
                        <span>{formatDate(historyDate(item))}</span>
                      </div>
                      <div className="player-history-metrics">
                        <div className="player-history-progress">
                          <i><b style={{ width: `${progress}%` }} /></i>
                          <span>{absent ? '-' : `${progress}%`}</span>
                        </div>
                        <span className={`player-detail-pill ${absent ? 'danger' : 'healthy'}`}>{absent ? 'Kelmadi' : 'Keldi'}</span>
                        {absent || !rating ? (
                          <span className="player-rating empty">- baho yo'q</span>
                        ) : (
                          <span className="player-rating"><Star size={16} /> {rating.toFixed(1)}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="player-detail-empty">Mashg'ulot tarixi yo'q.</p>
            )}
          </article>

          <article className="player-detail-card">
            <header>
              <h2>Murabbiy izohlari</h2>
              <span>So'nggi 2 ta</span>
            </header>
            {summary.coachNotes.length ? (
              <div className="player-notes-list">
                {summary.coachNotes.map((item) => (
                  <div className="player-note" key={`${item.id || historyTitle(item)}-note-${historyDate(item) || ''}`}>
                    <div>
                      <strong>{historyTitle(item)}</strong>
                      <span>{formatDate(historyDate(item), false)}</span>
                    </div>
                    <p>{item.coach_note}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="player-detail-empty">Izoh yo'q.</p>
            )}
          </article>
        </section>
      </div>

      <style>{`
        .page-content:has(.player-detail-page) {
          background: #f0f2f5;
        }

        .player-detail-page {
          --player-title-size: 36px;
          --player-section-title-size: 18px;
          --player-kpi-size: 30px;
          --player-game-size: 28px;
          --player-label-size: 14px;
          --player-body-size: 14px;
          display: grid;
          gap: 20px;
          min-height: calc(100vh - 92px);
          color: #151b26;
          font-variant-numeric: tabular-nums;
        }

        .player-detail-hero,
        .player-detail-card,
        .player-kpi-card {
          border: 1px solid #e8e8e8;
          border-radius: 12px;
          background: #fff;
        }

        .player-detail-hero {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 24px;
          min-height: 204px;
          overflow: hidden;
          padding: 32px 38px;
          border-color: #1a3560;
          background: #1a3560;
          color: #fff;
        }

        .player-detail-hero-main {
          display: flex;
          align-items: center;
          gap: 28px;
          min-width: 0;
        }

        .player-detail-hero h1 {
          margin: 0 0 18px;
          color: #fff;
          font-size: var(--player-title-size);
          font-weight: 760;
          line-height: 1.1;
          letter-spacing: 0;
        }

        .player-detail-avatar {
          display: grid;
          width: 128px;
          height: 128px;
          flex: 0 0 128px;
          place-items: center;
          overflow: hidden;
          border: 4px solid rgba(142, 185, 255, .38);
          border-radius: 50%;
          background: #355b99;
          color: #fff;
          font-size: 38px;
          font-weight: 750;
          object-fit: cover;
        }

        .player-detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 12px 26px;
          color: rgba(238, 244, 255, .78);
          font-size: var(--player-body-size);
          font-weight: 600;
        }

        .player-detail-meta span,
        .player-facts span {
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .player-detail-hero-actions {
          align-self: stretch;
          display: flex;
          min-width: 190px;
          flex-direction: column;
          align-items: stretch;
          justify-content: space-between;
          gap: 16px;
        }

        .player-detail-health,
        .player-detail-hero-actions button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          min-height: 52px;
          border: 1px solid rgba(218, 231, 255, .34);
          border-radius: 999px;
          background: rgba(255, 255, 255, .09);
          color: #fff;
          font-size: 16px;
          font-weight: 650;
        }

        .player-detail-health.danger {
          background: rgba(255, 113, 130, .16);
          border-color: rgba(255, 180, 188, .46);
        }

        .player-detail-hero-actions button {
          align-self: flex-end;
          width: 100%;
          border-radius: 12px;
          cursor: pointer;
          transition: background .18s ease, transform .18s ease;
        }

        .player-detail-hero-actions button:hover {
          background: rgba(255, 255, 255, .15);
          transform: translateY(-1px);
        }

        .player-detail-kpis {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 16px;
        }

        .player-kpi-card {
          display: grid;
          gap: 8px;
          min-height: 188px;
          padding: 26px;
        }

        .player-kpi-top {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 10px;
          min-height: 56px;
        }

        .player-kpi-icon {
          display: grid;
          width: 64px;
          height: 64px;
          place-items: center;
          border-radius: 14px;
        }

        .player-kpi-icon.blue { background: #dbeafe; color: #2563eb; }
        .player-kpi-icon.amber { background: #fef3c7; color: #b77905; }
        .player-kpi-icon.green { background: #d1fae5; color: #15905e; }
        .player-kpi-icon.red { background: #fee2e2; color: #ef4444; }
        .player-kpi-icon.purple { background: #ede9fe; color: #7c3aed; }

        .player-trend,
        .player-detail-pill,
        .player-rating {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 5px;
          border-radius: 999px;
          padding: 7px 12px;
          font-size: 14px;
          font-weight: 650;
          line-height: 1;
        }

        .player-trend.good,
        .player-detail-pill.healthy {
          background: #d8f8e4;
          color: #087443;
        }

        .player-trend.danger,
        .player-detail-pill.danger {
          background: #ffe0e3;
          color: #dc2626;
        }

        .player-trend.neutral {
          background: #f0f1f5;
          color: #6b7280;
        }

        .player-kpi-card > strong {
          color: #05070d;
          font-size: var(--player-kpi-size);
          font-weight: 760;
          line-height: 1.05;
          letter-spacing: 0;
        }

        .player-kpi-card > span:last-child {
          color: #8a8f99;
          font-size: var(--player-label-size);
          font-weight: 620;
          line-height: 1.25;
        }

        .player-detail-row {
          display: grid;
          gap: 22px;
        }

        .player-detail-row-games {
          grid-template-columns: 1fr 1fr;
        }

        .player-detail-row-history {
          grid-template-columns: 1.2fr .8fr;
        }

        .player-detail-card {
          overflow: hidden;
          min-height: 290px;
        }

        .player-detail-card header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          min-height: 68px;
          padding: 0 28px;
          border-bottom: 1px solid #ededed;
        }

        .player-detail-card h2 {
          margin: 0;
          color: #151515;
          font-size: var(--player-section-title-size);
          font-weight: 730;
          letter-spacing: 0;
        }

        .player-detail-card header > span {
          color: #9298a3;
          font-size: var(--player-label-size);
          font-weight: 560;
        }

        .player-game-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 14px;
          padding: 28px;
        }

        .player-game-stat {
          display: grid;
          min-height: 108px;
          place-items: center;
          gap: 5px;
          border-radius: 12px;
          background: #f7f8fa;
          color: #687180;
        }

        .player-game-stat svg {
          opacity: .78;
        }

        .player-game-stat strong {
          color: #05070d;
          font-size: var(--player-game-size);
          font-weight: 760;
          line-height: 1.05;
          letter-spacing: 0;
        }

        .player-game-stat span {
          color: #8a8f99;
          font-size: var(--player-label-size);
          font-weight: 620;
          line-height: 1.25;
        }

        .player-game-stat.active {
          background: #dbeafe;
          color: #2563eb;
        }

        .player-game-stat.active strong {
          color: #2563eb;
        }

        .player-game-stat.active span {
          color: #2563eb;
        }

        .player-facts {
          display: grid;
          padding: 28px;
        }

        .player-facts > div {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          min-height: 54px;
          border-bottom: 1px solid #ededed;
          color: #686d77;
          font-size: var(--player-body-size);
        }

        .player-facts strong {
          color: #252932;
          font-size: 16px;
          font-weight: 720;
          text-align: right;
        }

        .player-facts > div:last-child {
          min-height: 72px;
          border-bottom: 0;
        }

        .player-facts .player-detail-pill {
          font-size: var(--player-body-size);
        }

        .player-history-list,
        .player-notes-list {
          display: grid;
          padding: 18px 28px 28px;
        }

        .player-history-row {
          display: grid;
          grid-template-columns: minmax(150px, 1fr) auto;
          align-items: center;
          gap: 18px;
          min-height: 76px;
        }

        .player-history-copy {
          display: grid;
          gap: 3px;
        }

        .player-history-copy strong,
        .player-note strong {
          color: #2b2f37;
          font-size: var(--player-body-size);
          font-weight: 650;
          line-height: 1.2;
        }

        .player-history-copy span,
        .player-note div span {
          color: #969da8;
          font-size: 14px;
          font-weight: 560;
        }

        .player-history-metrics {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 10px;
        }

        .player-history-progress {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #5b6471;
          font-size: var(--player-label-size);
          font-weight: 620;
        }

        .player-history-progress i {
          display: block;
          width: 120px;
          height: 8px;
          overflow: hidden;
          border-radius: 999px;
          background: #ededed;
        }

        .player-history-progress b {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: #16a34a;
        }

        .player-rating {
          min-width: 78px;
          border-radius: 10px;
          background: #fff3b8;
          color: #9a6700;
        }

        .player-rating.empty {
          background: #f0f1f5;
          color: #9aa1ad;
          white-space: nowrap;
        }

        .player-note {
          display: grid;
          gap: 8px;
          padding: 18px 0;
          border-bottom: 1px solid #ededed;
        }

        .player-note:first-child {
          padding-top: 8px;
        }

        .player-note:last-child {
          border-bottom: 0;
          padding-bottom: 0;
        }

        .player-note > div {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .player-note p,
        .player-detail-empty {
          margin: 0;
          color: #616975;
          font-size: var(--player-body-size);
          line-height: 1.45;
        }

        .player-detail-empty {
          padding: 28px;
        }

        @media (max-width: 1180px) {
          .player-detail-kpis {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .player-detail-row-games,
          .player-detail-row-history {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 760px) {
          .player-detail-page {
            --player-title-size: 28px;
            --player-kpi-size: 28px;
            --player-game-size: 26px;
            gap: 14px;
          }

          .player-detail-hero {
            min-height: 0;
            flex-direction: column;
            align-items: stretch;
            padding: 22px;
          }

          .player-detail-hero-main {
            align-items: flex-start;
            flex-direction: column;
            gap: 16px;
          }

          .player-detail-avatar {
            width: 88px;
            height: 88px;
            flex-basis: 88px;
            font-size: 28px;
          }

          .player-detail-hero-actions {
            min-width: 0;
          }

          .player-detail-health,
          .player-detail-hero-actions button {
            min-height: 46px;
            font-size: 16px;
          }

          .player-detail-kpis,
          .player-game-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .player-kpi-card {
            min-height: 164px;
            padding: 18px;
          }

          .player-detail-card header,
          .player-game-grid,
          .player-facts,
          .player-history-list,
          .player-notes-list {
            padding-left: 18px;
            padding-right: 18px;
          }

          .player-history-row {
            grid-template-columns: 1fr;
            gap: 10px;
            padding: 10px 0;
          }

          .player-history-metrics {
            justify-content: flex-start;
            flex-wrap: wrap;
          }

          .player-history-progress i {
            width: 100px;
          }
        }

        @media (max-width: 480px) {
          .player-detail-kpis,
          .player-game-grid {
            grid-template-columns: 1fr;
          }

          .player-detail-meta {
            display: grid;
            gap: 8px;
          }

          .player-facts > div {
            align-items: flex-start;
            flex-direction: column;
            padding: 10px 0;
          }

          .player-facts strong {
            text-align: left;
          }
        }
      `}</style>
    </Layout>
  );
}
