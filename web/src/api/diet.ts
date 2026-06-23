import http from './client'

export interface DietLogCreate {
  log_time: string
  food_id: number
  grams: number
  note: string | null
}

export interface DietLogResponse {
  id: number
  log_time: string
  food_id: number
  food_name: string
  grams: number
  note: string | null
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  created_at: string
}

export function fetchDietLogs(limit: number = 100): Promise<DietLogResponse[]> {
  return http.get('/diet-logs', { params: { limit } }).then((r) => r.data)
}

export function createDietLog(data: DietLogCreate): Promise<DietLogResponse> {
  return http.post('/diet-logs', data).then((r) => r.data)
}

export function updateDietLog(logId: number, data: DietLogCreate): Promise<DietLogResponse> {
  return http.put(`/diet-logs/${logId}`, data).then((r) => r.data)
}

export function deleteDietLog(logId: number): Promise<void> {
  return http.delete(`/diet-logs/${logId}`).then(() => undefined)
}
