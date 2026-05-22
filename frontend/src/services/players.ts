import { api, ApiEnvelope } from '../app/services/api';
import type { PlayerProfile } from '../types/players';

export async function getPlayerProfile(id: number | string) {
  const response = await api.get<ApiEnvelope<PlayerProfile>>(`/players/${id}/profile/`);
  return response.data.data;
}
