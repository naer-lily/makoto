package com.makoto.android.data.remote

import com.makoto.android.data.remote.dto.*
import com.makoto.android.data.repository.*
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test

/**
 * 真实服务器集成测试 — 需要有效的 MAKOTO_TOKEN 环境变量或系统属性。
 * 运行方式: ./gradlew test -Dmakoto.token=your-token
 * 不带 token 时自动跳过。
 */
class MakotoApiIntegrationTest {

    private val serverUrl = System.getProperty("makoto.server") ?: "https://makoto.naer.ink"
    private val token: String = System.getProperty("makoto.token") ?: System.getenv("MAKOTO_TOKEN") ?: ""

    private lateinit var api: MakotoApi

    @Before
    fun setUp() {
        api = ApiProvider.get(serverUrl, token)
    }

    private fun requireToken() {
        assumeTrue("Set -Dmakoto.token=xxx to run integration tests", token.isNotBlank())
    }

    // ── Connectivity ──

    @Test
    fun `profile endpoint returns valid data`() = runTest {
        requireToken()
        val profile = api.getProfile()
        assertTrue(profile.name.isNotBlank())
        assertTrue(profile.age > 0)
        assertTrue(profile.neteeKcal > 0)
    }

    @Test
    fun `unauthorized request with bad token throws 401`() = runTest {
        val badApi = ApiProvider.get(serverUrl, "bad-token-12345")
        try {
            badApi.getProfile()
            fail("Expected 401")
        } catch (e: Exception) {
            assertTrue(e is retrofit2.HttpException)
        }
    }

    // ── Foods ──

    @Test
    fun `getFoods returns non-empty list`() = runTest {
        requireToken()
        val foods = api.getFoods()
        assertTrue(foods.isNotEmpty())
        val first = foods.first()
        assertTrue(first.name.isNotBlank())
        assertTrue(first.caloriesPer100g > 0)
    }

    @Test
    fun `searchFoods finds results`() = runTest {
        requireToken()
        val foods = api.getFoods()
        if (foods.isNotEmpty()) {
            val keyword = foods.first().name.take(1)
            val results = api.searchFoods(keyword)
            assertTrue(results.isNotEmpty())
            assertTrue(results.first().distance >= 0)
        }
    }

    @Test
    fun `getFood returns specific food`() = runTest {
        requireToken()
        val foods = api.getFoods()
        if (foods.isNotEmpty()) {
            val food = api.getFood(foods.first().id)
            assertEquals(foods.first().name, food.name)
        }
    }

    // ── Body Logs ──

    @Test
    fun `getBodyLogs returns data`() = runTest {
        requireToken()
        val logs = api.getBodyLogs()
        if (logs.isNotEmpty()) {
            assertTrue(logs.first().weightKg > 0)
        }
    }

    // ── Diet Logs ──

    @Test
    fun `getDietLogs with date filter`() = runTest {
        requireToken()
        val logs = api.getDietLogs(limit = 5)
        // May be empty if no data today
        if (logs.isNotEmpty()) {
            assertTrue(logs.first().foodName.isNotBlank())
            assertTrue(logs.first().caloriesKcal >= 0)
        }
    }

    // ── Exercise Logs ──

    @Test
    fun `getExerciseLogs with date filter`() = runTest {
        requireToken()
        val logs = api.getExerciseLogs(limit = 5)
        if (logs.isNotEmpty()) {
            assertTrue(logs.first().exerciseName.isNotBlank())
        }
    }

    // ── Dashboard ──

    @Test
    fun `dashboard today returns valid summary`() = runTest {
        requireToken()
        val today = api.getToday()
        assertTrue(today.date.isNotBlank())
        assertTrue(today.neteeKcal > 0)
    }

    @Test
    fun `dashboard report returns rows for 30 days`() = runTest {
        requireToken()
        val today = api.getToday()
        // Report for last 30 days
        val report = api.getReport("2026-06-01", today.date)
        assertTrue(report.days > 0)
    }

    // ── Repository integration ──

    @Test
    fun `DashboardRepository returns success from real server`() = runTest {
        requireToken()
        val repo = DashboardRepository(api)
        val result = repo.getToday()
        assertTrue(result.isSuccess)
        assertTrue(result.getOrNull()!!.neteeKcal > 0)
    }

    @Test
    fun `ProfileRepository returns success from real server`() = runTest {
        requireToken()
        val repo = ProfileRepository(api)
        val result = repo.getProfile()
        assertTrue(result.isSuccess)
        assertTrue(result.getOrNull()!!.name.isNotBlank())
    }
}
