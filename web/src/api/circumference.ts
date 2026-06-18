import http from './client'

export interface CircumferenceRecord {
  id: number
  log_date: string
  waist_cm: number | null
  arm_cm: number | null
  thigh_cm: number | null
  note: string | null
  created_at: string
}

export interface CircumferenceCreate {
  log_date: string
  waist_cm: number | null
  arm_cm: number | null
  thigh_cm: number | null
  note: string | null
}

export function fetchCircumferenceLogs(): Promise<CircumferenceRecord[]> {
  return http.get('/circumference-logs').then((r) => r.data)
}

export function createCircumferenceLog(
  data: CircumferenceCreate,
): Promise<CircumferenceRecord> {
  return http.post('/circumference-logs', data).then((r) => r.data)
}

export function deleteCircumferenceLog(id: number): Promise<void> {
  return http.delete(`/circumference-logs/${id}`)
}
