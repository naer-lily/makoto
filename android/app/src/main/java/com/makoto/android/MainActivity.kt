package com.makoto.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.makoto.android.data.local.SettingsStore
import com.makoto.android.data.remote.ApiProvider
import com.makoto.android.ui.navigation.MakotoNavGraph
import com.makoto.android.ui.navigation.Screen
import com.makoto.android.ui.theme.MakotoTheme
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking

class MainActivity : ComponentActivity() {

    private val settingsStore: SettingsStore by lazy {
        SettingsStore(applicationContext)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val savedUrl = runBlocking { settingsStore.serverUrl.first() }
        val savedToken = runBlocking { settingsStore.token.first() }
        val hasCredentials = savedToken.isNotBlank()

        setContent {
            MakotoTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MakotoAppContent(
                        savedUrl = savedUrl,
                        savedToken = savedToken,
                        hasCredentials = hasCredentials,
                    )
                }
            }
        }
    }

    @Composable
    private fun MakotoAppContent(
        savedUrl: String,
        savedToken: String,
        hasCredentials: Boolean,
    ) {
        val navController = rememberNavController()
        val startDestination = if (hasCredentials) Screen.Dashboard.route else Screen.Login.route

        val api = remember {
            ApiProvider.get(savedUrl, savedToken)
        }

        var currentStartDest by remember { mutableStateOf(startDestination) }

        MakotoNavGraph(
            navController = navController,
            api = api,
            startDestination = currentStartDest,
            onLogout = {
                runBlocking { settingsStore.clear() }
                currentStartDest = Screen.Login.route
                navController.navigate(Screen.Login.route) {
                    popUpTo(0) { inclusive = true }
                }
            },
        )
    }
}
