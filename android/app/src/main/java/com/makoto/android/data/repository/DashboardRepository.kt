package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.*

class DashboardRepository(private val api: MakotoApi) {

    suspend fun getToday(): Result<TodayResponse> = runCatching {
        api.getToday()
    }

    suspend fun getReport(startDate: String, endDate: String): Result<ReportResponse> = runCatching {
        api.getReport(startDate, endDate)
    }
}
