package com.makoto.android.data.remote

import com.makoto.android.data.remote.dto.*
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface MakotoApi {

    @GET("api/v1/profile")
    suspend fun getProfile(): ProfileResponse

    @GET("api/v1/foods")
    suspend fun getFoods(): List<FoodResponse>

    @GET("api/v1/foods/search")
    suspend fun searchFoods(
        @Query("q") q: String,
        @Query("limit") limit: Int = 20,
    ): List<FoodSearchResult>

    @GET("api/v1/foods/{food_id}")
    suspend fun getFood(@Path("food_id") foodId: Int): FoodResponse

    @GET("api/v1/body-logs")
    suspend fun getBodyLogs(
        @Query("start") start: String? = null,
        @Query("end") end: String? = null,
    ): List<BodyLogResponse>

    @GET("api/v1/circumference-logs")
    suspend fun getCircumferenceLogs(
        @Query("start") start: String? = null,
        @Query("end") end: String? = null,
    ): List<CircumferenceLogResponse>

    @GET("api/v1/diet-logs")
    suspend fun getDietLogs(
        @Query("start") start: String? = null,
        @Query("end") end: String? = null,
        @Query("limit") limit: Int? = null,
    ): List<DietLogResponse>

    @GET("api/v1/exercise-logs")
    suspend fun getExerciseLogs(
        @Query("start") start: String? = null,
        @Query("end") end: String? = null,
        @Query("limit") limit: Int? = null,
    ): List<ExerciseLogResponse>

    @GET("api/v1/painting-logs")
    suspend fun getPaintingLogs(
        @Query("start") start: String? = null,
        @Query("end") end: String? = null,
        @Query("limit") limit: Int? = null,
    ): List<PaintingLogResponse>

    @GET("api/v1/dashboard/today")
    suspend fun getToday(): TodayResponse

    @GET("api/v1/dashboard/report")
    suspend fun getReport(
        @Query("start_date") startDate: String,
        @Query("end_date") endDate: String,
    ): ReportResponse

    @GET("api/v1/keep/fitness")
    suspend fun getFitness(
        @Query("start_date") startDate: String? = null,
        @Query("end_date") endDate: String? = null,
    ): List<FitnessResponse>

    @GET("api/v1/keep/weekly-load")
    suspend fun getWeeklyLoad(
        @Query("week_count") weekCount: Int? = null,
    ): List<WeeklyLoadResponse>

    @GET("api/v1/weather/forecast")
    suspend fun getWeatherForecast(
        @Query("refresh") refresh: Boolean = false,
    ): List<WeatherForecastResponse>
}
