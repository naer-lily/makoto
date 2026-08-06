<template>
  <div class="chart-container">
    <el-button class="chart-copy-btn" size="small" text @click="handleCopy">
      <el-icon :size="14"><CopyDocument /></el-icon>
    </el-button>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ReportRow } from '../api/dashboard'
import { useTheme } from '../composables/useTheme'
import { useEChartsResize } from '../composables/useEChartsResize'
import { useCopyChartMd } from '../composables/useCopyChartMd'

const { isDark } = useTheme()
const { copyChartMd } = useCopyChartMd()

const props = defineProps<{ rows: ReportRow[] }>()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

// EA 四档折线点颜色：<20 偏低(红) / 20-30 适中(橙) / 30-40 良好(绿) / >=40 最佳(蓝)
function bandColorFor(ea: number | null): string {
  if (ea == null) return '#909399'
  if (ea < 20) return '#F56C6C'
  if (ea < 30) return '#E6A23C'
  if (ea < 40) return '#67C23A'
  return '#409EFF'
}

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const ea = props.rows.map((r) => r.ea_kcal_per_kg_ffm)

  const bandLabel = (formatter: string, color: string) => ({
    show: true,
    position: 'inside' as const,
    formatter,
    color,
    fontSize: 11,
  })

  return {
    backgroundColor: 'transparent',
    title: { text: '能量可用性 (EA)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params]
        const idx = items[0]?.dataIndex ?? 0
        const row = props.rows[idx]
        if (!row) return ''
        return (
          `${items[0]?.axisValue}<br/>` +
          `能量可用性: <b>${row.ea_kcal_per_kg_ffm ?? '--'} kcal/kg FFM</b><br/>` +
          `摄入: ${row.intake_kcal} kcal<br/>` +
          `运动: ${row.exercise_kcal} kcal<br/>` +
          `去脂体重: ${row.ffm_kg} kg`
        )
      },
    },
    grid: { top: 60, right: 20, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kcal/kg FFM',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
      max: (value: { max: number }) => Math.max(45, Math.ceil(value.max)),
    },
    series: [
      {
        name: '能量可用性',
        type: 'line',
        data: ea,
        smooth: true,
        lineStyle: { color: '#5470C6', width: 2 },
        itemStyle: {
          color: (params: any) => bandColorFor(params.value),
        },
        markArea: {
          silent: true,
          data: [
            [
              {
                yAxis: 0,
                itemStyle: { color: 'rgba(245,108,108,0.10)' },
                label: bandLabel('偏低 <20', '#F56C6C'),
              },
              { yAxis: 20 },
            ],
            [
              {
                yAxis: 20,
                itemStyle: { color: 'rgba(230,162,60,0.10)' },
                label: bandLabel('适中 20-30', '#E6A23C'),
              },
              { yAxis: 30 },
            ],
            [
              {
                yAxis: 30,
                itemStyle: { color: 'rgba(103,194,58,0.10)' },
                label: bandLabel('良好 30-40', '#67C23A'),
              },
              { yAxis: 40 },
            ],
            [
              {
                yAxis: 40,
                itemStyle: { color: 'rgba(64,158,255,0.10)' },
                label: bandLabel('最佳 ≥40', '#409EFF'),
              },
              { yAxis: 'max' },
            ],
          ],
        },
      },
    ],
  }
}

function initChart() {
  if (!chartRef.value) return
  chart.value?.dispose()
  chart.value = echarts.init(chartRef.value!, isDark.value ? 'dark' : undefined)
  chart.value.setOption(buildOption())
}

function handleCopy() {
  const rows = props.rows.map((r) => [
    r.date.substring(5),
    r.ea_kcal_per_kg_ffm != null ? String(r.ea_kcal_per_kg_ffm) : '-',
    String(r.intake_kcal),
    String(r.exercise_kcal),
    String(r.ffm_kg),
  ])
  copyChartMd(
    '能量可用性',
    ['日期', 'EA (kcal/kg FFM)', '摄入 (kcal)', '运动 (kcal)', 'FFM (kg)'],
    rows,
  )
}

onMounted(() => {
  initChart()
})

watch(() => props.rows, () => chart.value?.setOption(buildOption()), { deep: true })
watch(isDark, () => initChart())

onUnmounted(() => {
  chart.value?.dispose()
})
</script>

<style scoped>
.chart {
  width: 100%;
  height: 340px;
}
</style>
