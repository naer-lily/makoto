package com.makoto.android.data.repository

import com.makoto.android.data.remote.MakotoApi
import com.makoto.android.data.remote.dto.ProfileResponse

class ProfileRepository(private val api: MakotoApi) {

    suspend fun getProfile(): Result<ProfileResponse> = runCatching {
        api.getProfile()
    }
}
