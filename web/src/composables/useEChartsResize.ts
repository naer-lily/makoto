import { onMounted, onUnmounted, type Ref } from 'vue'
import type { ECharts } from 'echarts'

export function useEChartsResize(chartRef: Ref<ECharts | null>) {
  let observer: ResizeObserver | null = null

  function handleResize() {
    chartRef.value?.resize()
  }

  onMounted(() => {
    const dom = chartRef.value?.getDom?.()
    if (dom) {
      observer = new ResizeObserver(() => handleResize())
      observer.observe(dom)
    }
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    observer?.disconnect()
    window.removeEventListener('resize', handleResize)
  })
}
