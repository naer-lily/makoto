package com.makoto.android.data.local

import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SettingsStoreTest {

    private val context = ApplicationProvider.getApplicationContext<android.content.Context>()
    private val store = SettingsStore(context)

    @Test
    fun `default server URL is makoto-naer-ink`() = runTest {
        store.clear()
        assertEquals(SettingsStore.DEFAULT_SERVER_URL, store.serverUrl.first())
    }

    @Test
    fun `default token is blank`() = runTest {
        store.clear()
        assertTrue(store.token.first().isBlank())
    }

    @Test
    fun `set and read server URL`() = runTest {
        store.clear()
        store.setServerUrl("https://custom.example.com")
        assertEquals("https://custom.example.com", store.serverUrl.first())
    }

    @Test
    fun `set and read token`() = runTest {
        store.clear()
        store.setToken("secret-abc-123")
        assertEquals("secret-abc-123", store.token.first())
    }

    @Test
    fun `clear resets both values`() = runTest {
        store.setServerUrl("https://x.com")
        store.setToken("abc")
        store.clear()
        assertEquals(SettingsStore.DEFAULT_SERVER_URL, store.serverUrl.first())
        assertTrue(store.token.first().isBlank())
    }

    @Test
    fun `update token multiple times`() = runTest {
        store.clear()
        store.setToken("first")
        assertEquals("first", store.token.first())
        store.setToken("second")
        assertEquals("second", store.token.first())
    }
}
