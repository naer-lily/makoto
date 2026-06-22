import http from './client'

export interface BodyRecord {
  id: number
  log_date: string
  weight_kg: number
  body_fat_pct: number
  note: string | null
  created_at: string
}

export interface BodyCreate {
  log_date: string
  weight_kg: number
  body_fat_pct: number
  note: string | null
}

export function fetchBodyLogs(): Promise<BodyRecord[]> {
  return http.get('/body-logs').then((r) => r.data)
}

export function createBodyLog(data: BodyCreate): Promise<BodyRecord> {
  return http.post('/body-logs', data).then((r) => r.data)
}

export function deleteBodyLog(id: number): Promise<void> {
  return http.delete(`/body-logs/${id}`)
}
