import http from './client'

export interface TodayBody {
  weight_kg: number | null
  body_fat_pct: number | null
  note: string | null
}

export interface CircumferenceResponse {
  id: number
  log_date: string
  waist_cm: number | null
  arm_cm: number | null
  thigh_cm: number | null
  note: string | null
  created_at: string
}

export interface TodayDietItem {
  log_time: string
  food_name: string
  grams: number
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
}

export interface TodayExerciseItem {
  log_time: string
  exercise_name: string
  duration_desc: string
  calories_kcal: number
}

export interface TodayResponse {
  date: string
  body: TodayBody | null
  diets: TodayDietItem[]
  exercises: TodayExerciseItem[]
  total_intake_kcal: number
  total_burned_kcal: number
  total_protein_g: number
  total_carbs_g: number
  total_fat_g: number
  netee_kcal: number
  net_kcal: number
  weight_delta_day: number | null
  body_fat_delta_day: number | null
  weight_delta_week: number | null
  body_fat_delta_week: number | null
  circumference: CircumferenceResponse | null
}

export interface ReportRow {
  date: string
  weight_kg: number
  body_fat_pct: number
  ffm_kg: number
  fat_kg: number
  ma_weight_kg: number
  ma_body_fat_pct: number
  ma_ffm_kg: number
  ma_fat_kg: number
  deficit_kcal: number
  expected_deficit_kcal: number | null
  ma_deficit_kcal: number | null
  alpert_limit_kcal: number
  is_interpolated: boolean
  weekly_loss_kg: number | null
}

export interface ReportSummary {
  weight_delta: number
  body_fat_delta: number
  ffm_delta: number
  ma_weight_delta: number
  ma_body_fat_delta: number
  ma_ffm_delta: number
  total_deficit_kcal: number
  total_expected_kcal: number | null
  met_target: boolean | null
}

export interface ReportResponse {
  start_date: string
  end_date: string
  days: number
  target_weight_kg: number | null
  target_date: string | null
  rows: ReportRow[]
  summary: ReportSummary
}

export function fetchToday(): Promise<TodayResponse> {
  return http.get('/dashboard/today').then((r) => r.data)
}

export function fetchReport(
  startDate?: string,
  endDate?: string,
): Promise<ReportResponse> {
  const params: Record<string, string> = {}
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  return http.get('/dashboard/report', { params }).then((r) => r.data)
}

export interface ProfileResponse {
  name: string
  gender: string
  age: number
  height_cm: number
  weight_kg: number
  body_fat_pct: number
  target_weight_kg: number
  target_date: string
  activity_level: string
  ffm_kg: number
  bmr_kcal: number
  netee_kcal: number
  weekly_deficit_needed: number | null
  days_remaining: number
}

export function fetchProfile(): Promise<ProfileResponse> {
  return http.get('/profile').then((r) => r.data)
}
