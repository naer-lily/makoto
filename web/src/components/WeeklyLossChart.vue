<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ReportRow } from '../api/dashboard'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

const props = defineProps<{ rows: ReportRow[] }>()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const data = props.rows.map((r) => r.weekly_loss_kg ?? null)
  return {
    backgroundColor: 'transparent',
    title: {
      text: '周平均减重（kg），正数为减重',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: { trigger: 'axis' },
    grid: { top: 50, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kg',
      min: -1,
      max: 1.5,
    },
    series: [
      {
        name: '周减重',
        type: 'line',
        data,
        smooth: true,
        itemStyle: { color: '#EE6666' },
        lineStyle: { color: '#EE6666' },
        connectNulls: false,
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(103,194,58,0.08)' },
          data: [[{ yAxis: 0.5 }, { yAxis: 1.0 }]],
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
  height: 360px;
}
</style>
