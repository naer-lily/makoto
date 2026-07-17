package com.makoto.android.ui.diet

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.DietLogResponse
import com.makoto.android.data.repository.DietRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

data class DietUiState(
    val diets: List<DietLogResponse> = emptyList(),
    val currentDate: LocalDate = LocalDate.now(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val totalCalories: Double = 0.0,
    val totalProtein: Double = 0.0,
)

class DietViewModel(
    private val dietRepo: DietRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DietUiState())
    val uiState: StateFlow<DietUiState> = _uiState.asStateFlow()

    init {
        loadLogs()
    }

    fun loadLogs() {
        val date = _uiState.value.currentDate
        val dateStr = date.format(DateTimeFormatter.ISO_LOCAL_DATE)
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            dietRepo.getDietLogs(start = dateStr, end = dateStr)
                .onSuccess { diets ->
                    val sorted = diets.sortedByDescending { it.logTime }
                    _uiState.value = _uiState.value.copy(
                        diets = sorted,
                        isLoading = false,
                        totalCalories = sorted.sumOf { it.caloriesKcal },
                        totalProtein = sorted.sumOf { it.proteinG },
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
