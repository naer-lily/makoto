<template>
  <div class="card-row">
    <el-card shadow="hover">
      <div class="stat-label">体重</div>
      <div class="stat-value">
        <template v-if="data?.body">
          {{ data.body.weight_kg }} <small>kg</small>
        </template>
        <span v-else class="na">-</span>
      </div>
    </el-card>
    <el-card shadow="hover">
      <div class="stat-label">体脂率</div>
      <div class="stat-value">
        <template v-if="data?.body">
          {{ data.body.body_fat_pct }}<small>%</small>
        </template>
        <span v-else class="na">-</span>
      </div>
    </el-card>
    <el-card shadow="hover">
      <div class="stat-label">REE 基础消耗</div>
      <div class="stat-value">
        {{ data?.ree_kcal ?? '-' }} <small>kcal/天</small>
      </div>
    </el-card>
    <el-card shadow="hover">
      <div class="stat-label">今日摄入</div>
      <div class="stat-value">{{ data?.total_intake_kcal ?? '-' }} <small>kcal</small></div>
    </el-card>
    <el-card shadow="hover">
      <div class="stat-label">净热量</div>
      <div class="stat-value" :class="netClass">
        {{ data ? (data.net_kcal >= 0 ? '+' : '') + data.net_kcal.toFixed(0) : '-' }}
        <small>kcal</small>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TodayResponse } from '../api/dashboard'

const props = defineProps<{
  data: TodayResponse | null
  loading: boolean
}>()

const netClass = computed(() => {
  if (!props.data) return ''
  return props.data.net_kcal > 0 ? 'positive' : props.data.net_kcal < 0 ? 'negative' : ''
})
</script>

<style scoped>
.card-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}

.stat-value small {
  font-size: 13px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
}

.na {
  color: var(--el-text-color-placeholder);
  font-weight: 400;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #e6a23c;
}
</style>
