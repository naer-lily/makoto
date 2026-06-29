import { onMounted, onUnmounted, watch, type Ref } from 'vue'

type ChartLike = { resize: () => void; getDom?: () => HTMLElement | undefined } | null

export function useEChartsResize(chartRef: Ref<ChartLike>) {
  let observer: ResizeObserver | null = null

  function handleResize() {
    chartRef.value?.resize()
  }

  function tearDown() {
    observer?.disconnect()
    observer = null
  }

  function setUp() {
    tearDown()
    const dom = chartRef.value?.getDom?.()
    if (dom) {
      observer = new ResizeObserver(() => handleResize())
      observer.observe(dom)
    }
  }

  onMounted(() => {
    window.addEventListener('resize', handleResize)
  })

  watch(chartRef, () => setUp())

  onUnmounted(() => {
    tearDown()
    window.removeEventListener('resize', handleResize)
  })
}
