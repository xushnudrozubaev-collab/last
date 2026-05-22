import { api, getApiError, Training } from '../app/services/api';

type Envelope<T> = { success: boolean; data: T };

export type TrainingFilters = {
  search?: string;
  type?: string;
  date?: string;
};

export type TrainingCreatePayload = Pick<
  Training,
  'title' | 'training_type' | 'training_date' | 'start_time' | 'end_time' | 'location' | 'note'
>;

function dataOf<T>(payload: T | Envelope<T>) {
  return typeof payload === 'object' && payload !== null && 'data' in payload ? payload.data : payload;
}

export const trainingsService = {
  async list(filters?: TrainingFilters) {
    const response = await api.get<Training[] | Envelope<Training[]>>('/trainings/', { params: filters });
    return dataOf(response.data);
  },

  async create(payload: TrainingCreatePayload) {
    const response = await api.post<Training | Envelope<Training>>('/trainings/', payload);
    return dataOf(response.data);
  },
};

export { getApiError };
