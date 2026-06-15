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

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const weight = props.rows.map((r) => r.ma_weight_kg)
  const ffm = props.rows.map((r) => r.ma_ffm_kg)
  const minW = Math.min(...weight)
  const maxW = Math.max(...weight)
  const wRange = maxW - minW || 10
  const minF = Math.min(...ffm)
  const maxF = Math.max(...ffm)
  const fRange = maxF - minF || 10
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
        min: minW - wRange * 0.2,
        max: maxW + wRange * 0.2,
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
        axisLine: { show: true, lineStyle: { color: '#5470C6' } },
      },
      {
        type: 'value',
        name: '去脂体重 kg',
        min: minF - fRange * 0.2,
        max: maxF + fRange * 0.2,
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
