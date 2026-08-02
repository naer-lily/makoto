package com.makoto.android.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ── Profile ──

@Serializable
data class ProfileResponse(
    val name: String,
    val gender: String,
    val age: Int,
    @SerialName("height_cm") val heightCm: Double,
    @SerialName("weight_kg") val weightKg: Double,
    @SerialName("body_fat_pct") val bodyFatPct: Double,
    @SerialName("target_weight_kg") val targetWeightKg: Double,
    @SerialName("target_date") val targetDate: String,
    @SerialName("activity_level") val activityLevel: String,
    @SerialName("keep_token") val keepToken: String? = null,
    @SerialName("ffm_kg") val ffmKg: Double,
    @SerialName("bmr_kcal") val bmrKcal: Double,
    @SerialName("netee_kcal") val neteeKcal: Double,
    @SerialName("weekly_deficit_needed") val weeklyDeficitNeeded: Double? = null,
    @SerialName("days_remaining") val daysRemaining: Int,
)

// ── Food ──

@Serializable
data class FoodResponse(
    val id: Int,
    val name: String,
    @SerialName("calories_per_100g") val caloriesPer100g: Double,
    @SerialName("protein_per_100g") val proteinPer100g: Double,
    @SerialName("carbs_per_100g") val carbsPer100g: Double,
    @SerialName("fat_per_100g") val fatPer100g: Double,
    @SerialName("fiber_per_100g") val fiberPer100g: Double = 0.0,
    @SerialName("search_keywords") val searchKeywords: List<String> = emptyList(),
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class FoodSearchResult(
    val id: Int,
    val name: String,
    val distance: Int,
)

// ── Body Log ──

@Serializable
data class BodyLogResponse(
    val id: Int,
    @SerialName("log_date") val logDate: String,
    @SerialName("weight_kg") val weightKg: Double,
    @SerialName("body_fat_pct") val bodyFatPct: Double,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

// ── Circumference Log ──

@Serializable
data class CircumferenceLogResponse(
    val id: Int,
    @SerialName("log_date") val logDate: String,
    @SerialName("waist_cm") val waistCm: Double? = null,
    @SerialName("arm_cm") val armCm: Double? = null,
    @SerialName("thigh_cm") val thighCm: Double? = null,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

// ── Diet Log ──

@Serializable
data class DietLogResponse(
    val id: Int,
    @SerialName("log_time") val logTime: String,
    @SerialName("food_id") val foodId: Int,
    val grams: Double,
    val note: String? = null,
    @SerialName("food_name") val foodName: String,
    @SerialName("calories_kcal") val caloriesKcal: Double,
    @SerialName("protein_g") val proteinG: Double,
    @SerialName("carbs_g") val carbsG: Double,
    @SerialName("fat_g") val fatG: Double,
    @SerialName("fiber_g") val fiberG: Double = 0.0,
    @SerialName("food_calories_per_100g") val foodCaloriesPer100g: Double,
    @SerialName("food_protein_per_100g") val foodProteinPer100g: Double,
    @SerialName("food_carbs_per_100g") val foodCarbsPer100g: Double,
    @SerialName("food_fat_per_100g") val foodFatPer100g: Double,
    @SerialName("food_fiber_per_100g") val foodFiberPer100g: Double = 0.0,
    @SerialName("created_at") val createdAt: String,
)

// ── Exercise Log ──

@Serializable
data class ExerciseLogResponse(
    val id: Int,
    @SerialName("log_time") val logTime: String,
    @SerialName("exercise_name") val exerciseName: String,
    @SerialName("duration_desc") val durationDesc: String,
    @SerialName("calories_kcal") val caloriesKcal: Double,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

// ── Painting Log ──

@Serializable
data class PaintingLogResponse(
    val id: Int,
    @SerialName("log_time") val logTime: String,
    @SerialName("file_path") val filePath: String,
    @SerialName("file_id") val fileId: String,
    @SerialName("duration_seconds") val durationSeconds: Double,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

// ── Keep ──

@Serializable
data class FitnessResponse(
    val date: String,
    val atl: Int,
    val ctl: Int,
    val tsb: Int,
)

@Serializable
data class WeeklyLoadResponse(
    @SerialName("week_start") val weekStart: String,
    val load: Int,
)

// ── Dashboard / Today ──

@Serializable
data class TodayResponse(
    val date: String,
    val body: TodayBody? = null,
    val diets: List<TodayDietItem> = emptyList(),
    val exercises: List<TodayExerciseItem> = emptyList(),
    @SerialName("total_intake_kcal") val totalIntakeKcal: Double,
    @SerialName("total_burned_kcal") val totalBurnedKcal: Double,
    @SerialName("total_protein_g") val totalProteinG: Double,
    @SerialName("total_carbs_g") val totalCarbsG: Double,
    @SerialName("total_fat_g") val totalFatG: Double,
    @SerialName("total_fiber_g") val totalFiberG: Double = 0.0,
    @SerialName("netee_kcal") val neteeKcal: Double,
    @SerialName("net_kcal") val netKcal: Double,
    @SerialName("weight_delta_day") val weightDeltaDay: Double? = null,
    @SerialName("body_fat_delta_day") val bodyFatDeltaDay: Double? = null,
    @SerialName("weight_delta_week") val weightDeltaWeek: Double? = null,
    @SerialName("body_fat_delta_week") val bodyFatDeltaWeek: Double? = null,
    @SerialName("deficit_week_kcal") val deficitWeekKcal: Double? = null,
    @SerialName("deficit_month_kcal") val deficitMonthKcal: Double? = null,
    val circumference: CircumferenceLogResponse? = null,
    val atl: Int? = null,
    val ctl: Int? = null,
    val tsb: Int? = null,
    val painting: TodayPainting = TodayPainting(),
)

@Serializable
data class TodayBody(
    @SerialName("weight_kg") val weightKg: Double? = null,
    @SerialName("body_fat_pct") val bodyFatPct: Double? = null,
    val note: String? = null,
)

@Serializable
data class TodayDietItem(
    @SerialName("log_time") val logTime: String,
    @SerialName("food_id") val foodId: Int,
    @SerialName("food_name") val foodName: String,
    val grams: Double,
    @SerialName("calories_kcal") val caloriesKcal: Double,
    @SerialName("protein_g") val proteinG: Double,
    @SerialName("carbs_g") val carbsG: Double,
    @SerialName("fat_g") val fatG: Double,
    @SerialName("fiber_g") val fiberG: Double = 0.0,
)

@Serializable
data class TodayExerciseItem(
    @SerialName("log_time") val logTime: String,
    @SerialName("exercise_name") val exerciseName: String,
    @SerialName("duration_desc") val durationDesc: String,
    @SerialName("calories_kcal") val caloriesKcal: Double,
)

@Serializable
data class TodayPainting(
    @SerialName("painted_today") val paintedToday: Boolean = false,
    @SerialName("duration_seconds") val durationSeconds: Double = 0.0,
    @SerialName("session_count") val sessionCount: Int = 0,
    val sessions: List<TodayPaintingSession> = emptyList(),
    @SerialName("current_streak") val currentStreak: Int = 0,
    @SerialName("longest_streak") val longestStreak: Int = 0,
    @SerialName("total_days") val totalDays: Int = 0,
)

@Serializable
data class TodayPaintingSession(
    @SerialName("log_time") val logTime: String,
    @SerialName("file_id") val fileId: String,
    @SerialName("file_path") val filePath: String,
    @SerialName("duration_seconds") val durationSeconds: Double,
)

// ── Weather ──

@Serializable
data class WeatherDay(
    val date: String,
    @SerialName("temp_max") val tempMax: Double,
    @SerialName("temp_min") val tempMin: Double,
    @SerialName("precip_sum") val precipSum: Double,
    @SerialName("precip_probability") val precipProbability: Int,
    @SerialName("weather_code") val weatherCode: Int,
    @SerialName("weather_desc") val weatherDesc: String,
)

@Serializable
data class WeatherHour(
    val time: String,
    val temp: Double,
    @SerialName("precip_probability") val precipProbability: Int,
    @SerialName("weather_code") val weatherCode: Int,
    @SerialName("weather_desc") val weatherDesc: String,
)

@Serializable
data class WeatherForecastResponse(
    @SerialName("watch_id") val watchId: Int,
    val label: String,
    val latitude: Double,
    val longitude: Double,
    @SerialName("fetched_at") val fetchedAt: String,
    val days: List<WeatherDay> = emptyList(),
    val hours: List<WeatherHour> = emptyList(),
)

// ── Dashboard / Report ──

@Serializable
data class ReportResponse(
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    val days: Int,
    @SerialName("target_weight_kg") val targetWeightKg: Double? = null,
    @SerialName("target_date") val targetDate: String? = null,
    val rows: List<ReportRow> = emptyList(),
    val summary: ReportSummary,
)

@Serializable
data class ReportRow(
    val date: String,
    @SerialName("weight_kg") val weightKg: Double? = null,
    @SerialName("body_fat_pct") val bodyFatPct: Double? = null,
    @SerialName("ffm_kg") val ffmKg: Double? = null,
    @SerialName("fat_kg") val fatKg: Double? = null,
    @SerialName("weight_7d_ma") val weight7dMa: Double? = null,
    @SerialName("body_fat_7d_ma") val bodyFat7dMa: Double? = null,
    @SerialName("ffm_7d_ma") val ffm7dMa: Double? = null,
    @SerialName("fat_7d_ma") val fat7dMa: Double? = null,
    @SerialName("deficit_kcal") val deficitKcal: Double? = null,
    @SerialName("expected_deficit_kcal") val expectedDeficitKcal: Double? = null,
    @SerialName("alpert_limit_kcal") val alpertLimitKcal: Double? = null,
    @SerialName("is_interpolated") val isInterpolated: Boolean = false,
    @SerialName("weekly_loss_kg") val weeklyLossKg: Double? = null,
    @SerialName("intake_kcal") val intakeKcal: Double? = null,
    @SerialName("tdee_kcal") val tdeeKcal: Double? = null,
    val atl: Int? = null,
    val ctl: Int? = null,
    val tsb: Int? = null,
)

@Serializable
data class ReportSummary(
    @SerialName("weight_delta") val weightDelta: Double? = null,
    @SerialName("body_fat_delta") val bodyFatDelta: Double? = null,
    @SerialName("ffm_delta") val ffmDelta: Double? = null,
    @SerialName("fat_delta") val fatDelta: Double? = null,
    @SerialName("weight_7d_ma_delta") val weight7dMaDelta: Double? = null,
    @SerialName("body_fat_7d_ma_delta") val bodyFat7dMaDelta: Double? = null,
    @SerialName("ffm_7d_ma_delta") val ffm7dMaDelta: Double? = null,
    @SerialName("total_deficit_kcal") val totalDeficitKcal: Double? = null,
    @SerialName("total_expected_kcal") val totalExpectedKcal: Double? = null,
    @SerialName("met_target") val metTarget: Boolean = false,
)
