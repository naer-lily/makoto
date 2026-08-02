package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.BodyLogResponse
import com.makoto.android.data.remote.dto.ReportResponse

class BodyRepository(private val api: MakotoApi) {

    suspend fun getBodyLogs(start: String? = null, end: String? = null): Result<List<BodyLogResponse>> =
        runCatching {
            api.getBodyLogs(start, end)
        }

    suspend fun getReport(startDate: String, endDate: String): Result<ReportResponse> = runCatching {
        api.getReport(startDate, endDate)
    }
}
