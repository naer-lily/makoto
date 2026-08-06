package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.*
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response
import java.io.IOException
import okhttp3.ResponseBody.Companion.toResponseBody

class RepositoryTest {

    // ── DashboardRepository ──

    @Test
    fun `getToday returns success`() = runTest {
        val api = object : MakotoApi {
            override suspend fun getToday() = TodayResponse(
                date = "2026-07-09", totalIntakeKcal = 1200.0, totalBurnedKcal = 350.0,
                totalProteinG = 85.0, totalCarbsG = 150.0, totalFatG = 40.0,
                neteeKcal = 2040.0, netKcal = 1190.0,
            )
            override suspend fun getProfile() = error("not needed")
            override suspend fun getFoods() = error("not needed")
            override suspend fun searchFoods(q: String, limit: Int) = error("not needed")
            override suspend fun getFood(foodId: Int) = error("not needed")
            override suspend fun getBodyLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getCircumferenceLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getDietLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getExerciseLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getPaintingLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getReport(startDate: String, endDate: String) = error("not needed")
            override suspend fun getFitness(startDate: String?, endDate: String?) = error("not needed")
            override suspend fun getWeeklyLoad(weekCount: Int?) = error("not needed")
            override suspend fun getWeatherForecast(refresh: Boolean) = error("not needed")
        }
        val repo = DashboardRepository(api)
        val result = repo.getToday()
        assertTrue(result.isSuccess)
        assertEquals(1190.0, result.getOrNull()!!.netKcal, 0.01)
    }

    @Test
    fun `getToday wraps IOException in failure`() = runTest {
        val api = object : MakotoApi {
            override suspend fun getToday(): TodayResponse = throw IOException("Network error")
            override suspend fun getProfile() = error("not needed")
            override suspend fun getFoods() = error("not needed")
            override suspend fun searchFoods(q: String, limit: Int) = error("not needed")
            override suspend fun getFood(foodId: Int) = error("not needed")
            override suspend fun getBodyLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getCircumferenceLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getDietLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getExerciseLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getPaintingLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getReport(startDate: String, endDate: String) = error("not needed")
            override suspend fun getFitness(startDate: String?, endDate: String?) = error("not needed")
            override suspend fun getWeeklyLoad(weekCount: Int?) = error("not needed")
            override suspend fun getWeatherForecast(refresh: Boolean) = error("not needed")
        }
        val repo = DashboardRepository(api)
        val result = repo.getToday()
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is IOException)
    }

    // ── FoodRepository ──

    @Test
    fun `getFoods returns sorted list`() = runTest {
        val api = object : MakotoApi {
            override suspend fun getFoods() = listOf(
                FoodResponse(
                    id = 2, name = "鸡蛋", caloriesPer100g = 155.0, proteinPer100g = 13.0,
                    carbsPer100g = 1.1, fatPer100g = 10.6, fiberPer100g = 0.0,
                    searchKeywords = emptyList(), note = null, createdAt = "2026-01-01T12:00:00",
                ),
                FoodResponse(
                    id = 1, name = "米饭", caloriesPer100g = 116.0, proteinPer100g = 2.6,
                    carbsPer100g = 25.9, fatPer100g = 0.3, fiberPer100g = 0.0,
                    searchKeywords = emptyList(), note = null, createdAt = "2026-01-01T12:00:00",
                ),
            )
            override suspend fun getProfile() = error("not needed")
            override suspend fun getToday() = error("not needed")
            override suspend fun searchFoods(q: String, limit: Int) = error("not needed")
            override suspend fun getFood(foodId: Int) = error("not needed")
            override suspend fun getBodyLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getCircumferenceLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getDietLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getExerciseLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getPaintingLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getReport(startDate: String, endDate: String) = error("not needed")
            override suspend fun getFitness(startDate: String?, endDate: String?) = error("not needed")
            override suspend fun getWeeklyLoad(weekCount: Int?) = error("not needed")
            override suspend fun getWeatherForecast(refresh: Boolean) = error("not needed")
        }
        val repo = FoodRepository(api)
        val result = repo.getFoods()
        assertTrue(result.isSuccess)
    }

    // ── ProfileRepository ──

    @Test
    fun `getProfile handles HttpException`() = runTest {
        val api = object : MakotoApi {
            override suspend fun getProfile(): ProfileResponse =
                throw HttpException(Response.error<Nothing>(401, "".toResponseBody(null)))
            override suspend fun getToday() = error("not needed")
            override suspend fun getFoods() = error("not needed")
            override suspend fun searchFoods(q: String, limit: Int) = error("not needed")
            override suspend fun getFood(foodId: Int) = error("not needed")
            override suspend fun getBodyLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getCircumferenceLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getDietLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getExerciseLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getPaintingLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getReport(startDate: String, endDate: String) = error("not needed")
            override suspend fun getFitness(startDate: String?, endDate: String?) = error("not needed")
            override suspend fun getWeeklyLoad(weekCount: Int?) = error("not needed")
            override suspend fun getWeatherForecast(refresh: Boolean) = error("not needed")
        }
        val repo = ProfileRepository(api)
        val result = repo.getProfile()
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is HttpException)
    }

    // ── DietRepository / ExerciseRepository / BodyRepository ──

    @Test
    fun `diet and exercise repos wrap errors`() = runTest {
        val api = object : MakotoApi {
            override suspend fun getDietLogs(start: String?, end: String?, limit: Int?) =
                throw IOException("offline")
            override suspend fun getExerciseLogs(start: String?, end: String?, limit: Int?) =
                throw IOException("offline")
            override suspend fun getBodyLogs(start: String?, end: String?) =
                throw IOException("offline")
            override suspend fun getProfile() = error("not needed")
            override suspend fun getToday() = error("not needed")
            override suspend fun getFoods() = error("not needed")
            override suspend fun searchFoods(q: String, limit: Int) = error("not needed")
            override suspend fun getFood(foodId: Int) = error("not needed")
            override suspend fun getCircumferenceLogs(start: String?, end: String?) = error("not needed")
            override suspend fun getPaintingLogs(start: String?, end: String?, limit: Int?) = error("not needed")
            override suspend fun getReport(startDate: String, endDate: String) = error("not needed")
            override suspend fun getFitness(startDate: String?, endDate: String?) = error("not needed")
            override suspend fun getWeeklyLoad(weekCount: Int?) = error("not needed")
            override suspend fun getWeatherForecast(refresh: Boolean) = error("not needed")
        }
        assertTrue(DietRepository(api).getDietLogs().isFailure)
        assertTrue(ExerciseRepository(api).getExerciseLogs().isFailure)
        assertTrue(BodyRepository(api).getBodyLogs().isFailure)
    }
}
