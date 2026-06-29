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
import { useEChartsResize } from '../composables/useEChartsResize'

const { isDark } = useTheme()

const props = defineProps<{
  rows: ReportRow[]
}>()

const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const deficitData = props.rows.map((r) => r.deficit_kcal)
  const alpertData = props.rows.map((r) => r.alpert_limit_kcal)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    title: { text: '每日热量缺口', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params]
        const lines: string[] = [items[0]?.axisValue || '']
        for (const p of items) {
          if (p.seriesName === 'Alpert 安全上限') {
            lines.push(`安全上限 <span style="color:#F56C6C">${p.value} kcal</span>`)
          } else if (p.seriesName === '热量缺口') {
            const v = p.value
            const label = v > 0 ? `缺口 +${v} kcal` : v < 0 ? `盈余 ${v} kcal` : '平衡'
            lines.push(label)
          }
        }
        return lines.join('<br/>')
      },
    },
    legend: {
      data: ['热量缺口', '建议缺口 500-800', 'Alpert 安全上限'],
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
      {
        name: 'Alpert 安全上限',
        type: 'line',
        data: alpertData,
        symbol: 'none',
        smooth: true,
        lineStyle: { color: '#F56C6C', type: 'dashed', width: 2 },
        itemStyle: { color: '#F56C6C' },
        z: 10,
      },
    ],
  }

  return option
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
