package com.makoto.android.ui.weather

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.WeatherForecastResponse
import com.makoto.android.data.repository.WeatherRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class WeatherUiState(
    val forecasts: List<WeatherForecastResponse> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
)

class WeatherViewModel(
    private val weatherRepo: WeatherRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(WeatherUiState())
    val uiState: StateFlow<WeatherUiState> = _uiState.asStateFlow()

    init {
        loadForecasts()
    }

    fun loadForecasts(refresh: Boolean = false) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = !refresh,
                isRefreshing = refresh,
                error = null,
            )
            weatherRepo.getForecasts(refresh)
                .onSuccess { forecasts ->
                    _uiState.value = _uiState.value.copy(
                        forecasts = forecasts,
                        isLoading = false,
                        isRefreshing = false,
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isRefreshing = false,
                        error = e.localizedMessage ?: "加载失败",
                    )
                }
        }
    }

    fun refresh() = loadForecasts(refresh = true)
}
