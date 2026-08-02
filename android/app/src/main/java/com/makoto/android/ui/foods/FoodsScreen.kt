package com.makoto.android.ui.foods

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.makoto.android.data.remote.dto.FoodResponse
import com.makoto.android.data.repository.FoodRepository
import com.makoto.android.ui.components.MakotoScaffold

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FoodsScreen(
    foodRepo: FoodRepository,
    navController: NavController,
    viewModel: FoodsViewModel = viewModel(
        factory = FoodsViewModelFactory(foodRepo),
    ),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var detailFood by remember { mutableStateOf<FoodResponse?>(null) }

    MakotoScaffold(title = "食物库", navController = navController) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            OutlinedTextField(
                value = state.searchQuery,
                onValueChange = viewModel::onSearchQueryChanged,
                modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                placeholder = { Text("搜索食物...") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                trailingIcon = {
                    IconButton(onClick = viewModel::loadFoods) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新")
                    }
                },
                singleLine = true,
            )

            if (state.isLoading && state.foods.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (state.error != null && state.foods.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(state.error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(8.dp))
                        Button(onClick = viewModel::loadFoods) { Text("重试") }
                    }
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    items(state.foods) { food ->
                        FoodRow(food, onClick = { detailFood = food })
                    }
                    item { Spacer(modifier = Modifier.height(8.dp)) }
                }
            }
        }
    }

    // Detail dialog
    detailFood?.let { food ->
        AlertDialog(
            onDismissRequest = { detailFood = null },
            title = { Text(food.name) },
            text = {
                Column {
                    NutritionRow("热量", "${food.caloriesPer100g} kcal/100g")
                    NutritionRow("蛋白质", "${food.proteinPer100g} g/100g")
                    NutritionRow("碳水", "${food.carbsPer100g} g/100g")
                    NutritionRow("脂肪", "${food.fatPer100g} g/100g")
                    NutritionRow("膳食纤维", "${food.fiberPer100g} g/100g")
                    if (food.note != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("备注: ${food.note}", style = MaterialTheme.typography.bodySmall)
                    }
                    if (food.searchKeywords.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "关键词: ${food.searchKeywords.joinToString(", ")}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { detailFood = null }) { Text("关闭") }
            },
        )
    }
}

@Composable
private fun FoodRow(food: FoodResponse, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(food.name, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                Text(
                    "${food.caloriesPer100g.toInt()} kcal / 100g",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                "P${String.format("%.1f", food.proteinPer100g)}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}

@Composable
private fun NutritionRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
    }
}

internal class FoodsViewModelFactory(
    private val foodRepo: FoodRepository,
) : androidx.lifecycle.ViewModelProvider.Factory {
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return FoodsViewModel(foodRepo) as T
    }
}
