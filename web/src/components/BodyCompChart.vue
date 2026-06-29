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

const props = defineProps<{ rows: ReportRow[] }>()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

function buildOption(): echarts.EChartsOption {
  const dates: string[] = []
  const fatDeltas: (number | null)[] = []
  const ffmDeltas: (number | null)[] = []

  for (let i = 0; i < props.rows.length; i++) {
    const row = props.rows[i]
    const prevRow = i >= 7 ? props.rows[i - 7] : null
    dates.push(row.date.substring(5))
    if (prevRow) {
      fatDeltas.push(parseFloat((row.ma_fat_kg - prevRow.ma_fat_kg).toFixed(2)))
      ffmDeltas.push(parseFloat((row.ma_ffm_kg - prevRow.ma_ffm_kg).toFixed(2)))
    } else {
      fatDeltas.push(null)
      ffmDeltas.push(null)
    }
  }

  const allValues = [...fatDeltas, ...ffmDeltas].filter((v): v is number => v !== null)
  const maxAbs = allValues.length ? Math.max(...allValues.map(Math.abs)) : 1.5
  const pad = Math.max(0.3, maxAbs * 0.2)
  const yMax = Math.ceil((maxAbs + pad) * 4) / 4
  const yMin = -yMax

  return {
    backgroundColor: 'transparent',
    title: {
      text: '体成分周变化 (kg) ← 7日均线滚差',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params : [params]
        let html = `${p[0]?.axisValue}<br/>`
        let total = 0
        for (const item of p) {
          if (item.value !== null && item.value !== undefined) {
            const sign = item.value >= 0 ? '+' : ''
            html += `${item.marker} ${item.seriesName}: ${sign}${item.value} kg<br/>`
            total += item.value
          }
        }
        const totalSign = total >= 0 ? '+' : ''
        html += `<b>合计: ${totalSign}${total.toFixed(2)} kg</b>`
        return html
      },
    },
    legend: {
      data: ['脂肪变化', '去脂体重变化'],
      top: 28,
    },
    grid: { top: 60, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kg',
      min: yMin,
      max: yMax,
      axisLabel: { formatter: (v: number) => v.toFixed(1) },
    },
    series: [
      {
        name: '脂肪变化',
        type: 'bar',
        stack: 'total',
        data: fatDeltas,
        barWidth: '60%',
        itemStyle: { color: '#F5A623' },
      },
      {
        name: '去脂体重变化',
        type: 'bar',
        stack: 'total',
        data: ffmDeltas,
        barWidth: '60%',
        itemStyle: { color: '#4A90D9' },
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
