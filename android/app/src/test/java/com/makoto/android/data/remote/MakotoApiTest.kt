package com.makoto.android.data.remote

import com.makoto.android.data.remote.dto.*
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class MakotoApiTest {

    private lateinit var server: MockWebServer
    private lateinit var api: MakotoApi
    private val testToken = "test-token-123"

    @Before
    fun setUp() {
        server = MockWebServer()
        val baseUrl = server.url("/").toString()
        api = ApiProvider.get(baseUrl, testToken)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    // ── Auth header ──

    @Test
    fun `adds Bearer token header`() = runTest {
        server.enqueue(MockResponse().setBody("""{"name":"x","gender":"male","age":1,"height_cm":1.0,"weight_kg":1.0,"body_fat_pct":1.0,"target_weight_kg":1.0,"target_date":"2026-01-01","activity_level":"sedentary","ffm_kg":1.0,"bmr_kcal":1.0,"netee_kcal":1.0,"days_remaining":1}"""))
        api.getProfile()
        val request: RecordedRequest = server.takeRequest()
        assertEquals("Bearer $testToken", request.getHeader("Authorization"))
    }

    // ── URL construction ──

    @Test
    fun `profile endpoint uses correct path`() = runTest {
        server.enqueue(MockResponse().setBody("""{"name":"x","gender":"male","age":1,"height_cm":1.0,"weight_kg":1.0,"body_fat_pct":1.0,"target_weight_kg":1.0,"target_date":"2026-01-01","activity_level":"sedentary","ffm_kg":1.0,"bmr_kcal":1.0,"netee_kcal":1.0,"days_remaining":1}"""))
        api.getProfile()
        assertEquals("/api/v1/profile", server.takeRequest().requestUrl!!.encodedPath)
    }

    @Test
    fun `foods endpoint uses correct path`() = runTest {
        server.enqueue(MockResponse().setBody("[]"))
        api.getFoods()
        assertEquals("/api/v1/foods", server.takeRequest().requestUrl!!.encodedPath)
    }

    @Test
    fun `search foods adds query params`() = runTest {
        server.enqueue(MockResponse().setBody("[]"))
        api.searchFoods("米饭", 10)
        val request = server.takeRequest()
        assertEquals("/api/v1/foods/search", request.requestUrl!!.encodedPath)
        assertEquals("米饭", request.requestUrl!!.queryParameter("q"))
        assertEquals("10", request.requestUrl!!.queryParameter("limit"))
    }

    @Test
    fun `food detail uses id in path`() = runTest {
        server.enqueue(MockResponse().setBody("""{"id":5,"name":"x","calories_per_100g":1.0,"protein_per_100g":1.0,"carbs_per_100g":1.0,"fat_per_100g":1.0,"search_keywords":[],"note":null,"created_at":"2026-01-01T12:00:00"}"""))
        api.getFood(5)
        assertEquals("/api/v1/foods/5", server.takeRequest().requestUrl!!.encodedPath)
    }

    @Test
    fun `diet logs with date filters`() = runTest {
        server.enqueue(MockResponse().setBody("[]"))
        api.getDietLogs("2026-07-01", "2026-07-09", 100)
        val request = server.takeRequest()
        assertEquals("2026-07-01", request.requestUrl!!.queryParameter("start"))
        assertEquals("2026-07-09", request.requestUrl!!.queryParameter("end"))
        assertEquals("100", request.requestUrl!!.queryParameter("limit"))
    }

    @Test
    fun `diet logs without optional params`() = runTest {
        server.enqueue(MockResponse().setBody("[]"))
        api.getDietLogs()
        val request = server.takeRequest()
        assertNull(request.requestUrl!!.queryParameter("start"))
        assertNull(request.requestUrl!!.queryParameter("end"))
        assertNull(request.requestUrl!!.queryParameter("limit"))
    }

    @Test
    fun `dashboard report adds date params`() = runTest {
        server.enqueue(MockResponse().setBody("""{"start_date":"2026-01-01","end_date":"2026-07-09","days":1,"rows":[],"summary":{"met_target":false}}"""))
        api.getReport("2026-01-01", "2026-07-09")
        val request = server.takeRequest()
        assertEquals("2026-01-01", request.requestUrl!!.queryParameter("start_date"))
        assertEquals("2026-07-09", request.requestUrl!!.queryParameter("end_date"))
    }

    // ── Response parsing ──

    @Test
    fun `deserializes TodayResponse from mock`() = runTest {
        server.enqueue(MockResponse().setBody("""{
            "date":"2026-07-09","total_intake_kcal":1200.0,"total_burned_kcal":350.0,
            "total_protein_g":85.0,"total_carbs_g":150.0,"total_fat_g":40.0,
            "netee_kcal":2040.0,"net_kcal":1190.0,
            "body":{"weight_kg":75.5,"body_fat_pct":20.0,"ffm_kg":60.4,"fat_kg":15.1},
            "diets":[],"exercises":[],"circumference":null,"atl":null,"ctl":null,"tsb":null,
            "painting":{"painted_today":false,"duration_seconds":0.0,"session_count":0,"sessions":[],"current_streak":0,"longest_streak":0,"total_days":0},
            "weight_delta_day":null,"body_fat_delta_day":null,
            "weight_delta_week":null,"body_fat_delta_week":null,
            "deficit_week_kcal":null,"deficit_month_kcal":null
        }"""))
        val today = api.getToday()
        assertEquals(75.5, today.body!!.weightKg!!, 0.01)
        assertEquals(1190.0, today.netKcal, 0.01)
    }

    @Test
    fun `handles HTTP 401 error`() = runTest {
        server.enqueue(MockResponse().setResponseCode(401).setBody("""{"detail":"Unauthorized"}"""))
        try {
            api.getProfile()
            fail("Expected exception")
        } catch (e: Exception) {
            assertTrue(e is retrofit2.HttpException)
        }
    }

    // ── ApiProvider normalization ──

    @Test
    fun `ApiProvider normalizes URL and makes requests`() = runTest {
        val api = ApiProvider.get(server.url("/").toString().removeSuffix("/"), testToken)
        server.enqueue(MockResponse().setBody("""{"name":"x","gender":"male","age":1,"height_cm":1.0,"weight_kg":1.0,"body_fat_pct":1.0,"target_weight_kg":1.0,"target_date":"2026-01-01","activity_level":"sedentary","ffm_kg":1.0,"bmr_kcal":1.0,"netee_kcal":1.0,"days_remaining":1}"""))
        val profile = api.getProfile()
        assertEquals(1, profile.age)
    }
}
