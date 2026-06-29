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
import type { CircumferenceRecord } from '../api/circumference'

const props = defineProps<{
  rows: CircumferenceRecord[]
}>()

const { isDark } = useTheme()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

function buildOption(): echarts.EChartsOption {
  const sorted = [...props.rows].sort(
    (a, b) => new Date(a.log_date).getTime() - new Date(b.log_date).getTime(),
  )
  const dates = sorted.map((r) => r.log_date.substring(5))

  return {
    backgroundColor: 'transparent',
    title: { text: '围度变化趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['腰围', '臂围', '大腿围'], top: 28 },
    grid: { top: 60, right: 30, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'cm',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
    },
    series: [
      {
        name: '腰围',
        type: 'line',
        data: sorted.map((r) => r.waist_cm),
        smooth: true,
        connectNulls: true,
        lineStyle: { color: '#EE6666' },
        itemStyle: { color: '#EE6666' },
        symbol: 'circle',
        symbolSize: 6,
      },
      {
        name: '臂围',
        type: 'line',
        data: sorted.map((r) => r.arm_cm),
        smooth: true,
        connectNulls: true,
        lineStyle: { color: '#5470C6' },
        itemStyle: { color: '#5470C6' },
        symbol: 'circle',
        symbolSize: 6,
      },
      {
        name: '大腿围',
        type: 'line',
        data: sorted.map((r) => r.thigh_cm),
        smooth: true,
        connectNulls: true,
        lineStyle: { color: '#91CC75' },
        itemStyle: { color: '#91CC75' },
        symbol: 'circle',
        symbolSize: 6,
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
