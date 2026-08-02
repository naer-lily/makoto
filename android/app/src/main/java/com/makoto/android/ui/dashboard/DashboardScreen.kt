package com.makoto.android.ui.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import kotlinx.coroutines.launch
import com.makoto.android.data.remote.dto.TodayDietItem
import com.makoto.android.data.remote.dto.TodayExerciseItem
import com.makoto.android.data.remote.dto.TodayResponse
import com.makoto.android.data.repository.DashboardRepository
import com.makoto.android.ui.components.StatCard
import com.makoto.android.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    dashboardRepo: DashboardRepository,
    navController: NavController,
    viewModel: DashboardViewModel = viewModel(
        factory = DashboardViewModelFactory(dashboardRepo),
    ),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            DrawerContent(navController, drawerState)
        },
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("makoto") },
                    navigationIcon = {
                        val scope = rememberCoroutineScope()
                        IconButton(onClick = {
                            scope.launch { drawerState.open() }
                        }) {
                            Icon(Icons.Default.Menu, contentDescription = "菜单")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        titleContentColor = MaterialTheme.colorScheme.onPrimary,
                        navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                    ),
                )
            },
        ) { padding ->
            if (state.isLoading && state.today == null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = androidx.compose.ui.Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }
            } else if (state.error != null && state.today == null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = androidx.compose.ui.Alignment.Center,
                ) {
                    Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                        Text(state.error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(8.dp))
                        Button(onClick = viewModel::loadToday) { Text("重试") }
                    }
                }
            } else {
                state.today?.let { today ->
                    DashboardContent(
                        today = today,
                        modifier = Modifier.padding(padding),
                        onRefresh = viewModel::loadToday,
                    )
                }
            }
        }
    }
}

@Composable
private fun DashboardContent(
    today: TodayResponse,
    modifier: Modifier = Modifier,
    onRefresh: () -> Unit,
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        // Date header
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = today.date,
                    style = MaterialTheme.typography.titleLarge,
                )
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, contentDescription = "刷新")
                }
            }
        }

        // Calorie stats row
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                StatCard(
                    label = "摄入",
                    value = "${today.totalIntakeKcal.toInt()}",
                    subtitle = "kcal",
                    accentColor = Orange500,
                    modifier = Modifier.weight(1f),
                )
                StatCard(
                    label = "消耗",
                    value = "${today.totalBurnedKcal.toInt()}",
                    subtitle = "kcal",
                    accentColor = Red500,
                    modifier = Modifier.weight(1f),
                )
            }
        }

        // Net and protein row
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                StatCard(
                    label = "净热量",
                    value = "${today.netKcal.toInt()}",
                    subtitle = "NETEE ${today.neteeKcal.toInt()} kcal",
                    accentColor = if (today.netKcal >= 0) Green500 else Red500,
                    modifier = Modifier.weight(1f),
                )
                StatCard(
                    label = "蛋白质",
                    value = String.format("%.1f", today.totalProteinG),
                    subtitle = "g",
                    accentColor = Blue500,
                    modifier = Modifier.weight(1f),
                )
            }
        }

        // Weight and body fat row
        today.body?.let { body ->
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    StatCard(
                        label = "体重",
                        value = if (body.weightKg != null) String.format("%.1f", body.weightKg) else "-",
                        subtitle = buildDeltaString(today.weightDeltaDay, "kg"),
                        accentColor = Green700,
                        modifier = Modifier.weight(1f),
                    )
                    StatCard(
                        label = "体脂率",
                        value = if (body.bodyFatPct != null) String.format("%.1f%%", body.bodyFatPct) else "-",
                        subtitle = buildDeltaString(today.bodyFatDeltaDay, "%"),
                        accentColor = Purple500,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }

        // Macro row
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                ) {
                    MacroItem("碳水", String.format("%.0fg", today.totalCarbsG))
                    MacroItem("脂肪", String.format("%.0fg", today.totalFatG))
                    MacroItem("蛋白质", String.format("%.0fg", today.totalProteinG))
                    MacroItem("膳食纤维", String.format("%.0fg", today.totalFiberG))
                }
            }
        }

        // Diet log section
        if (today.diets.isNotEmpty()) {
            item {
                Text(
                    "今日饮食",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            items(today.diets) { diet ->
                DietItemCard(diet)
            }
        }

        // Exercise log section
        if (today.exercises.isNotEmpty()) {
            item {
                Text(
                    "今日运动",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            items(today.exercises) { exercise ->
                ExerciseItemCard(exercise)
            }
        }

        // Bottom spacing
        item { Spacer(modifier = Modifier.height(16.dp)) }
    }
}

@Composable
private fun MacroItem(label: String, value: String) {
    Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun DietItemCard(diet: TodayDietItem) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(diet.foodName, style = MaterialTheme.typography.bodyLarge)
                Text(
                    "${diet.grams.toInt()}g  ·  ${diet.caloriesKcal.toInt()} kcal",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Column(horizontalAlignment = androidx.compose.ui.Alignment.End) {
                Text("P ${String.format("%.1f", diet.proteinG)}g", style = MaterialTheme.typography.labelSmall)
                Text("C ${String.format("%.1f", diet.carbsG)}g", style = MaterialTheme.typography.labelSmall)
                Text("F ${String.format("%.1f", diet.fatG)}g", style = MaterialTheme.typography.labelSmall)
                Text("Fib ${String.format("%.1f", diet.fiberG)}g", style = MaterialTheme.typography.labelSmall)
            }
        }
    }
}

@Composable
private fun ExerciseItemCard(exercise: TodayExerciseItem) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(exercise.exerciseName, style = MaterialTheme.typography.bodyLarge)
                Text(
                    exercise.durationDesc,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                "${exercise.caloriesKcal.toInt()} kcal",
                style = MaterialTheme.typography.bodyMedium,
                color = Red500,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

@Composable
fun DrawerContent(navController: NavController, drawerState: DrawerState) {
    val scope = rememberCoroutineScope()
    ModalDrawerSheet {
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            "makoto",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(horizontal = 28.dp, vertical = 8.dp),
        )
        HorizontalDivider(modifier = Modifier.padding(horizontal = 28.dp))
        Spacer(modifier = Modifier.height(8.dp))

        DrawerItem(Icons.Default.Dashboard, "仪表盘") {
            scope.launch { drawerState.close() }
            navController.navigate("dashboard") { launchSingleTop = true }
        }
        DrawerItem(Icons.Default.RestaurantMenu, "食物库") {
            scope.launch { drawerState.close() }
            navController.navigate("foods") { launchSingleTop = true }
        }
        DrawerItem(Icons.Default.Fastfood, "饮食记录") {
            scope.launch { drawerState.close() }
            navController.navigate("diet") { launchSingleTop = true }
        }
        DrawerItem(Icons.Default.MonitorWeight, "身体测量") {
            scope.launch { drawerState.close() }
            navController.navigate("body") { launchSingleTop = true }
        }
        DrawerItem(Icons.Default.FitnessCenter, "运动记录") {
            scope.launch { drawerState.close() }
            navController.navigate("exercise") { launchSingleTop = true }
        }
        DrawerItem(Icons.Default.Person, "个人画像") {
            scope.launch { drawerState.close() }
            navController.navigate("profile") { launchSingleTop = true }
        }
        HorizontalDivider(modifier = Modifier.padding(horizontal = 28.dp, vertical = 8.dp))
        DrawerItem(Icons.Default.Settings, "设置") {
            scope.launch { drawerState.close() }
            navController.navigate("settings") { launchSingleTop = true }
        }
    }
}

@Composable
private fun DrawerItem(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, onClick: () -> Unit) {
    NavigationDrawerItem(
        icon = { Icon(icon, contentDescription = label) },
        label = { Text(label) },
        selected = false,
        onClick = onClick,
        modifier = Modifier.padding(horizontal = 12.dp),
    )
}

private fun buildDeltaString(delta: Double?, unit: String): String {
    if (delta == null) return "-"
    val sign = if (delta > 0) "+" else ""
    return "$sign${String.format("%.1f", delta)} $unit"
}

internal class DashboardViewModelFactory(
    private val dashboardRepo: DashboardRepository,
) : androidx.lifecycle.ViewModelProvider.Factory {
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return DashboardViewModel(dashboardRepo) as T
    }
}
