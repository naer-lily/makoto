package com.makoto.android

import android.app.Application
import com.makoto.android.data.remote.ApiProvider

class MakotoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: MakotoApp
            private set
    }
}
