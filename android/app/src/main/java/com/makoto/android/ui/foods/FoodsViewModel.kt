package com.makoto.android.ui.foods

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.makoto.android.data.remote.dto.FoodResponse
import com.makoto.android.data.repository.FoodRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class FoodsUiState(
    val foods: List<FoodResponse> = emptyList(),
    val searchQuery: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
)

class FoodsViewModel(
    private val foodRepo: FoodRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(FoodsUiState())
    val uiState: StateFlow<FoodsUiState> = _uiState.asStateFlow()

    private var searchJob: Job? = null

    init {
        loadFoods()
    }

    fun loadFoods() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            foodRepo.getFoods()
                .onSuccess { foods ->
                    _uiState.value = _uiState.value.copy(
                        foods = foods.sortedBy { it.name },
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

    fun onSearchQueryChanged(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        searchJob?.cancel()
        if (query.isBlank()) {
            loadFoods()
        } else {
            searchJob = viewModelScope.launch {
                delay(300)
                _uiState.value = _uiState.value.copy(isLoading = true)
                foodRepo.searchFoods(query)
                    .onSuccess {
                        _uiState.value = _uiState.value.copy(
                            foods = emptyList(), // search results don't include full food data
                            isLoading = false,
                        )
                    }
                    .onFailure { e ->
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = e.localizedMessage ?: "搜索失败",
                        )
                    }
            }
        }
    }
}
