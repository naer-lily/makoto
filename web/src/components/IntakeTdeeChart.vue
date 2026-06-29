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

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const intake = props.rows.map((r) => r.intake_kcal)
  const tdee = props.rows.map((r) => r.tdee_kcal)

  return {
    backgroundColor: 'transparent',
    title: { text: '每日摄入 vs TDEE', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params]
        let html = `${items[0]?.axisValue}<br/>`
        let deficit = 0
        for (const p of items) {
          html += `${p.marker} ${p.seriesName}: <b>${p.value} kcal</b><br/>`
          if (p.seriesName === 'TDEE') deficit += p.value
          if (p.seriesName === '摄入') deficit -= p.value
        }
        const label = deficit > 0 ? `缺口 +${deficit} kcal` : deficit < 0 ? `盈余 ${deficit} kcal` : '平衡'
        html += `<b>${label}</b>`
        return html
      },
    },
    legend: { data: ['TDEE', '摄入'], top: 28 },
    grid: { top: 60, right: 20, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kcal',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
    },
    series: [
      {
        name: 'TDEE',
        type: 'line',
        data: tdee,
        smooth: true,
        lineStyle: { color: '#F56C6C', width: 2 },
        itemStyle: { color: '#F56C6C' },
        areaStyle: { color: 'rgba(103,194,58,0.06)' },
      },
      {
        name: '摄入',
        type: 'line',
        data: intake,
        smooth: true,
        lineStyle: { color: '#5470C6', width: 2 },
        itemStyle: { color: '#5470C6' },
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
    String(r.tdee_kcal),
    String(r.intake_kcal),
    String(r.deficit_kcal),
  ])
  copyChartMd('每日摄入 vs TDEE', ['日期', 'TDEE (kcal)', '摄入 (kcal)', '缺口 (kcal)'], rows)
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
