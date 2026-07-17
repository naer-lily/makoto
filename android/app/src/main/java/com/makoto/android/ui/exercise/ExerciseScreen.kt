package com.makoto.android.ui.exercise

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.makoto.android.data.remote.dto.ExerciseLogResponse
import com.makoto.android.data.repository.ExerciseRepository
import com.makoto.android.ui.components.DateRangeBar
import com.makoto.android.ui.components.MakotoScaffold
import com.makoto.android.ui.theme.Red500
import java.time.format.DateTimeFormatter

@Composable
fun ExerciseScreen(
    exerciseRepo: ExerciseRepository,
    navController: NavController,
    viewModel: ExerciseViewModel = viewModel(
        factory = ExerciseViewModelFactory(exerciseRepo),
    ),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val dateLabel = state.currentDate.format(DateTimeFormatter.ofPattern("yyyy-MM-dd EEEE"))

    MakotoScaffold(title = "运动记录", navController = navController) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            DateRangeBar(
                dateLabel = dateLabel,
                onPrev = viewModel::goToPrevDay,
                onNext = viewModel::goToNextDay,
            )

            Card(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${state.totalBurned.toInt()}",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = Red500,
                        )
                        Text("消耗 kcal", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${state.exercises.size}",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text("项运动", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }

            if (state.isLoading) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (state.error != null) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(state.error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(8.dp))
                        Button(onClick = viewModel::loadLogs) { Text("重试") }
                    }
                }
            } else if (state.exercises.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("暂无运动记录", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    items(state.exercises) { exercise ->
                        ExerciseLogCard(exercise)
                    }
                    item { Spacer(modifier = Modifier.height(8.dp)) }
                }
            }
        }
    }
}

@Composable
private fun ExerciseLogCard(exercise: ExerciseLogResponse) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(exercise.exerciseName, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                Text(exercise.durationDesc, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                exercise.note?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
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

internal class ExerciseViewModelFactory(
    private val exerciseRepo: ExerciseRepository,
) : androidx.lifecycle.ViewModelProvider.Factory {
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return ExerciseViewModel(exerciseRepo) as T
    }
}
