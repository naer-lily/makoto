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

export function fetchFitness(): Promise<FitnessRecord[]> {
  return http.get('/keep/fitness').then((r) => r.data)
}

export function fetchWeeklyLoad(): Promise<WeeklyLoadRecord[]> {
  return http.get('/keep/weekly-load').then((r) => r.data)
}
