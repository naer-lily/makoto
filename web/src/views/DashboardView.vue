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

    <el-tabs v-model="activeTab" class="dash-tabs" @tab-change="onTabChange">
      <el-tab-pane label="概览" name="overview">
        <TodayOverview :data="todayData" :loading="todayLoading" />

        <KeepStatus :fitness="fitnessData" :weekly="weeklyLoadData" />

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

        <el-card v-if="todayData" shadow="hover" class="painting-card">
          <template #header>
            <div class="detail-card-header">
              <el-icon :size="16"><Brush /></el-icon>
              <span>今日绘画</span>
              <el-tag v-if="todayData.painting.painted_today" size="small" effect="plain" round type="success">已打卡</el-tag>
              <el-tag v-else size="small" effect="plain" round type="info">未打卡</el-tag>
              <div class="header-spacer"></div>
              <span class="streak-info">
                连续 {{ todayData.painting.current_streak }} 天
                · 最长 {{ todayData.painting.longest_streak }} 天
                · 累计 {{ todayData.painting.total_days }} 天
              </span>
            </div>
          </template>
          <el-empty v-if="!todayData.painting.sessions.length" description="今天还没有绘画记录" :image-size="60" />
          <el-table v-else :data="todayData.painting.sessions" size="small" stripe>
            <el-table-column label="时间" width="65">
              <template #default="{ row }">
                <span class="time-cell">{{ row.log_time.slice(11, 16) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="file_id" label="文件 ID" min-width="180" />
            <el-table-column prop="duration_seconds" label="时长" width="100" align="right">
              <template #default="{ row }">{{ formatDuration(row.duration_seconds) }}</template>
            </el-table-column>
          </el-table>
          <div v-if="todayData.painting.sessions.length" class="painting-summary">
            今日 {{ todayData.painting.session_count }} 次会话 · 合计 {{ formatDuration(todayData.painting.duration_seconds) }}
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="体重与体成分" name="weight">
        <div v-if="reportLoading" style="text-align:center;padding:40px">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        </div>
        <template v-else-if="reportData">
          <div class="chart-grid">
            <WeightTrendChart :rows="reportData.rows" :target-weight="reportData.target_weight_kg" :target-date="reportData.target_date" />
            <BodyFatTrendChart :rows="reportData.rows" />
          </div>
          <div class="chart-grid">
            <WeightFfmChart :rows="reportData.rows" />
            <BodyCompChart :rows="reportData.rows" />
          </div>
          <div class="chart-grid">
            <RawWeightChart :rows="reportData.rows" />
            <WeeklyLossChart :rows="reportData.rows" />
          </div>
        </template>
      </el-tab-pane>

      <el-tab-pane label="热量与运动负荷" name="calories">
        <div v-if="reportLoading" style="text-align:center;padding:40px">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        </div>
        <template v-else-if="reportData">
          <div class="chart-grid">
            <CalorieDeficitChart :rows="reportData.rows" />
            <IntakeTdeeChart :rows="reportData.rows" />
          </div>
          <div class="chart-grid">
            <FitnessChart :rows="fitnessData" />
            <WeeklyLoadChart :rows="weeklyLoadData" />
          </div>
        </template>
      </el-tab-pane>

      <el-tab-pane label="围度" name="circ">
        <div v-if="reportLoading" style="text-align:center;padding:40px">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        </div>
        <template v-else-if="reportData">
          <div class="chart-grid chart-full">
            <CircumferenceChart :rows="circData" />
          </div>
        </template>
      </el-tab-pane>
    </el-tabs>
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
import KeepStatus from '../components/KeepStatus.vue'
import WeightTrendChart from '../components/WeightTrendChart.vue'
import CalorieDeficitChart from '../components/CalorieDeficitChart.vue'
import IntakeTdeeChart from '../components/IntakeTdeeChart.vue'
import FitnessChart from '../components/FitnessChart.vue'
import WeeklyLoadChart from '../components/WeeklyLoadChart.vue'
import BodyFatTrendChart from '../components/BodyFatTrendChart.vue'
import WeightFfmChart from '../components/WeightFfmChart.vue'
import BodyCompChart from '../components/BodyCompChart.vue'
import WeeklyLossChart from '../components/WeeklyLossChart.vue'
import RawWeightChart from '../components/RawWeightChart.vue'
import CircumferenceChart from '../components/CircumferenceChart.vue'

const activeTab = ref('overview')
const todayData = ref<TodayResponse | null>(null)
const todayLoading = ref(false)
const reportData = ref<ReportResponse | null>(null)
const reportLoading = ref(false)
const dateRange = ref<[string, string] | null>(null)
const circData = ref<CircumferenceRecord[]>([])
const fitnessData = ref<FitnessRecord[]>([])
const weeklyLoadData = ref<WeeklyLoadRecord[]>([])

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m} 分 ${s} 秒`
  }
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h} 小时 ${m} 分`
}

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
    await loadKeep()
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
  const [start, end] = dateRange.value || [undefined, undefined]
  try {
    fitnessData.value = await fetchFitness(start, end)
  } catch {
    // non-critical
  }
  let weekCount: number | undefined
  if (start && end) {
    const days = Math.ceil((new Date(end).getTime() - new Date(start).getTime()) / 86400000)
    weekCount = Math.ceil(days / 7)
  }
  try {
    weeklyLoadData.value = await fetchWeeklyLoad(weekCount)
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

function onTabChange(name: string | number) {
  // trigger resize when switching to a chart tab
  if (name !== 'overview') {
    setTimeout(() => window.dispatchEvent(new Event('resize')), 50)
  }
}

onMounted(() => {
  loadToday()
  loadReport()
  loadCirc()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.dash-tabs {
  margin-top: 0;
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

.painting-card {
  margin-bottom: 20px;
}

.streak-info {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.painting-summary {
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .toolbar > div {
    width: 100%;
  }

  .toolbar > div > .el-date-editor {
    width: 100%;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
