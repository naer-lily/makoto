package com.makoto.android.widget

import android.content.Context
import android.util.Log
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.layout.Alignment
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import com.makoto.android.data.local.SettingsStore
import com.makoto.android.data.remote.ApiProvider
import kotlinx.coroutines.flow.first

class MakotoWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val settingsStore = SettingsStore(context.applicationContext)
        val serverUrl = try {
            settingsStore.serverUrl.first()
        } catch (_: Exception) {
            SettingsStore.DEFAULT_SERVER_URL
        }
        val token = try {
            settingsStore.token.first()
        } catch (_: Exception) {
            ""
        }

        if (token.isBlank()) {
            provideContent { NotConfiguredContent() }
        } else {
            try {
                val api = ApiProvider.get(serverUrl, token)
                val today = api.getToday()
                val netText = if (today.netKcal >= 0) "+${today.netKcal.toInt()}" else today.netKcal.toInt().toString()
                val netColor = if (today.netKcal >= 0) 0xFF4CAF50.toInt() else 0xFFF44336.toInt()
                provideContent { TodayContent(today, netText, netColor) }
            } catch (e: Exception) {
                Log.e("MakotoWidget", "Failed", e)
                provideContent { ErrorContent() }
            }
        }
    }

    companion object {
        private fun netColor(netKcal: Double): Int =
            if (netKcal >= 0) 0xFF4CAF50.toInt() else 0xFFF44336.toInt()
    }
}

class MakotoWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = MakotoWidget()
}

@androidx.compose.runtime.Composable
private fun NotConfiguredContent() {
    Column(
        modifier = GlanceModifier.fillMaxSize(),
        verticalAlignment = Alignment.Vertical.CenterVertically,
        horizontalAlignment = Alignment.Horizontal.CenterHorizontally,
    ) {
        Text(text = "makoto", style = TextStyle(fontWeight = FontWeight.Bold))
        Text(text = "未配置 Token")
    }
}

@androidx.compose.runtime.Composable
private fun TodayContent(today: com.makoto.android.data.remote.dto.TodayResponse, netText: String, netColor: Int) {
    Column(modifier = GlanceModifier.fillMaxSize()) {
        Row(modifier = GlanceModifier.fillMaxWidth()) {
            Text(text = "makoto ", style = TextStyle(fontWeight = FontWeight.Bold))
            Text(text = today.date.takeLast(5))
        }
        Row(modifier = GlanceModifier.fillMaxWidth()) {
            WidgetData("摄入", "${today.totalIntakeKcal.toInt()}", "kcal", 0xFFFF9800.toInt())
            WidgetData("消耗", "${today.totalBurnedKcal.toInt()}", "kcal", 0xFFF44336.toInt())
            WidgetData("净热量", netText, "kcal", netColor)
            WidgetData("蛋白质", "${today.totalProteinG.toInt()}", "g", 0xFF2196F3.toInt())
        }
    }
}

@androidx.compose.runtime.Composable
private fun ErrorContent() {
    Column(
        modifier = GlanceModifier.fillMaxSize(),
        verticalAlignment = Alignment.Vertical.CenterVertically,
        horizontalAlignment = Alignment.Horizontal.CenterHorizontally,
    ) {
        Text(text = "makoto", style = TextStyle(fontWeight = FontWeight.Bold))
        Text(text = "加载失败")
    }
}

@androidx.compose.runtime.Composable
private fun WidgetData(label: String, value: String, unit: String, color: Int) {
    Column(horizontalAlignment = Alignment.Horizontal.CenterHorizontally) {
        Text(text = label)
        Text(
            text = value,
            style = TextStyle(fontWeight = FontWeight.Bold, color = ColorProvider(color)),
        )
        Text(text = unit)
    }
}
