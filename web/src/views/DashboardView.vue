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

    <div v-if="todayData" class="detail-grid">
      <el-card shadow="hover">
        <template #header>
          <div class="detail-card-header">
            <el-icon :size="16"><ForkSpoon /></el-icon>
            <span>今日饮食</span>
            <el-tag size="small" effect="plain" round>{{ todayData.diets.length }} 条</el-tag>
            <div class="header-spacer"></div>
            <el-button size="small" text :disabled="!todayData.diets.length" @click="copyDietMd">
              <el-icon :size="14"><CopyDocument /></el-icon>
            </el-button>
          </div>
        </template>
        <el-empty v-if="!todayData.diets.length" description="今天还没有饮食记录" :image-size="60" />
        <el-table v-else :data="todayData.diets" size="small" stripe>
          <el-table-column label="时间" width="65">
            <template #default="{ row }">
              <span class="time-cell">{{ row.log_time.slice(11, 16) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="food_name" label="食物" min-width="100" />
          <el-table-column prop="grams" label="克数" width="65" align="right">
            <template #default="{ row }">{{ row.grams }}g</template>
          </el-table-column>
          <el-table-column prop="calories_kcal" label="热量" width="75" align="right">
            <template #default="{ row }">{{ row.calories_kcal }}</template>
          </el-table-column>
          <el-table-column prop="protein_g" label="蛋白质" width="70" align="right">
            <template #default="{ row }">{{ row.protein_g }}g</template>
          </el-table-column>
          <el-table-column prop="carbs_g" label="碳水" width="70" align="right">
            <template #default="{ row }">{{ row.carbs_g }}g</template>
          </el-table-column>
          <el-table-column prop="fat_g" label="脂肪" width="70" align="right">
            <template #default="{ row }">{{ row.fat_g }}g</template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="hover">
        <template #header>
          <div class="detail-card-header">
            <el-icon :size="16"><Baseball /></el-icon>
            <span>今日运动</span>
            <el-tag size="small" effect="plain" round>{{ todayData.exercises.length }} 条</el-tag>
            <div class="header-spacer"></div>
            <el-button size="small" text :disabled="!todayData.exercises.length" @click="copyExerciseMd">
              <el-icon :size="14"><CopyDocument /></el-icon>
            </el-button>
          </div>
        </template>
        <el-empty v-if="!todayData.exercises.length" description="今天还没有运动记录" :image-size="60" />
        <el-table v-else :data="todayData.exercises" size="small" stripe>
          <el-table-column label="时间" width="65">
            <template #default="{ row }">
              <span class="time-cell">{{ row.log_time.slice(11, 16) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="exercise_name" label="运动" min-width="100" />
          <el-table-column prop="duration_desc" label="时长" width="130" />
          <el-table-column prop="calories_kcal" label="消耗" width="85" align="right">
            <template #default="{ row }">{{ row.calories_kcal }} kcal</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <div v-if="reportLoading" style="text-align:center;padding:40px">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    </div>

    <template v-else-if="reportData">
      <div class="chart-grid">
        <WeightTrendChart :rows="reportData.rows" :target-weight="reportData.target_weight_kg" />
        <CalorieDeficitChart :rows="reportData.rows" />
      </div>
      <div class="chart-grid">
        <FitnessChart :rows="fitnessData" />
        <WeeklyLoadChart :rows="weeklyLoadData" />
      </div>
      <div class="chart-grid">
        <BodyFatTrendChart :rows="reportData.rows" />
        <WeightFfmChart :rows="reportData.rows" />
      </div>
      <div class="chart-grid">
        <WeeklyLossChart :rows="reportData.rows" />
        <RawWeightChart :rows="reportData.rows" />
      </div>
      <div class="chart-row-full">
        <CircumferenceChart :rows="circData" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchToday, fetchReport, type TodayResponse, type ReportResponse } from '../api/dashboard'
import {
  fetchCircumferenceLogs,
  type CircumferenceRecord,
} from '../api/circumference'
import {
  fetchFitness,
  fetchWeeklyLoad,
  type FitnessRecord,
  type WeeklyLoadRecord,
} from '../api/keep'
import TodayOverview from '../components/TodayOverview.vue'
import WeightTrendChart from '../components/WeightTrendChart.vue'
import CalorieDeficitChart from '../components/CalorieDeficitChart.vue'
import FitnessChart from '../components/FitnessChart.vue'
import WeeklyLoadChart from '../components/WeeklyLoadChart.vue'
import BodyFatTrendChart from '../components/BodyFatTrendChart.vue'
import WeightFfmChart from '../components/WeightFfmChart.vue'
import WeeklyLossChart from '../components/WeeklyLossChart.vue'
import RawWeightChart from '../components/RawWeightChart.vue'
import CircumferenceChart from '../components/CircumferenceChart.vue'

const todayData = ref<TodayResponse | null>(null)
const todayLoading = ref(false)
const reportData = ref<ReportResponse | null>(null)
const reportLoading = ref(false)
const dateRange = ref<[string, string] | null>(null)
const circData = ref<CircumferenceRecord[]>([])
const fitnessData = ref<FitnessRecord[]>([])
const weeklyLoadData = ref<WeeklyLoadRecord[]>([])

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

async function loadCirc() {
  try {
    circData.value = await fetchCircumferenceLogs()
  } catch {
    // non-critical
  }
}

async function loadKeep() {
  try {
    fitnessData.value = await fetchFitness()
  } catch {
    // non-critical
  }
  try {
    weeklyLoadData.value = await fetchWeeklyLoad()
  } catch {
    // non-critical
  }
}

function copyDietMd() {
  const rows = todayData.value?.diets ?? []
  if (!rows.length) return
  let md = '| 时间 | 食物 | 克数 | 热量 | 蛋白质 | 碳水 | 脂肪 |\n'
  md += '|------|------|------|------|--------|------|------|\n'
  for (const r of rows) {
    const t = r.log_time.slice(11, 16)
    md += `| ${t} | ${r.food_name} | ${r.grams}g | ${r.calories_kcal} | ${r.protein_g}g | ${r.carbs_g}g | ${r.fat_g}g |\n`
  }
  md += `\n**合计**: ${todayData.value!.total_intake_kcal} kcal · 蛋白质 ${todayData.value!.total_protein_g}g · 碳水 ${todayData.value!.total_carbs_g}g · 脂肪 ${todayData.value!.total_fat_g}g`
  navigator.clipboard.writeText(md)
  ElMessage.success('已复制为 Markdown')
}

function copyExerciseMd() {
  const rows = todayData.value?.exercises ?? []
  if (!rows.length) return
  let md = '| 时间 | 运动 | 时长 | 消耗 |\n'
  md += '|------|------|------|------|\n'
  for (const r of rows) {
    const t = r.log_time.slice(11, 16)
    md += `| ${t} | ${r.exercise_name} | ${r.duration_desc} | ${r.calories_kcal} kcal |\n`
  }
  md += `\n**合计**: ${todayData.value!.total_burned_kcal} kcal`
  navigator.clipboard.writeText(md)
  ElMessage.success('已复制为 Markdown')
}

onMounted(() => {
  loadToday()
  loadReport()
  loadCirc()
  loadKeep()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.header-spacer {
  flex: 1;
}

.time-cell {
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.chart-row-full {
  display: grid;
  grid-template-columns: 1fr;
  margin-bottom: 20px;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
