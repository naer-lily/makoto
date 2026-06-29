<template>
  <div class="chart-container">
    <el-button class="chart-copy-btn" size="small" text @click="handleCopy">
      <el-icon :size="14"><CopyDocument /></el-icon>
    </el-button>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { ReportRow } from '../api/dashboard'
import { useTheme } from '../composables/useTheme'
import { useEChartsResize } from '../composables/useEChartsResize'
import { useCopyChartMd } from '../composables/useCopyChartMd'

const { isDark } = useTheme()
const { copyChartMd } = useCopyChartMd()

const props = defineProps<{
  rows: ReportRow[]
  targetWeight: number | null
  targetDate: string | null
}>()

const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

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

  const series: any[] = [
    {
      name: '体重（7日均线）',
      type: 'line',
      data: weightData,
      smooth: true,
      lineStyle: { color: '#5470C6' },
      itemStyle: { color: '#5470C6' },
      areaStyle: { color: 'rgba(84,112,198,0.1)' },
    },
  ]

  if (props.targetWeight != null && props.targetDate) {
    const lastWeight = weightData[weightData.length - 1]
    const lastDateStr = dates[dates.length - 1]
    const targetDateShort = props.targetDate.substring(5)

    if (targetDateShort > lastDateStr) {
      const lastFull = new Date(props.rows[props.rows.length - 1].date)
      const targetFull = new Date(props.targetDate)
      const extraDates: string[] = []
      const cursor = new Date(lastFull.getTime() + 86400000)
      while (cursor <= targetFull) {
        const m = String(cursor.getMonth() + 1).padStart(2, '0')
        const d = String(cursor.getDate()).padStart(2, '0')
        extraDates.push(`${m}-${d}`)
        cursor.setDate(cursor.getDate() + 1)
      }
      const lastIdx = dates.length - 1
      dates.push(...extraDates)
      for (let i = 0; i < extraDates.length; i++) {
        weightData.push(null as any)
      }
      const proj = new Array<number | null>(dates.length).fill(null)
      proj[lastIdx] = lastWeight
      proj[dates.length - 1] = props.targetWeight
      series.push({
        name: '目标斜率',
        type: 'line',
        data: proj,
        lineStyle: { color: '#E6A23C', type: 'dashed', width: 2 },
        itemStyle: { color: '#E6A23C' },
        symbol: 'circle',
        symbolSize: 6,
        z: 10,
        legendHoverLink: false,
      })
    } else {
      const targetIdx = dates.findIndex((d) => d >= targetDateShort)
      if (targetIdx >= 0) {
        const proj = new Array<number | null>(dates.length).fill(null)
        proj[dates.length - 1] = lastWeight
        proj[targetIdx] = props.targetWeight
        series.push({
          name: '目标斜率',
          type: 'line',
          data: proj,
          lineStyle: { color: '#E6A23C', type: 'dashed', width: 2 },
          itemStyle: { color: '#E6A23C' },
          z: 10,
          legendHoverLink: false,
        })
      }
    }
  }

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    title: { text: '体重趋势（7日均线）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: series.map((s) => s.name), top: 28 },
    grid: { top: 60, right: 20, bottom: 30, left: 60 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: 'kg',
      min: domain.min,
      max: domain.max,
      axisLabel: { formatter: (v: number) => v.toFixed(1) },
    },
    series,
  }

  return option
}

function initChart() {
  if (!chartRef.value) return
  chart.value?.dispose()
  chart.value = echarts.init(chartRef.value!, isDark.value ? 'dark' : undefined)
  chart.value.setOption(buildOption())
}

function handleCopy() {
  const rows = props.rows.map((r) => [
    r.date.substring(5),
    String(r.ma_weight_kg),
    r.is_interpolated ? '插值' : '实测',
  ])
  const headers = ['日期', '体重 (kg) 7日均线', '来源']
  if (props.targetWeight != null) {
    headers.push('目标 (kg)')
    rows.forEach((r) => r.push(String(props.targetWeight)))
  }
  copyChartMd('体重趋势（7日均线）', headers, rows)
}

onMounted(() => {
  initChart()
})

watch(
  () => [props.rows, props.targetWeight, props.targetDate],
  () => chart.value?.setOption(buildOption()),
  { deep: true },
)

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
