import http from './client'

export interface FitnessRecord {
  date: string
  atl: number
  ctl: number
  tsb: number
}

export interface WeeklyLoadRecord {
  user_id: string
  week_start: string
  training_load: number | null
  load_lower: number
  load_upper: number
}

export function fetchFitness(startDate?: string, endDate?: string): Promise<FitnessRecord[]> {
  const params: Record<string, string> = {}
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  return http.get('/keep/fitness', { params }).then((r) => r.data)
}

export function fetchWeeklyLoad(weekCount?: number): Promise<WeeklyLoadRecord[]> {
  const params: Record<string, string> = {}
  if (weekCount !== undefined) params.week_count = String(weekCount)
  return http.get('/keep/weekly-load', { params }).then((r) => r.data)
}
