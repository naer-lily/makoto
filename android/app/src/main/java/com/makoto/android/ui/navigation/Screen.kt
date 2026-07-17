package com.makoto.android.ui.navigation

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object Foods : Screen("foods")
    data object Diet : Screen("diet")
    data object Body : Screen("body")
    data object Exercise : Screen("exercise")
    data object Profile : Screen("profile")
    data object Settings : Screen("settings")
}
