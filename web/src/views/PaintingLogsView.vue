<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">绘画记录</h2>
      <el-button type="primary" @click="openAdd">添加会话</el-button>
    </div>

    <div class="heatmap-container">
      <div ref="heatmapRef" class="heatmap-chart" style="height: 200px"></div>
    </div>

    <el-table :data="logs" v-loading="loading" stripe style="margin-top: 16px">
      <el-table-column prop="log_time" label="绘画时间" min-width="150" />
      <el-table-column prop="file_id" label="文件 ID" min-width="180" />
      <el-table-column prop="duration_seconds" label="时长" width="120" align="right">
        <template #default="{ row }">
          {{ formatDuration(row.duration_seconds) }}
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="160">
        <template #default="{ row }">{{ row.note || '' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑绘画会话' : '添加绘画会话'"
      width="520px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="时间" required>
          <el-date-picker
            v-model="form.log_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择时间"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="文件路径" required>
          <el-input v-model="form.file_path" placeholder="如 D:/ART/xxx.kra" />
        </el-form-item>
        <el-form-item label="文件 ID" required>
          <el-input v-model="form.file_id" placeholder="如 37799f1b-dfd2-8420-8e7b-57590510433f" />
        </el-form-item>
        <el-form-item label="时长(秒)" required>
          <el-input-number v-model="form.duration_seconds" :min="0" :precision="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  fetchPaintingLogs,
  createPaintingLog,
  updatePaintingLog,
  deletePaintingLog,
  type PaintingLogResponse,
  type PaintingLogCreate,
} from '../api/painting'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

const logs = ref<PaintingLogResponse[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const heatmapRef = ref<HTMLDivElement>()
let chart: echarts.EChartsType | null = null

const form = ref<PaintingLogCreate>({
  log_time: '',
  file_path: '',
  file_id: '',
  duration_seconds: 0,
  note: null,
})

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m} 分 ${s} 秒`
  }
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h} 小时 ${m} 分`
}

function resetForm() {
  form.value = {
    log_time: '',
    file_path: '',
    file_id: '',
    duration_seconds: 0,
    note: null,
  }
}

async function loadLogs() {
  loading.value = true
  try {
    logs.value = await fetchPaintingLogs(2000)
    await nextTick()
    renderHeatmap()
  } finally {
    loading.value = false
  }
}

function aggregateByDate(): [string, number][] {
  const map = new Map<string, number>()
  logs.value.forEach((log) => {
    const date = log.log_time.substring(0, 10)
    map.set(date, (map.get(date) || 0) + log.duration_seconds)
  })
  return Array.from(map.entries()).map(([date, secs]) => [date, Math.round(secs / 60)])
}

function renderHeatmap() {
  chart?.dispose()
  if (!heatmapRef.value) return
  chart = echarts.init(heatmapRef.value, isDark.value ? 'dark' : undefined)

  const data = aggregateByDate()
  if (data.length === 0) {
    chart.setOption({
      title: { text: '暂无绘画记录', left: 'center', top: 'center', textStyle: { fontSize: 14 } },
    })
    return
  }

  const dates = data.map((d) => d[0]).sort()
  const maxVal = Math.max(...data.map((d) => d[1]), 1)

  chart.setOption({
    tooltip: {
      formatter: (params: any) => {
        const d = params.value[0]
        const v = params.value[1]
        return `${d}<br/>绘画 ${v} 分钟`
      },
    },
    visualMap: {
      min: 0,
      max: maxVal,
      type: 'piecewise',
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      pieces: [
        { min: 0, max: 0, label: '0', color: '#ebedf0' },
        { min: 1, max: Math.max(30, Math.ceil(maxVal * 0.15)), label: '低', color: '#9be9a8' },
        { min: Math.max(30, Math.ceil(maxVal * 0.15)) + 1, max: Math.max(60, Math.ceil(maxVal * 0.35)), label: '中', color: '#40c463' },
        { min: Math.max(60, Math.ceil(maxVal * 0.35)) + 1, max: Math.max(120, Math.ceil(maxVal * 0.6)), label: '高', color: '#30a14e' },
        { min: Math.max(120, Math.ceil(maxVal * 0.6)) + 1, label: '很高', color: '#216e39' },
      ],
    },
    calendar: {
      top: 20,
      left: 40,
      right: 20,
      bottom: 60,
      range: [dates[0], dates[dates.length - 1]],
      cellSize: ['auto', 14],
      yearLabel: { show: true, fontSize: 12 },
      monthLabel: { show: true, nameMap: 'ZH', fontSize: 11 },
      dayLabel: { show: true, nameMap: 'ZH', firstDay: 1, fontSize: 10 },
      splitLine: { lineStyle: { color: isDark.value ? '#333' : '#e0e0e0' } },
      itemStyle: {
        color: isDark.value ? '#1a1a2e' : '#fff',
        borderColor: isDark.value ? '#333' : '#e0e0e0',
        borderWidth: 2,
        borderRadius: 3,
      },
    },
    series: {
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: data,
    },
  })
}

function openAdd() {
  editing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: PaintingLogResponse) {
  editing.value = true
  editingId.value = row.id
  form.value = {
    log_time: row.log_time,
    file_path: row.file_path,
    file_id: row.file_id,
    duration_seconds: row.duration_seconds,
    note: row.note,
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editing.value && editingId.value != null) {
      await updatePaintingLog(editingId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await createPaintingLog(form.value)
      ElMessage.success('已记录')
    }
    dialogVisible.value = false
    await loadLogs()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: PaintingLogResponse) {
  try {
    await ElMessageBox.confirm(
      `确定要删除"${row.file_id}"的绘画会话吗？`,
      '确认删除',
      { type: 'warning' },
    )
    await deletePaintingLog(row.id)
    ElMessage.success('已删除')
    await loadLogs()
  } catch {
    // cancelled
  }
}

watch(isDark, () => {
  renderHeatmap()
})

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  loadLogs()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.heatmap-container {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 8px;
}
</style>
