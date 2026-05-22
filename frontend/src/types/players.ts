export type PlayerGameStatistics = {
  matches_played: number;
  goals: number;
  assists: number;
  rating: number | string;
};

export type Player = {
  id: number;
  full_name: string;
  shirt_number: number;
  position: string;
  position_display: string;
  age: number;
  nationality: string;
  height: string | number;
  weight: number;
  join_date: string;
  photo_url?: string;
  short_note?: string;
  attendance_percent?: number;
  average_rating?: number;
  training_count?: number;
  absent_count?: number;
  last_training_status?: string;
  game_statistics?: PlayerGameStatistics;
};

export type PlayerTrainingHistoryItem = {
  id: number | null;
  training?: number;
  player?: number;
  training_title?: string;
  training_date?: string;
  training_detail?: {
    id?: number;
    title: string;
    training_date: string;
  };
  attendance_status: string;
  attendance_status_display?: string;
  rating?: number | null;
  participation_percent?: number;
  injury_status?: string;
  injury_status_display?: string;
  coach_note?: string;
};

export type PlayerProfileStats = {
  attendance_percent?: number;
  average_rating?: number;
  total_marked_trainings?: number;
  training_count?: number;
  absent_trainings?: number;
  absent_count?: number;
  [key: string]: number | string | undefined;
};

export type PlayerProfile = {
  player: Player;
  stats?: PlayerProfileStats;
  attendance_percent?: number;
  average_rating?: number;
  training_count?: number;
  absent_count?: number;
  last_training_status?: string;
  training_history: PlayerTrainingHistoryItem[];
  game_statistics: PlayerGameStatistics;
};
