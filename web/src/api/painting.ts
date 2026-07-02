import http from './client'

export interface PaintingLogCreate {
  log_time: string
  file_path: string
  file_id: string
  duration_seconds: number
  note: string | null
}

export interface PaintingLogResponse {
  id: number
  log_time: string
  file_path: string
  file_id: string
  duration_seconds: number
  note: string | null
  created_at: string
}

export interface TodayPaintingItem {
  log_time: string
  file_id: string
  file_path: string
  duration_seconds: number
}

export interface TodayPainting {
  painted_today: boolean
  duration_seconds: number
  session_count: number
  sessions: TodayPaintingItem[]
  current_streak: number
  longest_streak: number
  total_days: number
}

export function fetchPaintingLogs(
  limit: number = 500,
  start?: string,
  end?: string,
): Promise<PaintingLogResponse[]> {
  return http
    .get('/painting-logs', { params: { limit, start, end } })
    .then((r) => r.data)
}

export function createPaintingLog(data: PaintingLogCreate): Promise<PaintingLogResponse> {
  return http.post('/painting-logs', data).then((r) => r.data)
}

export function updatePaintingLog(
  logId: number,
  data: PaintingLogCreate,
): Promise<PaintingLogResponse> {
  return http.put(`/painting-logs/${logId}`, data).then((r) => r.data)
}

export function deletePaintingLog(logId: number): Promise<void> {
  return http.delete(`/painting-logs/${logId}`).then(() => undefined)
}
