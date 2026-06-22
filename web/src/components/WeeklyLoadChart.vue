<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import type { WeeklyLoadRecord } from '../api/keep'

const props = defineProps<{
  rows: WeeklyLoadRecord[]
}>()

const { isDark } = useTheme()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function buildOption(): echarts.EChartsOption {
  const sorted = [...props.rows].sort(
    (a, b) => a.week_start.localeCompare(b.week_start),
  )
  const labels = sorted.map((r) => r.week_start.substring(0, 10))
  return {
    backgroundColor: 'transparent',
    title: { text: '周运动负荷 (Keep)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['训练负荷', '推荐区间'], top: 28 },
    grid: { top: 60, right: 30, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: labels },
    yAxis: {
      type: 'value',
      name: '负荷',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
    },
    series: [
      {
        name: '训练负荷',
        type: 'bar',
        data: sorted.map((r) => r.training_load),
        barWidth: '50%',
        itemStyle: { color: '#5470C6' },
      },
      {
        name: '推荐区间',
        type: 'line',
        data: sorted.map(() => null),
        lineStyle: { opacity: 0 },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(103,194,58,0.12)' },
          data: sorted.map((s) => [
            { yAxis: s.load_lower },
            { yAxis: s.load_upper },
          ]),
        },
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
