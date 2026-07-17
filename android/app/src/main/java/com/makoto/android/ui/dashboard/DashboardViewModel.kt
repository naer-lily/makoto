package com.makoto.android.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.TodayResponse
import com.makoto.android.data.repository.DashboardRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DashboardUiState(
    val today: TodayResponse? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
)

class DashboardViewModel(
    private val dashboardRepo: DashboardRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadToday()
    }

    fun loadToday() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            dashboardRepo.getToday()
                .onSuccess { data ->
                    _uiState.value = _uiState.value.copy(
                        today = data,
                        isLoading = false,
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
}
