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

const props = defineProps<{ rows: ReportRow[] }>()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.EChartsType | null>(null)
useEChartsResize(chart)

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
    backgroundColor: 'transparent',
    title: { text: '体重 & 去脂体重（7日均线）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['体重', '去脂体重'], top: 30 },
    grid: { top: 70, right: 70, bottom: 30, left: 70 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      {
        type: 'value',
        name: 'kg',
        min: domain.floor,
        max: domain.ceil,
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
        axisLine: { show: true, lineStyle: { color: '#5470C6' } },
      },
      {
        type: 'value',
        name: 'kg',
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
    String(r.ma_ffm_kg),
    String(r.fat_kg),
  ])
  copyChartMd('体重 & 去脂体重（7日均线）', ['日期', '体重 (kg)', '去脂体重 (kg)', '脂肪 (kg)'], rows)
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
