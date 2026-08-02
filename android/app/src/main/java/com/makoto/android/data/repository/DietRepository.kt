package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.DietLogResponse

class DietRepository(private val api: MakotoApi) {

    suspend fun getDietLogs(
        start: String? = null,
        end: String? = null,
        limit: Int? = null,
    ): Result<List<DietLogResponse>> = runCatching {
        api.getDietLogs(start, end, limit)
    }
}
