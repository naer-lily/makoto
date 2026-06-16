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
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const deficitData = props.rows.map((r) => r.deficit_kcal)

  const option: echarts.EChartsOption = {
    title: { text: '每日热量缺口', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        const v = p.value
        const label = v > 0 ? `缺口 +${v} kcal` : v < 0 ? `盈余 ${v} kcal` : '平衡'
        return `${p.axisValue}<br/>${label}`
      },
    },
    legend: {
      data: ['热量缺口', '建议缺口 500-800'],
      top: 28,
    },
    grid: { top: 60, right: 40, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kcal',
      axisLabel: { formatter: (v: number) => v.toFixed(0) },
    },
    series: [
      {
        name: '热量缺口',
        type: 'bar',
        data: deficitData,
        barWidth: '60%',
        itemStyle: {
          color: (params: any) => (params.value > 0 ? '#67C23A' : '#F56C6C'),
        },
        markArea: {
          silent: true,
          data: [
            [
              { yAxis: 500, itemStyle: { color: 'rgba(103,194,58,0.1)' } },
              { yAxis: 800 },
            ],
          ],
          label: { show: true, position: 'insideTop', formatter: '建议缺口\n500-800' },
        },
      },
      {
        name: '建议缺口 500-800',
        type: 'bar',
        data: [],
        itemStyle: { color: 'rgba(103,194,58,0.1)' },
        barGap: '-100%',
      },
    ],
  }

  return option
}

onMounted(() => {
  chart = echarts.init(chartRef.value!, 'dark')
  chart.setOption(buildOption())
  window.addEventListener('resize', () => chart?.resize())
})

watch(
  () => props.rows,
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
