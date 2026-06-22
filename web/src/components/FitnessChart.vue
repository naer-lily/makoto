<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import type { FitnessRecord } from '../api/keep'

const props = defineProps<{
  rows: FitnessRecord[]
}>()

const { isDark } = useTheme()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(4))
  return {
    backgroundColor: 'transparent',
    title: { text: '体能水平 (Keep)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['ATL 疲劳度', 'CTL 体能', 'TSB 趋势'], top: 28 },
    grid: { top: 60, right: 60, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      {
        type: 'value',
        name: 'ATL / CTL',
        axisLabel: { formatter: (v: number) => v.toFixed(0) },
      },
      {
        type: 'value',
        name: 'TSB',
        axisLabel: { formatter: (v: number) => v.toFixed(0) },
      },
    ],
    series: [
      {
        name: 'ATL 疲劳度',
        type: 'line',
        yAxisIndex: 0,
        data: props.rows.map((r) => r.atl),
        smooth: true,
        lineStyle: { color: '#F56C6C' },
        itemStyle: { color: '#F56C6C' },
      },
      {
        name: 'CTL 体能',
        type: 'line',
        yAxisIndex: 0,
        data: props.rows.map((r) => r.ctl),
        smooth: true,
        lineStyle: { color: '#5470C6' },
        itemStyle: { color: '#5470C6' },
      },
      {
        name: 'TSB 趋势',
        type: 'line',
        yAxisIndex: 1,
        data: props.rows.map((r) => r.tsb),
        smooth: true,
        lineStyle: { color: '#91CC75' },
        itemStyle: { color: '#91CC75' },
        areaStyle: { color: 'rgba(145,204,117,0.08)' },
      },
    ],
  }
}

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value!, isDark.value ? 'dark' : undefined)
  chart.setOption(buildOption())
}

function onResize() {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', onResize)
})

watch(() => props.rows, () => chart?.setOption(buildOption()), { deep: true })
watch(isDark, () => initChart())

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.chart {
  width: 100%;
  height: 380px;
}
</style>
