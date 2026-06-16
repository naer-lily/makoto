<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ReportRow } from '../api/dashboard'

const props = defineProps<{
  rows: ReportRow[]
  targetWeight: number | null
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function yDomain(data: number[]) {
  const vals = data.filter((v) => v > 0)
  if (vals.length === 0) return { min: 0, max: 100 }
  if (props.targetWeight != null) vals.push(props.targetWeight)
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const gap = Math.max(1.0, (max - min) * 0.15)
  return { min: Math.floor(min - gap), max: Math.ceil(max + gap) }
}

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const weightData = props.rows.map((r) => r.ma_weight_kg)
  const domain = yDomain(weightData)

  const option: echarts.EChartsOption = {
    title: { text: '体重趋势（7日均线）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['体重（7日均线）'], top: 28 },
    grid: { top: 60, right: 40, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: '体重 kg',
      min: domain.min,
      max: domain.max,
      axisLabel: { formatter: (v: number) => v.toFixed(1) },
    },
    series: [
      {
        name: '体重（7日均线）',
        type: 'line',
        data: weightData,
        smooth: true,
        lineStyle: { color: '#5470C6' },
        itemStyle: { color: '#5470C6' },
        areaStyle: { color: 'rgba(84,112,198,0.1)' },
      },
    ],
  }

  if (props.targetWeight != null) {
    ;(option.series as any[]).push({
      name: '目标体重',
      type: 'line',
      markLine: {
        silent: true,
        data: [
          {
            yAxis: props.targetWeight,
            label: { formatter: `目标 ${props.targetWeight}kg` },
          },
        ],
        lineStyle: { color: '#F56C6C', type: 'dashed' },
      },
    })
  }
  return option
}

onMounted(() => {
  chart = echarts.init(chartRef.value!, 'dark')
  chart.setOption(buildOption())
  window.addEventListener('resize', () => chart?.resize())
})

watch(
  () => [props.rows, props.targetWeight],
  () => chart?.setOption(buildOption()),
  { deep: true },
)

onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart {
  width: 100%;
  height: 360px;
}
</style>
