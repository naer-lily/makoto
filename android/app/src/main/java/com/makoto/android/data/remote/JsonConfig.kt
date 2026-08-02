package com.makoto.android.data.remote

import kotlinx.serialization.json.Json

internal val makotoJson = Json {
    ignoreUnknownKeys = true
    isLenient = true
}
