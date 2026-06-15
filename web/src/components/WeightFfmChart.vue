<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ReportRow } from '../api/dashboard'

const props = defineProps<{ rows: ReportRow[] }>()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function yDomain(series1: number[], series2: number[]) {
  const vals = [...series1, ...series2].filter((v) => v > 0)
  if (vals.length === 0) return { min: 0, max: 100 }
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const gap = Math.max(1.0, (max - min) * 0.2)
  return { floor: Math.floor(min - gap), ceil: Math.ceil(max + gap) }
}

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const weight = props.rows.map((r) => r.ma_weight_kg)
  const ffm = props.rows.map((r) => r.ma_ffm_kg)
  const domain = yDomain(weight, ffm)
  return {
    title: { text: '体重 & 去脂体重（7日均线）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['体重', '去脂体重'], top: 30 },
    grid: { top: 70, right: 70, bottom: 30, left: 70 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      {
        type: 'value',
        name: '体重 kg',
        min: domain.floor,
        max: domain.ceil,
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
        axisLine: { show: true, lineStyle: { color: '#5470C6' } },
      },
      {
        type: 'value',
        name: '去脂体重 kg',
        min: domain.floor,
        max: domain.ceil,
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
        axisLine: { show: true, lineStyle: { color: '#91CC75' } },
      },
    ],
    series: [
      {
        name: '体重',
        type: 'line',
        yAxisIndex: 0,
        data: weight,
        smooth: true,
        itemStyle: { color: '#5470C6' },
      },
      {
        name: '去脂体重',
        type: 'line',
        yAxisIndex: 1,
        data: ffm,
        smooth: true,
        itemStyle: { color: '#91CC75' },
      },
    ],
  }
}

onMounted(() => {
  chart = echarts.init(chartRef.value!, 'dark')
  chart.setOption(buildOption())
  window.addEventListener('resize', () => chart?.resize())
})

watch(() => props.rows, () => chart?.setOption(buildOption()), { deep: true })
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart {
  width: 100%;
  height: 380px;
}
</style>
