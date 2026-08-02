package com.makoto.android.data.remote

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object ApiProvider {

    private var currentApi: MakotoApi? = null
    private var currentBaseUrl: String = ""
    private var currentToken: String = ""

    fun get(baseUrl: String, token: String): MakotoApi {
        val normalizedUrl = normalizeUrl(baseUrl)
        if (currentApi != null && currentBaseUrl == normalizedUrl && currentToken == token) {
            return currentApi!!
        }

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor { token })
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(normalizedUrl)
            .client(client)
            .addConverterFactory(makotoJson.asConverterFactory("application/json".toMediaType()))
            .build()

        val api = retrofit.create(MakotoApi::class.java)
        currentApi = api
        currentBaseUrl = normalizedUrl
        currentToken = token
        return api
    }

    private fun normalizeUrl(url: String): String {
        var result = url.trim()
        if (!result.startsWith("http://") && !result.startsWith("https://")) {
            result = "https://$result"
        }
        if (!result.endsWith("/")) {
            result = "$result/"
        }
        return result
    }
}
