<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import { useEChartsResize } from '../composables/useEChartsResize'
import type { WeeklyLoadRecord } from '../api/keep'

const props = defineProps<{
  rows: WeeklyLoadRecord[]
}>()

const { isDark } = useTheme()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.ECharts | null>(null)
useEChartsResize(chart)

function buildOption(): echarts.EChartsOption {
  const sorted = [...props.rows].sort(
    (a, b) => a.week_start.localeCompare(b.week_start),
  )
  const labels = sorted.map((r) => r.week_start.substring(0, 10))
  return {
    backgroundColor: 'transparent',
    title: { text: '周运动负荷 (Keep)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex ?? 0
        const r = sorted[idx]
        let html = `${params[0]?.axisValue}<br/>`
        html += `训练负荷: <b>${r.training_load ?? '-'}</b><br/>`
        html += `推荐负荷: <b>${r.load_lower}-${r.load_upper}</b>`
        return html
      },
    },
    legend: { data: ['训练负荷'], top: 28 },
    grid: { top: 60, right: 30, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: labels },
    yAxis: {
      type: 'value',
      name: '负荷',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
    },
    series: [
      {
        name: '训练负荷',
        type: 'line',
        data: sorted.map((r) => r.training_load),
        smooth: true,
        connectNulls: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { color: '#5470C6', width: 2 },
        itemStyle: { color: '#5470C6' },
      },
      {
        name: '推荐下界',
        type: 'line',
        data: sorted.map((r) => r.load_lower),
        stack: 'band',
        lineStyle: { opacity: 0 },
        symbol: 'none',
        silent: true,
        legendHoverLink: false,
      },
      {
        name: '推荐区间',
        type: 'line',
        data: sorted.map((r) => r.load_upper - r.load_lower),
        stack: 'band',
        lineStyle: { opacity: 0 },
        symbol: 'none',
        silent: true,
        areaStyle: { color: 'rgba(103,194,58,0.12)' },
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
