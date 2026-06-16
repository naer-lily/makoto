import http from './client'

export interface ExerciseLogCreate {
  log_time: string
  exercise_name: string
  duration_desc: string
  calories_kcal: number
  note: string | null
}

export interface ExerciseLogResponse {
  id: number
  log_time: string
  exercise_name: string
  duration_desc: string
  calories_kcal: number
  note: string | null
  created_at: string
}

export function fetchExerciseLogs(limit: number = 100): Promise<ExerciseLogResponse[]> {
  return http.get('/exercise-logs', { params: { limit } }).then((r) => r.data)
}

export function createExerciseLog(data: ExerciseLogCreate): Promise<ExerciseLogResponse> {
  return http.post('/exercise-logs', data).then((r) => r.data)
}

export function updateExerciseLog(
  logId: number,
  data: ExerciseLogCreate,
): Promise<ExerciseLogResponse> {
  return http.put(`/exercise-logs/${logId}`, data).then((r) => r.data)
}

export function deleteExerciseLog(logId: number): Promise<void> {
  return http.delete(`/exercise-logs/${logId}`).then(() => undefined)
}
