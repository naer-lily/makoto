<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">数据总览</h2>
      <div style="display:flex;gap:12px">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          size="default"
          @change="loadReport"
        />
      </div>
    </div>

    <TodayOverview :data="todayData" :loading="todayLoading" />

    <div v-if="reportLoading" style="text-align:center;padding:40px">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <template v-else-if="reportData">
      <div class="chart-grid">
        <WeightTrendChart :rows="reportData.rows" :target-weight="reportData.target_weight_kg" />
        <CalorieDeficitChart :rows="reportData.rows" />
        <BodyFatTrendChart :rows="reportData.rows" />
      </div>
      <div class="chart-grid">
        <WeightFfmChart :rows="reportData.rows" />
        <WeeklyLossChart :rows="reportData.rows" />
        <RawWeightChart :rows="reportData.rows" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchToday, fetchReport, type TodayResponse, type ReportResponse } from '../api/dashboard'
import TodayOverview from '../components/TodayOverview.vue'
import WeightTrendChart from '../components/WeightTrendChart.vue'
import CalorieDeficitChart from '../components/CalorieDeficitChart.vue'
import BodyFatTrendChart from '../components/BodyFatTrendChart.vue'
import WeightFfmChart from '../components/WeightFfmChart.vue'
import WeeklyLossChart from '../components/WeeklyLossChart.vue'
import RawWeightChart from '../components/RawWeightChart.vue'

const todayData = ref<TodayResponse | null>(null)
const todayLoading = ref(false)
const reportData = ref<ReportResponse | null>(null)
const reportLoading = ref(false)
const dateRange = ref<[string, string] | null>(null)

async function loadToday() {
  todayLoading.value = true
  try {
    todayData.value = await fetchToday()
  } finally {
    todayLoading.value = false
  }
}

async function loadReport() {
  reportLoading.value = true
  try {
    const [start, end] = dateRange.value || [undefined, undefined]
    reportData.value = await fetchReport(start, end)
  } finally {
    reportLoading.value = false
  }
}

onMounted(() => {
  loadToday()
  loadReport()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
