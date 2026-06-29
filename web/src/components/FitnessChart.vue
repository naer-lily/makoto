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
import type { FitnessRecord } from '../api/keep'

const props = defineProps<{
  rows: FitnessRecord[]
}>()

const { isDark } = useTheme()
const chartRef = ref<HTMLDivElement>()
const chart = ref<echarts.ECharts | null>(null)
useEChartsResize(chart)

function buildOption(): echarts.EChartsOption {
  const dates = props.rows.map((r) => r.date.substring(4))
  const acwrData = props.rows.map((r) =>
    r.ctl > 0 ? +(r.atl / r.ctl).toFixed(2) : null,
  )

  return {
    backgroundColor: 'transparent',
    title: { text: '体能水平 (Keep)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let html = `${params[0]?.axisValue}<br/>`
        for (const p of params) {
          if (p.seriesName === 'ACWR') {
            const v = p.value
            let zone = ''
            if (v == null) zone = ''
            else if (v < 0.8) zone = ' 负荷过低'
            else if (v < 1.3) zone = ' 安全区'
            else if (v < 1.5) zone = ' 风险监控'
            else zone = ' 危险区'
            html += `${p.marker} ACWR: <b>${v ?? '-'}</b>${zone}<br/>`
          } else {
            html += `${p.marker} ${p.seriesName}: <b>${p.value}</b><br/>`
          }
        }
        return html
      },
    },
    legend: {
      data: ['ATL 疲劳度', 'CTL 体能', 'TSB 趋势', 'ACWR'],
      top: 28,
      selected: { 'TSB 趋势': false },
    },
    grid: { top: 60, right: 60, bottom: 55, left: 55 },
    xAxis: { type: 'category', data: dates },
    yAxis: [
      {
        type: 'value',
        name: 'ATL / CTL',
        axisLabel: { formatter: (v: number) => v.toFixed(0) },
      },
      {
        type: 'value',
        name: 'TSB / ACWR',
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
      },
    ],
    visualMap: {
      type: 'piecewise',
      seriesIndex: 3,
      pieces: [
        { lt: 0.8, color: '#909399', label: '负荷过低' },
        { gte: 0.8, lt: 1.3, color: '#67C23A', label: '安全区 0.8-1.3' },
        { gte: 1.3, lt: 1.5, color: '#E6A23C', label: '风险监控 1.3-1.5' },
        { gte: 1.5, color: '#F56C6C', label: '危险区 >1.5' },
      ],
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      itemWidth: 14,
      itemHeight: 10,
      textStyle: { fontSize: 10 },
    },
    series: [
      {
        name: 'ATL 疲劳度',
        type: 'line',
        yAxisIndex: 0,
        data: props.rows.map((r) => r.atl),
        smooth: true,
        lineStyle: { color: '#F56C6C' },
        itemStyle: { color: '#F56C6C' },
      },
      {
        name: 'CTL 体能',
        type: 'line',
        yAxisIndex: 0,
        data: props.rows.map((r) => r.ctl),
        smooth: true,
        lineStyle: { color: '#5470C6' },
        itemStyle: { color: '#5470C6' },
      },
      {
        name: 'TSB 趋势',
        type: 'line',
        yAxisIndex: 1,
        data: props.rows.map((r) => r.tsb),
        smooth: true,
        lineStyle: { color: '#91CC75' },
        itemStyle: { color: '#91CC75' },
        areaStyle: { color: 'rgba(145,204,117,0.08)' },
      },
      {
        name: 'ACWR',
        type: 'line',
        yAxisIndex: 1,
        data: acwrData,
        smooth: true,
        connectNulls: true,
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4,
      },
    ],
  }
}

function initChart() {
  if (!chartRef.value) return
  chart.value?.dispose()
  chart.value = echarts.init(chartRef.value!, isDark.value ? 'dark' : undefined)
  chart.value.setOption(buildOption())
  chart.value.on('legendselectchanged', (params: any) => {
    const s = params.selected
    if (params.name === 'TSB 趋势' && s['TSB 趋势']) {
      chart.value?.setOption({ legend: { selected: { ACWR: false } } })
    } else if (params.name === 'ACWR' && s['ACWR']) {
      chart.value?.setOption({ legend: { selected: { 'TSB 趋势': false } } })
    }
  })
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
  height: 380px;
}
</style>
