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

function yDomain(data: number[]) {
  const vals = data.filter((v) => v > 0)
  if (vals.length === 0) return { min: 0, max: 100 }
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const gap = Math.max(1.0, (max - min) * 0.15)
  return { min: Math.floor(min - gap), max: Math.ceil(max + gap) }
}

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const data = props.rows.map((r) => r.weight_kg)
  const interp = props.rows.map((r) => r.is_interpolated)
  const realData = data.map((v, i) => (interp[i] ? null : v))
  const interpData = data.map((v, i) => (interp[i] ? v : null))
  const domain = yDomain(data)
  return {
    backgroundColor: 'transparent',
    title: {
      text: '原始体重（线性插值补全）',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: { trigger: 'axis' },
    grid: { top: 50, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kg',
      min: domain.min,
      max: domain.max,
      axisLabel: { formatter: (v: number) => v.toFixed(1) },
    },
    series: [
      {
        name: '插值',
        type: 'line',
        data: interpData,
        smooth: true,
        connectNulls: true,
        lineStyle: { color: '#aaa', type: 'dashed' },
        itemStyle: { color: '#aaa' },
      },
      {
        name: '实测',
        type: 'line',
        data: realData,
        connectNulls: false,
        lineStyle: { color: '#5470C6' },
        itemStyle: { color: '#5470C6' },
        symbol: 'circle',
        symbolSize: 6,
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
