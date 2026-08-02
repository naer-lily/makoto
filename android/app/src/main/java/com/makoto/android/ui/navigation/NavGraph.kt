package com.makoto.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.repository.*
import com.makoto.android.ui.body.BodyScreen
import com.makoto.android.ui.dashboard.DashboardScreen
import com.makoto.android.ui.diet.DietScreen
import com.makoto.android.ui.exercise.ExerciseScreen
import com.makoto.android.ui.foods.FoodsScreen
import com.makoto.android.ui.login.LoginScreen
import com.makoto.android.ui.profile.ProfileScreen
import com.makoto.android.ui.settings.SettingsScreen
import com.makoto.android.ui.weather.WeatherScreen

@Composable
fun MakotoNavGraph(
    navController: NavHostController,
    api: MakotoApi,
    startDestination: String,
    onLogout: () -> Unit,
) {
    val dashboardRepo = DashboardRepository(api)
    val foodRepo = FoodRepository(api)
    val bodyRepo = BodyRepository(api)
    val dietRepo = DietRepository(api)
    val exerciseRepo = ExerciseRepository(api)
    val profileRepo = ProfileRepository(api)
    val weatherRepo = WeatherRepository(api)

    NavHost(
        navController = navController,
        startDestination = startDestination,
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onConnected = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
            )
        }

        composable(Screen.Dashboard.route) {
            DashboardScreen(
                dashboardRepo = dashboardRepo,
                navController = navController,
            )
        }

        composable(Screen.Foods.route) {
            FoodsScreen(
                foodRepo = foodRepo,
                navController = navController,
            )
        }

        composable(Screen.Diet.route) {
            DietScreen(
                dietRepo = dietRepo,
                navController = navController,
            )
        }

        composable(Screen.Body.route) {
            BodyScreen(
                bodyRepo = bodyRepo,
                navController = navController,
            )
        }

        composable(Screen.Exercise.route) {
            ExerciseScreen(
                exerciseRepo = exerciseRepo,
                navController = navController,
            )
        }

        composable(Screen.Profile.route) {
            ProfileScreen(
                profileRepo = profileRepo,
                navController = navController,
            )
        }

        composable(Screen.Weather.route) {
            WeatherScreen(
                weatherRepo = weatherRepo,
                navController = navController,
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                navController = navController,
                onLogout = onLogout,
            )
        }
    }
}
