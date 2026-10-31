import { readonly, ref } from 'vue'

const mediaQuery = window.matchMedia('(max-width: 767px)')
const isMobile = ref(mediaQuery.matches)

mediaQuery.addEventListener('change', (event) => {
  isMobile.value = event.matches
})

/** Shared mobile breakpoint (< 768px) for navigation and table/card swaps. */
export function useMobile() {
  return readonly(isMobile)
}
