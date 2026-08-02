package com.makoto.android.data.remote.dto

import com.makoto.android.data.remote.makotoJson
import org.junit.Assert.*
import org.junit.Test

class ModelsParsingTest {

    @Test
    fun `parse ProfileResponse`() {
        val raw = """{
            "name":"测试","gender":"male","age":30,"height_cm":178.0,"weight_kg":78.0,
            "body_fat_pct":21.0,"target_weight_kg":72.0,"target_date":"2026-09-15",
            "activity_level":"sedentary","keep_token":"abc",
            "ffm_kg":61.6,"bmr_kcal":1700.0,"netee_kcal":2040.0,
            "weekly_deficit_needed":3500.0,"days_remaining":433
        }"""
        val p = makotoJson.decodeFromString<ProfileResponse>(raw)
        assertEquals("测试", p.name)
        assertEquals(2040.0, p.neteeKcal, 0.01)
        assertEquals("abc", p.keepToken)
    }

    @Test
    fun `parse ProfileResponse null keep_token`() {
        val raw = """{
            "name":"x","gender":"female","age":25,"height_cm":165.0,"weight_kg":55.0,
            "body_fat_pct":20.0,"target_weight_kg":50.0,"target_date":"2026-01-01",
            "activity_level":"moderate","keep_token":null,
            "ffm_kg":44.0,"bmr_kcal":1400.0,"netee_kcal":2200.0,"days_remaining":100
        }"""
        val p = makotoJson.decodeFromString<ProfileResponse>(raw)
        assertNull(p.keepToken)
    }

    @Test
    fun `parse ProfileResponse ignores unknown fields`() {
        val raw = """{
            "name":"x","gender":"male","age":1,"height_cm":1.0,"weight_kg":1.0,
            "body_fat_pct":1.0,"target_weight_kg":1.0,"target_date":"2026-01-01",
            "activity_level":"sedentary","ffm_kg":1.0,"bmr_kcal":1.0,
            "netee_kcal":1.0,"days_remaining":1,"future_field":"ignore me"
        }"""
        val p = makotoJson.decodeFromString<ProfileResponse>(raw)
        assertEquals(1, p.age)
    }

    @Test
    fun `parse FoodResponse`() {
        val raw = """{
            "id":1,"name":"米饭","calories_per_100g":116.0,"protein_per_100g":2.6,
            "carbs_per_100g":25.9,"fat_per_100g":0.3,"search_keywords":["主食","碳水"],
            "note":"白米饭","created_at":"2026-01-01T12:00:00"
        }"""
        val f = makotoJson.decodeFromString<FoodResponse>(raw)
        assertEquals(1, f.id)
        assertEquals("米饭", f.name)
        assertEquals(116.0, f.caloriesPer100g, 0.01)
        assertEquals(2, f.searchKeywords.size)
    }

    @Test
    fun `parse FoodResponse empty keywords null note`() {
        val raw = """{
            "id":2,"name":"鸡蛋","calories_per_100g":155.0,"protein_per_100g":13.0,
            "carbs_per_100g":1.1,"fat_per_100g":10.6,"search_keywords":[],
            "note":null,"created_at":"2026-01-01T12:00:00"
        }"""
        val f = makotoJson.decodeFromString<FoodResponse>(raw)
        assertTrue(f.searchKeywords.isEmpty())
        assertNull(f.note)
    }

    @Test
    fun `parse FoodSearchResult`() {
        val r = makotoJson.decodeFromString<FoodSearchResult>(
            """{"id":5,"name":"鸡胸肉","distance":2}"""
        )
        assertEquals(5, r.id)
        assertEquals(2, r.distance)
    }

    @Test
    fun `parse BodyLogResponse`() {
        val raw = """{
            "id":10,"log_date":"2026-07-01","weight_kg":75.5,"body_fat_pct":20.0,
            "note":null,"created_at":"2026-07-01T08:00:00"
        }"""
        val b = makotoJson.decodeFromString<BodyLogResponse>(raw)
        assertEquals(10, b.id)
        assertEquals(75.5, b.weightKg, 0.01)
    }

    @Test
    fun `parse CircumferenceLogResponse partial`() {
        val raw = """{
            "id":3,"log_date":"2026-07-01","waist_cm":80.0,"arm_cm":null,
            "thigh_cm":55.0,"note":null,"created_at":"2026-07-01T08:00:00"
        }"""
        val c = makotoJson.decodeFromString<CircumferenceLogResponse>(raw)
        assertEquals(80.0, c.waistCm!!, 0.01)
        assertNull(c.armCm)
    }

    @Test
    fun `parse DietLogResponse`() {
        val raw = """{
            "id":20,"log_time":"2026-07-01T12:30:00","food_id":1,"grams":300.0,
            "note":"午餐","food_name":"米饭","calories_kcal":348.0,
            "protein_g":7.8,"carbs_g":77.7,"fat_g":0.9,
            "food_calories_per_100g":116.0,"food_protein_per_100g":2.6,
            "food_carbs_per_100g":25.9,"food_fat_per_100g":0.3,
            "created_at":"2026-07-01T12:30:00"
        }"""
        val d = makotoJson.decodeFromString<DietLogResponse>(raw)
        assertEquals(20, d.id)
        assertEquals("米饭", d.foodName)
        assertEquals(348.0, d.caloriesKcal, 0.01)
        assertEquals(116.0, d.foodCaloriesPer100g, 0.01)
    }

    @Test
    fun `parse ExerciseLogResponse`() {
        val raw = """{
            "id":5,"log_time":"2026-07-01T18:00:00","exercise_name":"跑步",
            "duration_desc":"5公里","calories_kcal":320.0,"note":null,
            "created_at":"2026-07-01T18:00:00"
        }"""
        val e = makotoJson.decodeFromString<ExerciseLogResponse>(raw)
        assertEquals("跑步", e.exerciseName)
        assertEquals(320.0, e.caloriesKcal, 0.01)
    }

    @Test
    fun `parse PaintingLogResponse`() {
        val raw = """{
            "id":1,"log_time":"2026-07-01T20:00:00","file_path":"/a/b.png",
            "file_id":"abc123","duration_seconds":3600.0,"note":"练习",
            "created_at":"2026-07-01T20:00:00"
        }"""
        val p = makotoJson.decodeFromString<PaintingLogResponse>(raw)
        assertEquals(3600.0, p.durationSeconds, 0.01)
    }

    @Test
    fun `parse TodayResponse fully populated`() {
        val raw = """{
            "date":"2026-07-09","total_intake_kcal":1200.0,"total_burned_kcal":350.0,
            "total_protein_g":85.0,"total_carbs_g":150.0,"total_fat_g":40.0,
            "netee_kcal":2040.0,"net_kcal":1190.0,
            "weight_delta_day":-0.3,"body_fat_delta_day":null,
            "weight_delta_week":-0.5,"body_fat_delta_week":-0.2,
            "deficit_week_kcal":3500.0,"deficit_month_kcal":14000.0,
            "atl":50,"ctl":45,"tsb":5,
            "body":{"weight_kg":75.5,"body_fat_pct":20.0,"ffm_kg":60.4,"fat_kg":15.1},
            "diets":[{
                "log_time":"2026-07-09T12:30:00","food_id":1,"food_name":"米饭",
                "grams":300.0,"calories_kcal":348.0,"protein_g":7.8,
                "carbs_g":77.7,"fat_g":0.9
            }],
            "exercises":[{
                "log_time":"2026-07-09T18:00:00","exercise_name":"跑步",
                "duration_desc":"5公里","calories_kcal":320.0
            }],
            "circumference":null,
            "painting":{
                "painted_today":false,"duration_seconds":0.0,"session_count":0,
                "sessions":[],"current_streak":0,"longest_streak":0,"total_days":0
            }
        }"""
        val t = makotoJson.decodeFromString<TodayResponse>(raw)
        assertEquals(1190.0, t.netKcal, 0.01)
        assertEquals(75.5, t.body!!.weightKg!!, 0.01)
        assertEquals(1, t.diets.size)
        assertEquals("米饭", t.diets[0].foodName)
        assertEquals(50, t.atl)
    }

    @Test
    fun `parse TodayResponse null body`() {
        val raw = """{
            "date":"2026-07-09","total_intake_kcal":0.0,"total_burned_kcal":0.0,
            "total_protein_g":0.0,"total_carbs_g":0.0,"total_fat_g":0.0,
            "netee_kcal":2000.0,"net_kcal":2000.0,
            "weight_delta_day":null,"body_fat_delta_day":null,
            "weight_delta_week":null,"body_fat_delta_week":null,
            "deficit_week_kcal":null,"deficit_month_kcal":null,
            "atl":null,"ctl":null,"tsb":null,
            "body":null,"diets":[],"exercises":[],"circumference":null,
            "painting":{"painted_today":false,"duration_seconds":0.0,"session_count":0,"sessions":[],"current_streak":0,"longest_streak":0,"total_days":0}
        }"""
        val t = makotoJson.decodeFromString<TodayResponse>(raw)
        assertNull(t.body)
        assertTrue(t.diets.isEmpty())
    }

    @Test
    fun `parse ReportResponse`() {
        val raw = """{
            "start_date":"2026-04-10","end_date":"2026-07-09","days":90,
            "target_weight_kg":72.0,"target_date":"2026-09-15",
            "rows":[{
                "date":"2026-07-01","weight_kg":75.5,"body_fat_pct":20.0,
                "ffm_kg":60.4,"fat_kg":15.1,"weight_7d_ma":75.3,"body_fat_7d_ma":20.1,
                "ffm_7d_ma":60.2,"fat_7d_ma":15.1,"deficit_kcal":500.0,
                "expected_deficit_kcal":400.0,"alpert_limit_kcal":800.0,
                "is_interpolated":false,"weekly_loss_kg":-0.3,
                "intake_kcal":1800.0,"tdee_kcal":2300.0,
                "atl":50,"ctl":45,"tsb":5
            }],
            "summary":{
                "weight_delta":-2.5,"body_fat_delta":-1.0,
                "ffm_delta":0.5,"fat_delta":-3.0,
                "weight_7d_ma_delta":-2.3,"body_fat_7d_ma_delta":-0.8,
                "ffm_7d_ma_delta":0.3,"total_deficit_kcal":35000.0,
                "total_expected_kcal":30000.0,"met_target":true
            }
        }"""
        val r = makotoJson.decodeFromString<ReportResponse>(raw)
        assertEquals(90, r.days)
        assertEquals(75.5, r.rows[0].weightKg!!, 0.01)
        assertTrue(r.summary.metTarget)
    }

    @Test
    fun `parse ReportRow interpolated`() {
        val raw = """{
            "date":"2026-06-15","weight_kg":75.0,"body_fat_pct":null,
            "ffm_kg":null,"fat_kg":null,"weight_7d_ma":74.8,"body_fat_7d_ma":20.0,
            "ffm_7d_ma":null,"fat_7d_ma":null,"deficit_kcal":null,
            "expected_deficit_kcal":null,"alpert_limit_kcal":null,
            "is_interpolated":true,"weekly_loss_kg":null,
            "intake_kcal":null,"tdee_kcal":null,
            "atl":null,"ctl":null,"tsb":null
        }"""
        val r = makotoJson.decodeFromString<ReportRow>(raw)
        assertEquals(75.0, r.weightKg!!, 0.01)
        assertTrue(r.isInterpolated)
    }

    @Test
    fun `parse FitnessResponse and WeeklyLoadResponse`() {
        val f = makotoJson.decodeFromString<FitnessResponse>(
            """{"date":"2026-07-01","atl":50,"ctl":45,"tsb":5}"""
        )
        assertEquals(50, f.atl)

        val w = makotoJson.decodeFromString<WeeklyLoadResponse>(
            """{"week_start":"2026-06-29","load":1200}"""
        )
        assertEquals(1200, w.load)
    }

    @Test
    fun `parse list of FoodResponse`() {
        val raw = """[
            {"id":1,"name":"米饭","calories_per_100g":116.0,"protein_per_100g":2.6,
             "carbs_per_100g":25.9,"fat_per_100g":0.3,"search_keywords":[],"note":null,
             "created_at":"2026-01-01T12:00:00"},
            {"id":2,"name":"鸡蛋","calories_per_100g":155.0,"protein_per_100g":13.0,
             "carbs_per_100g":1.1,"fat_per_100g":10.6,"search_keywords":[],"note":null,
             "created_at":"2026-01-01T12:00:00"}
        ]"""
        val foods = makotoJson.decodeFromString<List<FoodResponse>>(raw)
        assertEquals(2, foods.size)
        assertEquals("米饭", foods[0].name)
        assertEquals("鸡蛋", foods[1].name)
    }

    @Test
    fun `parse empty list`() {
        assertTrue(makotoJson.decodeFromString<List<DietLogResponse>>("[]").isEmpty())
    }

    @Test
    fun `parse list of BodyLogResponse`() {
        val raw = """[{
            "id":1,"log_date":"2026-07-01","weight_kg":75.5,"body_fat_pct":20.0,
            "note":null,"created_at":"2026-07-01T08:00:00"
        }]"""
        val logs = makotoJson.decodeFromString<List<BodyLogResponse>>(raw)
        assertEquals(1, logs.size)
        assertEquals(75.5, logs[0].weightKg, 0.01)
    }

    @Test
    fun `parse ReportSummary`() {
        val raw = """{
            "weight_delta":-2.5,"body_fat_delta":null,
            "ffm_delta":null,"fat_delta":null,
            "weight_7d_ma_delta":null,"body_fat_7d_ma_delta":null,
            "ffm_7d_ma_delta":null,"total_deficit_kcal":null,
            "total_expected_kcal":null,"met_target":false
        }"""
        val s = makotoJson.decodeFromString<ReportSummary>(raw)
        assertEquals(-2.5, s.weightDelta!!, 0.01)
        assertNull(s.bodyFatDelta)
        assertFalse(s.metTarget)
    }
}
