import { ElMessage } from 'element-plus'

export function useCopyChartMd() {
  function copyChartMd(title: string, headers: string[], rows: string[][]) {
    let md = `**${title}**\n\n`
    md += '| ' + headers.join(' | ') + ' |\n'
    md += '|' + headers.map(() => '------').join('|') + '|\n'
    for (const row of rows) {
      md += '| ' + row.join(' | ') + ' |\n'
    }
    navigator.clipboard.writeText(md)
    ElMessage.success('已复制为 Markdown')
  }

  return { copyChartMd }
}
