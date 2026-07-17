package com.makoto.android.ui.exercise

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.ExerciseLogResponse
import com.makoto.android.data.repository.ExerciseRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

data class ExerciseUiState(
    val exercises: List<ExerciseLogResponse> = emptyList(),
    val currentDate: LocalDate = LocalDate.now(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val totalBurned: Double = 0.0,
)

class ExerciseViewModel(
    private val exerciseRepo: ExerciseRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ExerciseUiState())
    val uiState: StateFlow<ExerciseUiState> = _uiState.asStateFlow()

    init {
        loadLogs()
    }

    fun loadLogs() {
        val date = _uiState.value.currentDate
        val dateStr = date.format(DateTimeFormatter.ISO_LOCAL_DATE)
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            exerciseRepo.getExerciseLogs(start = dateStr, end = dateStr)
                .onSuccess { exercises ->
                    val sorted = exercises.sortedByDescending { it.logTime }
                    _uiState.value = _uiState.value.copy(
                        exercises = sorted,
                        isLoading = false,
                        totalBurned = sorted.sumOf { it.caloriesKcal },
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "加载失败",
                    )
                }
        }
    }

    fun goToPrevDay() {
        _uiState.value = _uiState.value.copy(currentDate = _uiState.value.currentDate.minusDays(1))
        loadLogs()
    }

    fun goToNextDay() {
        _uiState.value = _uiState.value.copy(currentDate = _uiState.value.currentDate.plusDays(1))
        loadLogs()
    }
}
