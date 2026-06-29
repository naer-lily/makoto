<template>
  <div v-if="acwr != null || weeklyLoad" class="keep-status">
    <div v-if="acwr != null" class="keep-card" :class="acwrZone">
      <div class="keep-label">ACWR</div>
      <div class="keep-value">{{ acwr }}</div>
      <div class="keep-sub">{{ acwrLabel }}</div>
    </div>
    <div v-if="ctl != null" class="keep-card">
      <div class="keep-label">CTL 体能</div>
      <div class="keep-value">{{ ctl }}</div>
    </div>
    <div v-if="weeklyLoad" class="keep-card">
      <div class="keep-label">本周训练负荷</div>
      <div class="keep-value">{{ weeklyLoad }}</div>
    </div>
    <div v-if="loadLower != null && loadUpper != null" class="keep-card">
      <div class="keep-label">本周推荐区间</div>
      <div class="keep-value">{{ loadLower }} - {{ loadUpper }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FitnessRecord, WeeklyLoadRecord } from '../api/keep'

const props = defineProps<{
  fitness: FitnessRecord[]
  weekly: WeeklyLoadRecord[]
}>()

const latestFitness = computed(() => props.fitness[props.fitness.length - 1] ?? null)
const latestWeekly = computed(() => {
  const sorted = [...props.weekly].sort(
    (a, b) => b.week_start.localeCompare(a.week_start),
  )
  return sorted[0] ?? null
})

const ctl = computed(() => latestFitness.value?.ctl ?? null)
const acwr = computed(() => {
  const f = latestFitness.value
  if (!f || f.ctl <= 0) return null
  return +(f.atl / f.ctl).toFixed(2)
})
const acwrLabel = computed(() => {
  const v = acwr.value
  if (v == null) return ''
  if (v < 0.8) return '负荷过低'
  if (v < 1.3) return '安全区'
  if (v < 1.5) return '风险监控'
  return '危险区'
})
const acwrZone = computed(() => {
  const v = acwr.value
  if (v == null) return ''
  if (v < 0.8) return 'zone-low'
  if (v < 1.3) return 'zone-safe'
  if (v < 1.5) return 'zone-warn'
  return 'zone-danger'
})
const weeklyLoad = computed(() => latestWeekly.value?.training_load ?? null)
const loadLower = computed(() => latestWeekly.value?.load_lower ?? null)
const loadUpper = computed(() => latestWeekly.value?.load_upper ?? null)
</script>

<style scoped>
.keep-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.keep-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 12px 16px;
  text-align: center;
}

.keep-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.keep-value {
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.keep-sub {
  font-size: 11px;
  margin-top: 2px;
}

.zone-low .keep-value { color: #909399; }
.zone-safe .keep-value { color: #67c23a; }
.zone-warn .keep-value { color: #e6a23c; }
.zone-danger .keep-value { color: #f56c6c; }
</style>
