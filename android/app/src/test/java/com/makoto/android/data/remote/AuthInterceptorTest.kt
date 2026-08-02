package com.makoto.android.data.remote

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class AuthInterceptorTest {

    private lateinit var server: MockWebServer

    @Before
    fun setUp() {
        server = MockWebServer()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `adds Authorization header with Bearer token`() {
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor { "my-token" })
            .build()

        server.enqueue(MockResponse().setBody("ok"))
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().use { response ->
            assertEquals(200, response.code)
        }

        val recorded = server.takeRequest()
        assertEquals("Bearer my-token", recorded.getHeader("Authorization"))
    }

    @Test
    fun `skips Authorization header when token is blank`() {
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor { "" })
            .build()

        server.enqueue(MockResponse().setBody("ok"))
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().close()

        val recorded = server.takeRequest()
        assertNull(recorded.getHeader("Authorization"))
    }

    @Test
    fun `skips Authorization header when token is whitespace`() {
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor { "   " })
            .build()

        server.enqueue(MockResponse().setBody("ok"))
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().close()

        val recorded = server.takeRequest()
        assertNull(recorded.getHeader("Authorization"))
    }
}
