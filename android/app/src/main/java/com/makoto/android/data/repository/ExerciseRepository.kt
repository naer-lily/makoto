package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.ExerciseLogResponse

class ExerciseRepository(private val api: MakotoApi) {

    suspend fun getExerciseLogs(
        start: String? = null,
        end: String? = null,
        limit: Int? = null,
    ): Result<List<ExerciseLogResponse>> = runCatching {
        api.getExerciseLogs(start, end, limit)
    }
}
