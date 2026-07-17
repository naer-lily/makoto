package com.makoto.android.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.local.SettingsStore
import com.makoto.android.data.remote.ApiProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val serverUrl: String = SettingsStore.DEFAULT_SERVER_URL,
    val token: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
    val isConnected: Boolean = false,
)

class LoginViewModel(
    private val settingsStore: SettingsStore,
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun updateServerUrl(url: String) {
        _uiState.value = _uiState.value.copy(serverUrl = url, error = null)
    }

    fun updateToken(token: String) {
        _uiState.value = _uiState.value.copy(token = token, error = null)
    }

    fun connect() {
        val state = _uiState.value
        if (state.serverUrl.isBlank() || state.token.isBlank()) {
            _uiState.value = state.copy(error = "请填写服务器地址和 Token")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val api = ApiProvider.get(state.serverUrl, state.token)
                api.getProfile()

                settingsStore.setServerUrl(state.serverUrl)
                settingsStore.setToken(state.token)

                _uiState.value = _uiState.value.copy(isLoading = false, isConnected = true)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "连接失败: ${e.localizedMessage ?: "未知错误"}",
                )
            }
        }
    }
}
