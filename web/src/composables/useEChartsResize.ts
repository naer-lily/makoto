import { onMounted, onUnmounted, type Ref } from 'vue'

type ChartLike = { resize: () => void; getDom?: () => HTMLElement | undefined } | null

export function useEChartsResize(chartRef: Ref<ChartLike>) {
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
