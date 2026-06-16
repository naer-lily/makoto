<template>
  <div v-loading="loading">
    <div class="stat-row">
      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(64,158,255,0.12); color: #409EFF">
          <el-icon :size="20"><TrendCharts /></el-icon>
        </div>
        <div class="stat-label">体重</div>
        <div class="stat-value">
          <template v-if="data?.body?.weight_kg != null">
            {{ data.body.weight_kg }} <span class="unit">kg</span>
          </template>
          <span v-else class="na">--</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(155,89,182,0.12); color: #9B59B6">
          <el-icon :size="20"><PieChart /></el-icon>
        </div>
        <div class="stat-label">体脂率</div>
        <div class="stat-value">
          <template v-if="data?.body?.body_fat_pct != null">
            {{ data.body.body_fat_pct }}<span class="unit">%</span>
          </template>
          <span v-else class="na">--</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(103,194,58,0.12); color: #67C23A">
          <el-icon :size="20"><Sunny /></el-icon>
        </div>
        <div class="stat-label">REE 基础消耗</div>
        <div class="stat-value">
          {{ data?.ree_kcal ?? '--' }} <span class="unit">kcal/天</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(230,162,60,0.12); color: #E6A23C">
          <el-icon :size="20"><ForkSpoon /></el-icon>
        </div>
        <div class="stat-label">今日摄入</div>
        <div class="stat-value">
          {{ data?.total_intake_kcal ?? '--' }} <span class="unit">kcal</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(103,128,200,0.12); color: #6788C8">
          <el-icon :size="20"><DataLine /></el-icon>
        </div>
        <div class="stat-label">净热量</div>
        <div class="stat-value" :class="netClass">
          {{ data ? (data.net_kcal >= 0 ? '+' : '') + data.net_kcal.toFixed(0) : '--' }}
          <span class="unit">kcal</span>
        </div>
      </el-card>
    </div>

    <div class="stat-row">
      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(245,108,108,0.12); color: #F56C6C">
          <el-icon :size="20"><Baseball /></el-icon>
        </div>
        <div class="stat-label">运动消耗</div>
        <div class="stat-value">
          {{ data?.total_burned_kcal ?? '--' }} <span class="unit">kcal</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(84,112,198,0.12); color: #5470C6">
          <el-icon :size="20"><Star /></el-icon>
        </div>
        <div class="stat-label">蛋白质</div>
        <div class="stat-value">
          {{ data?.total_protein_g ?? '--' }} <span class="unit">g</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(230,162,60,0.12); color: #E6A23C">
          <el-icon :size="20"><Apple /></el-icon>
        </div>
        <div class="stat-label">碳水</div>
        <div class="stat-value">
          {{ data?.total_carbs_g ?? '--' }} <span class="unit">g</span>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-icon-wrap" style="background: rgba(245,108,108,0.12); color: #F56C6C">
          <el-icon :size="20"><WarningFilled /></el-icon>
        </div>
        <div class="stat-label">脂肪</div>
        <div class="stat-value">
          {{ data?.total_fat_g ?? '--' }} <span class="unit">g</span>
        </div>
      </el-card>
    </div>
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
.stat-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.stat-row + .stat-row {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 20px;
}

.stat-card {
  border: 1px solid var(--el-border-color-lighter);
  transition: transform 0.15s, box-shadow 0.15s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  margin-bottom: 12px;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}

.stat-value .unit {
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

@media (max-width: 1200px) {
  .stat-row,
  .stat-row + .stat-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stat-row,
  .stat-row + .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
