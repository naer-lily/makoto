<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">天气监视</h2>
      <el-button type="primary" :loading="refreshing" @click="handleRefresh">
        <el-icon :size="16"><Refresh /></el-icon>
        刷新预报
      </el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="监视地点" name="watches">
        <div style="margin-bottom:16px">
          <el-form :inline="true" :model="watchForm" class="watch-form">
            <el-form-item label="标签">
              <el-input v-model="watchForm.label" placeholder="例如: 北京" clearable />
            </el-form-item>
            <el-form-item label="纬度">
              <el-input-number v-model="watchForm.latitude" :min="-90" :max="90" :precision="4" />
            </el-form-item>
            <el-form-item label="经度">
              <el-input-number v-model="watchForm.longitude" :min="-180" :max="180" :precision="4" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="adding" @click="handleAdd">
                {{ editingId ? '保存修改' : '添加地点' }}
              </el-button>
              <el-button v-if="editingId" @click="cancelEdit">取消编辑</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="watches" stripe style="width:100%">
          <el-table-column prop="id" label="ID" width="60" align="right" />
          <el-table-column prop="label" label="标签" min-width="100" />
          <el-table-column prop="latitude" label="纬度" width="120" align="right">
            <template #default="{ row }">{{ row.latitude.toFixed(4) }}</template>
          </el-table-column>
          <el-table-column prop="longitude" label="经度" width="120" align="right">
            <template #default="{ row }">{{ row.longitude.toFixed(4) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="startEdit(row)">编辑</el-button>
              <el-popconfirm title="确定删除该监视地点？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" text type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="天气预报" name="forecast">
        <div v-if="forecasts.length === 0" style="text-align:center;padding:40px">
          <el-empty description="暂无天气数据，请先添加监视地点" :image-size="80" />
        </div>
        <div v-for="fc in forecasts" :key="fc.watch_id" class="forecast-section">
          <div class="forecast-header">
            <span class="forecast-label">{{ fc.label }}</span>
            <span class="forecast-coords">{{ fc.latitude.toFixed(2) }}, {{ fc.longitude.toFixed(2) }}</span>
            <el-tag size="small" effect="plain" type="info" class="forecast-time">
              {{ fc.fetched_at ? '更新于 ' + fc.fetched_at.slice(0, 16).replace('T', ' ') : '暂无数据' }}
            </el-tag>
          </div>

          <el-empty
            v-if="!fc.days.length"
            description="等待数据拉取..."
            :image-size="60"
          />

          <div v-else class="day-cards">
            <div
              v-for="day in fc.days"
              :key="day.date"
              class="day-card"
              :class="{ 'day-danger': [95, 96, 99].includes(day.weather_code) }"
            >
              <div class="day-date">{{ day.date.slice(5) }}</div>
              <div class="day-temp">
                <span class="temp-high">{{ Math.round(day.temp_max) }}°</span>
                <span class="temp-sep">/</span>
                <span class="temp-low">{{ Math.round(day.temp_min) }}°</span>
              </div>
              <div class="day-desc">{{ day.weather_desc }}</div>
              <div class="day-precip">
                <span v-if="day.precip_sum > 0" class="precip-val">
                  <el-icon :size="12"><Drizzling /></el-icon>
                  {{ day.precip_sum.toFixed(1) }}mm
                </span>
                <span class="precip-prob">{{ day.precip_probability }}%</span>
              </div>
              <div v-if="[95, 96, 99].includes(day.weather_code)" class="day-warning">
                <el-icon :size="14"><WarningFilled /></el-icon>
                雷暴警告
              </div>
            </div>
          </div>

          <div v-if="fc.hours && fc.hours.length" class="hourly-section">
            <div class="hourly-label">未来 24 小时</div>
            <div class="hourly-strip">
              <div
                v-for="h in fc.hours"
                :key="h.time"
                class="hour-card"
                :class="{ 'hour-danger': [95, 96, 99].includes(h.weather_code) }"
              >
                <div class="hour-time">{{ h.time.slice(11, 16) }}</div>
                <div class="hour-temp">{{ Math.round(h.temp) }}°</div>
                <div class="hour-desc">{{ h.weather_desc }}</div>
                <div class="hour-prob">
                  <el-icon :size="10"><Drizzling /></el-icon>
                  {{ h.precip_probability }}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchWatches,
  createWatch,
  updateWatch,
  deleteWatch,
  fetchAllForecasts,
  type WeatherWatch,
  type WeatherForecast,
} from '../api/weather'

const activeTab = ref('watches')
const watches = ref<WeatherWatch[]>([])
const forecasts = ref<WeatherForecast[]>([])
const refreshing = ref(false)

const watchForm = ref({ label: '', latitude: 39.906, longitude: 116.391 })
const adding = ref(false)
const editingId = ref<number | null>(null)

async function loadWatches() {
  try {
    watches.value = await fetchWatches()
  } catch {
    // handled by interceptor
  }
}

async function loadForecasts(refresh = false) {
  try {
    forecasts.value = await fetchAllForecasts(refresh)
  } catch {
    // handled by interceptor
  }
}

async function handleAdd() {
  if (!watchForm.value.label) {
    ElMessage.warning('请输入地点标签')
    return
  }
  adding.value = true
  try {
    if (editingId.value) {
      await updateWatch(editingId.value, watchForm.value)
      ElMessage.success('已更新')
    } else {
      await createWatch(watchForm.value)
      ElMessage.success('已添加')
    }
    watchForm.value = { label: '', latitude: 39.906, longitude: 116.391 }
    editingId.value = null
    await loadWatches()
    await loadForecasts(true)
  } finally {
    adding.value = false
  }
}

function startEdit(row: WeatherWatch) {
  watchForm.value = { label: row.label, latitude: row.latitude, longitude: row.longitude }
  editingId.value = row.id
}

function cancelEdit() {
  watchForm.value = { label: '', latitude: 39.906, longitude: 116.391 }
  editingId.value = null
}

async function handleDelete(id: number) {
  try {
    await deleteWatch(id)
    ElMessage.success('已删除')
    await loadWatches()
    await loadForecasts()
  } catch {
    // handled by interceptor
  }
}

async function handleRefresh() {
  refreshing.value = true
  try {
    await loadForecasts(true)
    ElMessage.success('预报已刷新')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadWatches()
  loadForecasts()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.watch-form {
  display: flex;
  flex-wrap: wrap;
}

.forecast-section {
  margin-bottom: 24px;
}

.forecast-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.forecast-label {
  font-size: 16px;
  font-weight: 600;
}

.forecast-coords {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.forecast-time {
  margin-left: auto;
}

.day-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.day-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  text-align: center;
  transition: box-shadow 0.2s;
}

.day-card:hover {
  box-shadow: var(--el-box-shadow-light);
}

.day-card.day-danger {
  border-color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.day-date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.day-temp {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.temp-high {
  color: var(--el-color-danger);
}

.temp-sep {
  color: var(--el-text-color-secondary);
  font-weight: 400;
  margin: 0 2px;
}

.temp-low {
  color: var(--el-color-info);
}

.day-desc {
  font-size: 13px;
  margin-bottom: 6px;
}

.day-precip {
  font-size: 12px;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.precip-prob {
  color: var(--el-text-color-secondary);
}

.day-warning {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-color-danger);
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.hourly-section {
  margin-top: 16px;
}

.hourly-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.hourly-strip {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.hourly-strip::-webkit-scrollbar {
  height: 4px;
}

.hourly-strip::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 2px;
}

.hour-card {
  flex: 0 0 auto;
  width: 72px;
  background: var(--el-bg-color);
  border-radius: 6px;
  padding: 8px 4px;
  border: 1px solid var(--el-border-color-light);
  text-align: center;
}

.hour-card.hour-danger {
  border-color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.hour-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.hour-temp {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 2px;
}

.hour-desc {
  font-size: 11px;
  margin-bottom: 4px;
  white-space: nowrap;
}

.hour-prob {
  font-size: 10px;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .watch-form {
    flex-direction: column;
  }

  .watch-form .el-form-item {
    margin-right: 0;
    margin-bottom: 8px;
  }

  .day-cards {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 8px;
  }

  .day-card {
    padding: 8px;
  }

  .day-temp {
    font-size: 16px;
  }
}
</style>
