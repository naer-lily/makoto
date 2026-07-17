package com.makoto.android.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MakotoScaffold(
    title: String,
    navController: NavController,
    content: @Composable (PaddingValues) -> Unit,
) {
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
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

                DrawerNavItem(Icons.Default.Dashboard, "仪表盘", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("dashboard") { launchSingleTop = true }
                })
                DrawerNavItem(Icons.Default.RestaurantMenu, "食物库", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("foods") { launchSingleTop = true }
                })
                DrawerNavItem(Icons.Default.Fastfood, "饮食记录", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("diet") { launchSingleTop = true }
                })
                DrawerNavItem(Icons.Default.MonitorWeight, "身体测量", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("body") { launchSingleTop = true }
                })
                DrawerNavItem(Icons.Default.FitnessCenter, "运动记录", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("exercise") { launchSingleTop = true }
                })
                DrawerNavItem(Icons.Default.Person, "个人画像", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("profile") { launchSingleTop = true }
                })
                HorizontalDivider(modifier = Modifier.padding(horizontal = 28.dp, vertical = 8.dp))
                DrawerNavItem(Icons.Default.Settings, "设置", onClick = {
                    scope.launch { drawerState.close() }
                    navController.navigate("settings") { launchSingleTop = true }
                })
            }
        },
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(title) },
                    navigationIcon = {
                        IconButton(onClick = { scope.launch { drawerState.open() } }) {
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
            content(padding)
        }
    }
}

@Composable
private fun DrawerNavItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit,
) {
    NavigationDrawerItem(
        icon = { Icon(icon, contentDescription = label) },
        label = { Text(label) },
        selected = false,
        onClick = onClick,
        modifier = Modifier.padding(horizontal = 12.dp),
    )
}
