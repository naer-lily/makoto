package com.makoto.android.ui.body

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.BodyLogResponse
import com.makoto.android.data.remote.dto.ReportResponse
import com.makoto.android.data.repository.BodyRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

data class BodyUiState(
    val bodyLogs: List<BodyLogResponse> = emptyList(),
    val report: ReportResponse? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
)

class BodyViewModel(
    private val bodyRepo: BodyRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(BodyUiState())
    val uiState: StateFlow<BodyUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    private fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            val today = LocalDate.now()
            val startDate = today.minus(90, ChronoUnit.DAYS)
            val endDate = today
            val startStr = startDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
            val endStr = endDate.format(DateTimeFormatter.ISO_LOCAL_DATE)

            var logs: List<BodyLogResponse> = emptyList()
            var report: ReportResponse? = null

            bodyRepo.getBodyLogs()
                .onSuccess { logs = it.sortedByDescending { it.logDate } }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "加载失败",
                    )
                    return@launch
                }

            bodyRepo.getReport(startDate = startStr, endDate = endStr)
                .onSuccess { report = it }
                .onFailure { /* chart data optional */ }

            _uiState.value = _uiState.value.copy(
                bodyLogs = logs,
                report = report,
                isLoading = false,
            )
        }
    }
}
