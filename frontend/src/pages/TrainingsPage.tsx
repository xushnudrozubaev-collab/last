import { FormEvent, useEffect, useMemo, useState } from 'react';
import { BarChart2, Calendar, Clock, Plus, Search, Users } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Layout } from '../app/components/layout/Layout';
import { Training } from '../app/services/api';
import { ErrorState, EmptyState, LoadingState } from '../components/ui/page-states';
import { Modal } from '../components/ui/modal';
import { getApiError, TrainingCreatePayload, trainingsService } from '../services/trainings';

const trainingTypes = [
  { value: '', label: 'Barcha turlar' },
  { value: 'tactics', label: 'Taktika' },
  { value: 'fitness', label: 'Jismoniy' },
  { value: 'technical', label: 'Texnik' },
  { value: 'recovery', label: 'Tiklanish' },
] as const;

const typeTone: Record<string, string> = {
  tactics: 'tactics',
  fitness: 'fitness',
  technical: 'technical',
  recovery: 'recovery',
};

type QuickPeriod = 'today' | 'week' | 'month';

function localToday() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function createDefaults(): TrainingCreatePayload {
  return {
    title: '',
    training_type: 'tactics',
    training_date: localToday(),
    start_time: '09:00',
    end_time: '10:30',
    location: '',
    note: '',
  };
}

function dateDisplay(value: string) {
  const [year, month, day] = String(value || '').slice(0, 10).split('-');
  return year && month && day ? `${day}.${month}.${year}` : '-';
}

function timeDisplay(value: string) {
  return value ? value.slice(0, 5) : '-';
}

function wholeRating(value: number) {
  return String(Math.round(Number(value || 0)));
}

function attendanceRatio(training: Training) {
  if (training.attendance_display) return training.attendance_display;
  return `${training.attendance_present || 0}/${training.attendance_total || 0}`;
}

function average(rows: Training[], field: 'attendance_percent' | 'average_rating') {
  if (!rows.length) return 0;
  return rows.reduce((sum, training) => sum + Number(training[field] || 0), 0) / rows.length;
}

function trainingInPeriod(training: Training, period: QuickPeriod) {
  const trainingDate = new Date(`${training.training_date}T00:00:00`);
  const current = new Date(`${localToday()}T00:00:00`);
  if (period === 'today') return training.training_date === localToday();
  if (period === 'week') {
    const weekStart = new Date(current);
    weekStart.setDate(current.getDate() - 6);
    return trainingDate >= weekStart && trainingDate <= current;
  }
  return trainingDate.getFullYear() === current.getFullYear() && trainingDate.getMonth() === current.getMonth();
}

export default function TrainingsPage() {
  const navigate = useNavigate();
  const [trainings, setTrainings] = useState<Training[]>([]);
  const [allTrainings, setAllTrainings] = useState<Training[]>([]);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [period, setPeriod] = useState<QuickPeriod>('month');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<TrainingCreatePayload>(createDefaults);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [filtered, all] = await Promise.all([
        trainingsService.list({ search: search || undefined, type: type || undefined }),
        trainingsService.list(),
      ]);
      setTrainings(filtered);
      setAllTrainings(all);
    } catch (caught) {
      setError(getApiError(caught));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [search, type]);

  const visibleTrainings = useMemo(
    () => trainings.filter((training) => trainingInPeriod(training, period)),
    [trainings, period],
  );

  const kpis = useMemo(() => {
    const today = localToday();
    return [
      { label: "Jami mashg'ulot", value: allTrainings.length, icon: Clock },
      { label: 'Bugungi', value: allTrainings.filter((training) => training.training_date === today).length, icon: Calendar },
      { label: "O'rtacha qatnashuv", value: `${Math.round(average(allTrainings, 'attendance_percent'))}%`, icon: Users },
      { label: "O'rtacha baho", value: wholeRating(average(allTrainings, 'average_rating')), icon: BarChart2 },
    ];
  }, [allTrainings]);

  const setField = (field: keyof TrainingCreatePayload, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const createTraining = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      await trainingsService.create(form);
      setCreateOpen(false);
      setForm(createDefaults());
      await load();
    } catch (caught) {
      setFormError(getApiError(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout>
      <section className="trainings-page">
        <header className="trainings-header">
          <div>
            <h1>Mashg'ulotlar</h1>
            <p>Barcha mashg'ulotlar va davomad ko'rsatkichlari</p>
          </div>
          <button className="trainings-primary-button" type="button" onClick={() => setCreateOpen(true)}>
            <Plus size={17} /> Qo'shish
          </button>
        </header>

        <div className="trainings-kpi-grid">
          {kpis.map(({ label, value, icon: Icon }) => (
            <article className="trainings-kpi-card" key={label}>
              <span className="trainings-kpi-icon"><Icon size={17} /></span>
              <span className="trainings-kpi-label">{label}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </div>

        <div className="trainings-filter-row">
          <label className="trainings-search">
            <Search size={17} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Mashg'ulot nomi yoki joy bo'yicha qidirish" />
          </label>
          <select value={type} onChange={(event) => setType(event.target.value)} aria-label="Mashg'ulot turi">
            {trainingTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
          <div className="trainings-quick-period" aria-label="Tezkor sana filtri">
            <button className={period === 'today' ? 'active' : ''} type="button" onClick={() => setPeriod('today')}>Bugun</button>
            <button className={period === 'week' ? 'active' : ''} type="button" onClick={() => setPeriod('week')}>Bu hafta</button>
            <button className={period === 'month' ? 'active' : ''} type="button" onClick={() => setPeriod('month')}>Bu oy</button>
          </div>
        </div>

        <section className="trainings-cards-section">
          <div className="trainings-table-head">
            <h2>{visibleTrainings.length} ta mashg'ulot</h2>
          </div>
          {loading ? (
            <LoadingState />
          ) : error ? (
            <ErrorState message={error} retry={load} />
          ) : !visibleTrainings.length ? (
            <EmptyState message="Hali mashg'ulot qo'shilmagan" />
          ) : (
            <>
              <div className="trainings-card-grid">
                {visibleTrainings.map((training) => (
                  <article className={`training-list-card ${typeTone[training.training_type] || 'technical'}`} key={training.id} onClick={() => navigate(`/mashgulotlar/${training.id}`)}>
                    <div className="training-list-card-top">
                      <div>
                        <h3>{training.title}</h3>
                        <p>{training.location}</p>
                      </div>
                      <span className={`trainings-type-badge ${typeTone[training.training_type] || 'technical'}`}>{training.training_type_display}</span>
                    </div>
                    <div className="training-list-card-meta">
                      <span><Calendar size={15} /> {dateDisplay(training.training_date)}</span>
                      <span><Clock size={15} /> {timeDisplay(training.start_time)} - {timeDisplay(training.end_time)}</span>
                      <span>{training.duration_minutes} daq</span>
                    </div>
                    <div className="training-list-card-footer">
                      <span className="trainings-attendance">
                        <i><b style={{ width: `${Math.min(Math.max(training.attendance_percent || 0, 0), 100)}%` }} /></i>
                        <em>{attendanceRatio(training)} / {Math.round(training.attendance_percent || 0)}%</em>
                      </span>
                      <strong>{wholeRating(training.average_rating)}</strong>
                    </div>
                  </article>
                ))}
              </div>
            {false && <div className="table-wrap">
              <table className="trainings-table">
                <thead>
                  <tr>
                    <th>Nom</th>
                    <th>Sana</th>
                    <th>Vaqt</th>
                    <th>Turi</th>
                    <th>Qatnashuv</th>
                  </tr>
                </thead>
                <tbody>
                  {trainings.map((training) => (
                    <tr key={training.id} onClick={() => navigate(`/mashgulotlar/${training.id}`)}>
                      <td>
                        <strong>{training.title}</strong>
                        <small>{training.location}</small>
                      </td>
                      <td>{dateDisplay(training.training_date)}</td>
                      <td>{timeDisplay(training.start_time)} - {timeDisplay(training.end_time)}</td>
                      <td><span className={`trainings-type-badge ${typeTone[training.training_type] || 'technical'}`}>{training.training_type_display}</span></td>
                      <td>
                        <span className="trainings-attendance">
                          <i><b style={{ width: `${Math.min(Math.max(training.attendance_percent || 0, 0), 100)}%` }} /></i>
                          <em>{attendanceRatio(training)} · {Math.round(training.attendance_percent || 0)}%</em>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>}
            </>
          )}
        </section>
      </section>

      {createOpen && (
        <Modal title="Mashg'ulot qo'shish" onClose={() => setCreateOpen(false)}>
          <form className="trainings-form" onSubmit={createTraining}>
            <label>Mashg'ulot nomi<input required value={form.title} onChange={(event) => setField('title', event.target.value)} /></label>
            <label>Turi
              <select required value={form.training_type} onChange={(event) => setField('training_type', event.target.value)}>
                {trainingTypes.filter((item) => item.value).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </label>
            <label>Sana<input required type="date" value={form.training_date} onChange={(event) => setField('training_date', event.target.value)} /></label>
            <label>Boshlanish vaqti<input required type="time" value={form.start_time} onChange={(event) => setField('start_time', event.target.value)} /></label>
            <label>Tugash vaqti<input required type="time" value={form.end_time} onChange={(event) => setField('end_time', event.target.value)} /></label>
            <label>Joy<input required value={form.location} onChange={(event) => setField('location', event.target.value)} /></label>
            <label className="wide">Izoh<textarea value={form.note} onChange={(event) => setField('note', event.target.value)} /></label>
            {formError && <p className="trainings-form-error">{formError}</p>}
            <div className="trainings-form-actions">
              <button className="button ghost" type="button" onClick={() => setCreateOpen(false)}>Bekor qilish</button>
              <button className="trainings-primary-button" disabled={saving}>{saving ? 'Saqlanmoqda...' : 'Saqlash'}</button>
            </div>
          </form>
        </Modal>
      )}
    </Layout>
  );
}
