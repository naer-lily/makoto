package com.makoto.android.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = Green700,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    primaryContainer = Green100,
    onPrimaryContainer = Green900,
    secondary = Orange500,
    onSecondary = androidx.compose.ui.graphics.Color.White,
    secondaryContainer = androidx.compose.ui.graphics.Color(0xFFFFE0B2),
    tertiary = Blue500,
    background = SurfaceLight,
    surface = androidx.compose.ui.graphics.Color.White,
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFFE8E8E8),
    onBackground = OnSurfaceLight,
    onSurface = OnSurfaceLight,
    error = Red500,
)

private val DarkColorScheme = darkColorScheme(
    primary = Green200,
    onPrimary = Green900,
    primaryContainer = Green700,
    onPrimaryContainer = Green50,
    secondary = Orange500,
    tertiary = Blue500,
    background = SurfaceDark,
    surface = SurfaceDark,
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFF2D2D2D),
    onBackground = OnSurfaceDark,
    onSurface = OnSurfaceDark,
    error = Red500,
)

@Composable
fun MakotoTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content,
    )
}
