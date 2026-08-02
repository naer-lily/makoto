package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.FoodResponse
import com.makoto.android.data.remote.dto.FoodSearchResult

class FoodRepository(private val api: MakotoApi) {

    suspend fun getFoods(): Result<List<FoodResponse>> = runCatching {
        api.getFoods()
    }

    suspend fun searchFoods(q: String, limit: Int = 20): Result<List<FoodSearchResult>> = runCatching {
        api.searchFoods(q, limit)
    }

    suspend fun getFood(foodId: Int): Result<FoodResponse> = runCatching {
        api.getFood(foodId)
    }
}
