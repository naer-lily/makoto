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

function yDomain(data: number[]) {
  const vals = data.filter((v) => v > 0)
  if (vals.length === 0) return { min: 0, max: 30 }
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const gap = Math.max(1.0, (max - min) * 0.2)
  return { min: Math.floor(min - gap), max: Math.ceil(max + gap) }
}

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(5))
  const data = props.rows.map((r) => r.ma_body_fat_pct)
  const domain = yDomain(data)
  return {
    backgroundColor: 'transparent',
    title: { text: '体脂率变化趋势（7日均线）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { top: 50, right: 20, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      name: '%',
      min: domain.min,
      max: domain.max,
      axisLabel: { formatter: (v: number) => v.toFixed(1) },
    },
    series: [
      {
        name: '体脂率',
        type: 'line',
        data,
        smooth: true,
        lineStyle: { color: '#91CC75' },
        itemStyle: { color: '#91CC75' },
        areaStyle: { color: 'rgba(145,204,117,0.1)' },
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
    String(r.ma_body_fat_pct),
  ])
  copyChartMd('体脂率变化趋势（7日均线）', ['日期', '体脂率 (%)'], rows)
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
