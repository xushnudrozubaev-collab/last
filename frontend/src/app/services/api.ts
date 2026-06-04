import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000/api');

export type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  full_name: string;
  club_name: string;
  role: string;
  phone: string;
  language: string;
  theme: string;
};

export type Player = {
  id: number;
  full_name: string;
  shirt_number: number;
  position: string;
  position_display: string;
  age: number;
  nationality: string;
  height: string;
  weight: number;
  join_date: string;
  photo_url: string;
  short_note: string;
  attendance_percent: number;
  average_rating: number;
  training_count: number;
  absent_count: number;
  late_count: number;
  last_training_status: string;
  game_statistics: {
    matches_played: number;
    goals: number;
    assists: number;
    rating: number | string;
  };
};

export type PlayerPayload = Partial<Player> & {
  photo?: File | null;
};

export type Training = {
  id: number;
  title: string;
  training_type: string;
  training_type_display: string;
  training_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  duration_display: string;
  location: string;
  note: string;
  attendance_total: number;
  attendance_present: number;
  attendance_percent: number;
  attendance_display: string;
  average_rating: number;
  marked_count: number;
};

export type AttendanceRecord = {
  id: number | null;
  training: number;
  player: number;
  player_detail: Player;
  attendance_status: string;
  attendance_status_display: string;
  physical_condition: string;
  physical_condition_display: string;
  activity_level: string;
  activity_level_display: string;
  discipline: string;
  discipline_display: string;
  rating: number;
  attended_minutes: number;
  training_duration_minutes: number;
  participation_percent: number;
  fatigue_level: number;
  pain_level: number;
  sleep_quality: number;
  activity_score: number;
  heart_rate: number | null;
  blood_pressure: string;
  body_temperature: string | number | null;
  measured_weight: string | number | null;
  measured_height: number | null;
  oxygen_saturation: number | null;
  respiratory_rate: number | null;
  injury_status: string;
  injury_status_display: string;
  injury_note: string;
  coach_note: string;
};

export type Match = {
  id: number;
  home_team: string;
  away_team: string;
  home_logo_url: string;
  away_logo_url: string;
  match_date: string;
  match_time: string;
  stadium: string;
  status: string;
  status_display: string;
  home_score: number | null;
  away_score: number | null;
  attendance: number | null;
  referee: string;
  possession_percent: number;
  shots: number;
  shots_on_target: number;
  corners: number;
  yellow_cards: number;
  red_cards: number;
  note: string;
  result_label: string;
};

export type MatchStats = {
  total: number;
  wins: number;
  draws: number;
  losses: number;
};

export type DashboardData = {
  period?: string;
  period_label?: string;
  total_players: number;
  today_trainings: number;
  team_attendance_percent: number;
  team_average_rating: number;
  period_stats?: {
    trainings_count: number;
    matches_count: number;
    match_record: { wins: number; draws: number; losses: number };
    goals: number;
    average_attendance_percent: number;
    average_rating: number;
    injury_related_count: number;
    trends: {
      trainings: number;
      matches: number;
      goals: number;
      attendance: number;
      rating: number;
    };
  };
  top_recent_active_player?: {
    player_id: number;
    player_name: string;
    average_activity: number;
    trainings_count: number;
  } | null;
  recent_trainings: Training[];
  period_trainings?: Training[];
  period_active_players?: Array<{
    player_id: number;
    full_name: string;
    score: number;
    trainings_count: number;
  }>;
  recent_matches: Match[];
  recent_completed_matches?: Match[];
  period_completed_matches?: Match[];
  injured_players: Array<{
    player_id: number;
    player_name: string;
    training: string;
    injury_status: string;
    note: string;
  }>;
  warnings: Array<{ type: string; message: string; date: string }>;
  latest_comments?: Array<{
    player_id: number;
    player_name: string;
    training: string;
    comment: string;
    date: string;
  }>;
};

export type StatisticsData = {
  period?: string;
  summary?: {
    attendance_percent: number;
    average_rating: number;
    average_activity: number;
    injury_count: number;
    trainings_count: number;
    trends: {
      attendance: number;
      rating: number;
      activity: number;
      injury: number;
    };
  };
  team: {
    total_trainings: number;
    total_records: number;
    average_attendance_percent: number;
    average_activity_score: number;
    average_rating: number;
    average_fatigue_level: number;
    average_heart_rate: number;
    today_attendance_percent: number;
    injury_related_count: number;
    status_counts: Record<string, number>;
  };
  players: Array<Record<string, number | string>>;
  top_active_players: Array<Record<string, number | string>>;
  most_absent_players: Array<Record<string, number | string>>;
  injured_players: Array<Record<string, number | string>>;
  matches: {
    total: number;
    wins: number;
    draws: number;
    losses: number;
    win_percent: number;
    goals_for: number;
    goals_against: number;
    goal_difference: number;
  };
  training_types: Array<{
    type: string;
    label: string;
    trainings_count: number;
    attendance_percent: number;
    average_rating: number;
  }>;
};

export type AttendanceTrendPoint = {
  date: string;
  present: number;
  total: number;
};

export type GoalAssistPoint = {
  player_id: number;
  player_name: string;
  goals: number;
  assists: number;
};

export type StatisticsPlayerRow = {
  player_id: number;
  full_name: string;
  short_name: string;
  initials: string;
  position: string;
  position_display: string;
  present: number;
  total: number;
  avg_rating: number;
  avg_activity: number;
  goals: number;
  assists: number;
  attendance_percent: number;
};

export type StatisticsRankings = {
  most_present: StatisticsPlayerRow[];
  top_rated: StatisticsPlayerRow[];
};

export type ReportData = {
  report_type?: 'attendance' | 'performance' | 'matches' | 'player' | 'training' | 'month';
  title: string;
  subtitle: string;
  summary: Array<{ label: string; value: string | number }>;
  rows: Array<Record<string, string | number>>;
  most_absent?: Array<{ player_id: number; player_name: string; absent: number }>;
  injury_overview?: {
    players: Array<{ player_id: number; player_name: string; status: string; tone: string }>;
    healthy_count: number;
  };
  top_rating?: Array<{ player_id: number; player_name: string; value: number }>;
  top_activity?: Array<{ player_id: number; player_name: string; value: number }>;
};

export type ReportParams = {
  report_type: 'attendance' | 'performance' | 'matches' | 'player' | 'training' | 'month';
  start_date?: string;
  end_date?: string;
  player_id?: number;
  training_id?: number;
  month?: string;
};

export type PlayerProfile = {
  player: Player;
  stats: Record<string, number | string>;
  training_history: AttendanceRecord[];
  progress: Array<{ training_id: number; date: string; title: string; rating: number; attendance: string }>;
  comments: Array<{ date: string; training: string; comment: string }>;
  game_statistics: {
    matches_played: number;
    goals: number;
    assists: number;
    rating: number;
  };
};

export const tokenStore = {
  getAccess() {
    return localStorage.getItem('murabbiy_access_token');
  },
  getRefresh() {
    return localStorage.getItem('murabbiy_refresh_token');
  },
  set(access: string, refresh: string) {
    localStorage.setItem('murabbiy_access_token', access);
    localStorage.setItem('murabbiy_refresh_token', refresh);
  },
  clear() {
    localStorage.removeItem('murabbiy_access_token');
    localStorage.removeItem('murabbiy_refresh_token');
  },
};

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let redirecting = false;
let refreshRequest: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = String(originalRequest?.url || '');
    const canRefresh =
      error.response?.status === 401
      && originalRequest
      && !originalRequest._retry
      && !requestUrl.includes('/auth/login/')
      && !requestUrl.includes('/auth/refresh/')
      && tokenStore.getRefresh();

    if (canRefresh) {
      originalRequest._retry = true;
      try {
        if (!refreshRequest) {
          refreshRequest = axios
            .post<{ access: string }>(`${API_BASE_URL}/auth/refresh/`, { refresh: tokenStore.getRefresh() })
            .then((response) => response.data.access)
            .finally(() => {
              refreshRequest = null;
            });
        }
        const access = await refreshRequest;
        const refresh = tokenStore.getRefresh();
        if (!refresh) throw new Error('Refresh token topilmadi.');
        tokenStore.set(access, refresh);
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch {
        tokenStore.clear();
      }
    }

    if (error.response?.status === 401 && !redirecting && !requestUrl.includes('/auth/login/')) {
      redirecting = true;
      tokenStore.clear();
      window.dispatchEvent(new Event('auth:logout'));
      setTimeout(() => {
        redirecting = false;
      }, 500);
    }
    return Promise.reject(error);
  },
);

export function getApiError(error: unknown, fallback = 'Amalni bajarishda xatolik yuz berdi.'): string {
  const readMessage = (value: unknown): string | null => {
    if (!value) return null;
    if (typeof value === 'string') return value;
    if (Array.isArray(value)) {
      for (const item of value) {
        const message = readMessage(item);
        if (message) return message;
      }
      return null;
    }
    if (typeof value === 'object') {
      for (const [key, item] of Object.entries(value)) {
        const message = readMessage(item);
        if (message) return key === 'non_field_errors' ? message : `${key}: ${message}`;
      }
    }
    return null;
  };

  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.message === 'string') return data.message;
    if (typeof data?.detail === 'string') return data.detail;
    const message = readMessage(data);
    if (message) return message;
  }
  return fallback;
}

function unwrap<T>(response: { data: ApiEnvelope<T> }): T {
  return response.data.data;
}

function playerPayloadToFormData(data: PlayerPayload) {
  const formData = new FormData();
  const writableFields: Array<keyof PlayerPayload> = [
    'full_name',
    'shirt_number',
    'position',
    'age',
    'nationality',
    'height',
    'weight',
    'join_date',
    'short_note',
    'photo',
  ];

  writableFields.forEach((field) => {
    const value = data[field];
    if (value === undefined || value === null) return;
    if (field === 'photo') {
      if (value instanceof File) {
        formData.append(field, value);
      }
      return;
    }
    formData.append(field, String(value));
  });

  return formData;
}

export const authAPI = {
  async login(username: string, password: string) {
    const response = await api.post<{ access: string; refresh: string; user: User }>('/auth/login/', { username, password });
    tokenStore.set(response.data.access, response.data.refresh);
    return response.data.user;
  },
  async register(payload: {
    username: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    email: string;
    club_name: string;
  }) {
    const response = await api.post<ApiEnvelope<{ access: string; refresh: string; user: User }>>('/auth/register/', payload);
    tokenStore.set(response.data.data.access, response.data.data.refresh);
    return response.data.data.user;
  },
  async me() {
    return unwrap<User>(await api.get<ApiEnvelope<User>>('/auth/me/'));
  },
  logout() {
    tokenStore.clear();
  },
};

export const playersAPI = {
  async list(params?: { search?: string; position?: string }) {
    const response = await api.get<Player[]>('/players/', { params });
    return response.data;
  },
  async detail(id: number) {
    const response = await api.get<Player>(`/players/${id}/`);
    return response.data;
  },
  async profile(id: number) {
    return unwrap<PlayerProfile>(await api.get<ApiEnvelope<PlayerProfile>>(`/players/${id}/profile/`));
  },
  async create(data: PlayerPayload) {
    const response = await api.post<Player>('/players/', playerPayloadToFormData(data), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  async update(id: number, data: PlayerPayload) {
    const response = await api.patch<Player>(`/players/${id}/`, playerPayloadToFormData(data), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  async remove(id: number) {
    await api.delete(`/players/${id}/`);
  },
};

export const trainingsAPI = {
  async list(params?: { search?: string; training_type?: string; date?: string }) {
    const response = await api.get<Training[] | ApiEnvelope<Training[]>>('/trainings/', { params });
    return Array.isArray(response.data) ? response.data : response.data.data;
  },
  async detail(id: number) {
    const response = await api.get<Training>(`/trainings/${id}/`);
    return response.data;
  },
  async create(data: Partial<Training>) {
    const response = await api.post<Training | ApiEnvelope<Training>>('/trainings/', data);
    return 'data' in response.data ? response.data.data : response.data;
  },
  async update(id: number, data: Partial<Training>) {
    const response = await api.patch<Training>(`/trainings/${id}/`, data);
    return response.data;
  },
  async remove(id: number) {
    await api.delete(`/trainings/${id}/`);
  },
  async attendance(id: number) {
    return unwrap<{ training: Training; records: AttendanceRecord[] }>(
      await api.get<ApiEnvelope<{ training: Training; records: AttendanceRecord[] }>>(`/trainings/${id}/attendance/`),
    );
  },
  async saveAttendance(id: number, records: AttendanceRecord[]) {
    return unwrap<AttendanceRecord[]>(
      await api.post<ApiEnvelope<AttendanceRecord[]>>(`/trainings/${id}/attendance/`, { records }),
    );
  },
};

export const matchesAPI = {
  async list(params?: { search?: string; status?: string; date?: string; ordering?: string }) {
    const response = await api.get<Match[]>('/matches/', { params });
    return response.data;
  },
  async stats(params?: { search?: string; status?: string; date?: string; ordering?: string }) {
    return unwrap<MatchStats>(await api.get<ApiEnvelope<MatchStats>>('/matches/stats/', { params }));
  },
  async detail(id: number) {
    const response = await api.get<Match>(`/matches/${id}/`);
    return response.data;
  },
  async create(data: Partial<Match>) {
    const response = await api.post<Match>('/matches/', data);
    return response.data;
  },
  async update(id: number, data: Partial<Match>) {
    const response = await api.patch<Match>(`/matches/${id}/`, data);
    return response.data;
  },
  async remove(id: number) {
    await api.delete(`/matches/${id}/`);
  },
};

export const dashboardAPI = {
  async get(period?: 'week' | 'month' | 'season') {
    return unwrap<DashboardData>(await api.get<ApiEnvelope<DashboardData>>('/dashboard/', { params: period ? { period } : undefined }));
  },
};

export const statisticsAPI = {
  async get(period?: 'week' | 'month' | 'season') {
    return unwrap<StatisticsData>(await api.get<ApiEnvelope<StatisticsData>>('/statistics/', { params: period ? { period } : undefined }));
  },
  async attendanceTrend(period: 'week' | 'month' | 'season') {
    return unwrap<AttendanceTrendPoint[]>(await api.get<ApiEnvelope<AttendanceTrendPoint[]>>('/statistics/attendance-trend/', { params: { period } }));
  },
  async goalsAssists(period: 'week' | 'month' | 'season') {
    return unwrap<GoalAssistPoint[]>(await api.get<ApiEnvelope<GoalAssistPoint[]>>('/statistics/goals-assists/', { params: { period } }));
  },
  async rankings(period: 'week' | 'month' | 'season') {
    return unwrap<StatisticsRankings>(await api.get<ApiEnvelope<StatisticsRankings>>('/statistics/rankings/', { params: { period } }));
  },
  async players(period: 'week' | 'month' | 'season') {
    return unwrap<StatisticsPlayerRow[]>(await api.get<ApiEnvelope<StatisticsPlayerRow[]>>('/statistics/players/', { params: { period } }));
  },
};

export const reportsAPI = {
  async get(params: ReportParams) {
    return unwrap<ReportData>(await api.get<ApiEnvelope<ReportData>>('/reports/', { params }));
  },
  async download(params: ReportParams) {
    const response = await api.get<Blob>('/reports/print/', { params, responseType: 'blob' });
    return response.data;
  },
};

export const settingsAPI = {
  async get() {
    return unwrap<User>(await api.get<ApiEnvelope<User>>('/settings/'));
  },
  async update(data: Partial<User>) {
    return unwrap<User>(await api.patch<ApiEnvelope<User>>('/settings/', data));
  },
  async changePassword(current_password: string, new_password: string) {
    return unwrap<Record<string, never>>(
      await api.post<ApiEnvelope<Record<string, never>>>('/settings/password/', { current_password, new_password }),
    );
  },
};

// AI Assistant Types
export type AIMessage = {
  id: number;
  role: 'user' | 'assistant';
  role_display: string;
  content: string;
  created_at: string;
};

export type AIConversation = {
  id: number;
  title: string;
  is_active: boolean;
  message_count: number;
  last_message?: {
    content: string;
    role: string;
    created_at: string;
  } | null;
  created_at: string;
  updated_at: string;
};

export type AIConversationDetail = {
  id: number;
  title: string;
  is_active: boolean;
  messages: AIMessage[];
  created_at: string;
  updated_at: string;
};

export type AIChatResponse = {
  conversation_id: number;
  user_message: AIMessage;
  ai_message: AIMessage;
};

export type AIQuickReportType = 'team_analysis' | 'player_assessment' | 'training_plan' | 'strengths_weaknesses' | 'next_match';

// AI Assistant API
export const aiAssistantAPI = {
  async listConversations() {
    return unwrap<AIConversation[]>(await api.get<ApiEnvelope<AIConversation[]>>('/ai/conversations/'));
  },
  async getConversation(id: number) {
    return unwrap<AIConversationDetail>(await api.get<ApiEnvelope<AIConversationDetail>>(`/ai/conversations/${id}/`));
  },
  async createConversation(title: string) {
    return unwrap<AIConversationDetail>(await api.post<ApiEnvelope<AIConversationDetail>>('/ai/conversations/', { title }));
  },
  async updateConversation(id: number, data: { title?: string; is_active?: boolean }) {
    return unwrap<AIConversation>(await api.patch<ApiEnvelope<AIConversation>>(`/ai/conversations/${id}/`, data));
  },
  async deleteConversation(id: number) {
    await api.delete(`/ai/conversations/${id}/`);
  },
  async chat(message: string, conversation_id?: number | null) {
    return unwrap<AIChatResponse>(
      await api.post<ApiEnvelope<AIChatResponse>>('/ai/chat/', {
        message,
        conversation_id: conversation_id || null,
      })
    );
  },
  async quickReport(report_type: AIQuickReportType) {
    return unwrap<{ report: string; content: string; report_type: string }>(
      await api.post<ApiEnvelope<{ report: string; content: string; report_type: string }>>('/ai/quick-report/', { report_type })
    );
  },
};
