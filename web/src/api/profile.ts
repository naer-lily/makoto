import http from './client'

export interface ProfileCreate {
  name: string
  gender: string
  age: number
  height_cm: number
  weight_kg: number
  body_fat_pct: number
  target_weight_kg: number
  target_date: string
  activity_level: string
  keep_token: string | null
}

export interface ProfileResponse extends ProfileCreate {
  ffm_kg: number
  bmr_kcal: number
  ree_kcal: number
  weekly_deficit_needed: number | null
  days_remaining: number
}

export function fetchProfile(): Promise<ProfileResponse> {
  return http.get('/profile').then((r) => r.data)
}

export function updateProfile(data: ProfileCreate): Promise<ProfileResponse> {
  return http.put('/profile', data).then((r) => r.data)
}
