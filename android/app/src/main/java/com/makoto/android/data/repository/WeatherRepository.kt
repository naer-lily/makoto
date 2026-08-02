package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.WeatherForecastResponse

class WeatherRepository(private val api: MakotoApi) {

    suspend fun getForecasts(refresh: Boolean = false): Result<List<WeatherForecastResponse>> =
        runCatching {
            api.getWeatherForecast(refresh)
        }
}
