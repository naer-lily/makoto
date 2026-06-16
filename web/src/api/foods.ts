import http from './client'

export interface FoodCreate {
  name: string
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
  search_keywords: string[]
  note: string | null
}

export interface FoodResponse extends FoodCreate {
  id: number
  created_at: string
}

export interface FoodSearchResult {
  id: number
  name: string
  distance: number
}

export function fetchFoods(): Promise<FoodResponse[]> {
  return http.get('/foods').then((r) => r.data)
}

export function fetchFood(foodId: number): Promise<FoodResponse> {
  return http.get(`/foods/${foodId}`).then((r) => r.data)
}

export function createFood(data: FoodCreate): Promise<FoodResponse> {
  return http.post('/foods', data).then((r) => r.data)
}

export function updateFood(foodId: number, data: FoodCreate): Promise<FoodResponse> {
  return http.put(`/foods/${foodId}`, data).then((r) => r.data)
}

export function deleteFood(foodId: number): Promise<void> {
  return http.delete(`/foods/${foodId}`).then(() => undefined)
}

export function searchFoods(query: string, limit: number = 20): Promise<FoodSearchResult[]> {
  return http.get('/foods/search', { params: { q: query, limit } }).then((r) => r.data)
}
