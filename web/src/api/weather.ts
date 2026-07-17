import http from './client'

export interface WeatherWatch {
  id: number
  label: string
  latitude: number
  longitude: number
  created_at: string
}

export interface WeatherWatchCreate {
  label: string
  latitude: number
  longitude: number
}

export interface WeatherWatchUpdate {
  label?: string
  latitude?: number
  longitude?: number
}

export interface WeatherHour {
  time: string
  temp: number
  precip_probability: number
  weather_code: number
  weather_desc: string
}

export interface WeatherDay {
  date: string
  temp_max: number
  temp_min: number
  precip_sum: number
  precip_probability: number
  weather_code: number
  weather_desc: string
}

export interface WeatherForecast {
  watch_id: number
  label: string
  latitude: number
  longitude: number
  fetched_at: string
  days: WeatherDay[]
  hours: WeatherHour[]
}

export function fetchWatches(): Promise<WeatherWatch[]> {
  return http.get('/weather/watches').then((r) => r.data)
}

export function createWatch(data: WeatherWatchCreate): Promise<WeatherWatch> {
  return http.post('/weather/watches', data).then((r) => r.data)
}

export function updateWatch(id: number, data: WeatherWatchUpdate): Promise<WeatherWatch> {
  return http.put(`/weather/watches/${id}`, data).then((r) => r.data)
}

export function deleteWatch(id: number): Promise<WeatherWatch> {
  return http.delete(`/weather/watches/${id}`).then((r) => r.data)
}

export function fetchAllForecasts(refresh?: boolean): Promise<WeatherForecast[]> {
  const params = refresh ? { refresh: true } : undefined
  return http.get('/weather/forecast', { params }).then((r) => r.data)
}

export function fetchForecast(id: number, refresh?: boolean): Promise<WeatherForecast> {
  const params = refresh ? { refresh: true } : undefined
  return http.get(`/weather/forecast/${id}`, { params }).then((r) => r.data)
}
