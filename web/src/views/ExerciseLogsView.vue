<template>
  <div>
    <div class="toolbar">
      <h2 class="page-title">运动记录</h2>
      <el-button type="primary" @click="openAdd">添加记录</el-button>
    </div>

    <el-table v-if="!isMobile" :data="logs" v-loading="loading" stripe>
      <el-table-column prop="log_time" label="时间" min-width="150" />
      <el-table-column prop="exercise_name" label="运动名称" min-width="120" />
      <el-table-column prop="duration_desc" label="时长" min-width="100" />
      <el-table-column prop="calories_kcal" label="消耗热量" width="100" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-else v-loading="loading" class="mobile-card-list">
      <el-empty v-if="!logs.length && !loading" description="暂无运动记录" :image-size="72" />
      <article v-for="row in logs" :key="row.id" class="mobile-card">
        <div class="mobile-card-head">
          <div class="mobile-card-title">{{ row.exercise_name }}</div>
          <el-tag size="small" effect="plain" type="success">{{ row.calories_kcal }} kcal</el-tag>
        </div>
        <div class="mobile-card-grid">
          <div class="mobile-card-field">
            <div class="mobile-card-label">时间</div>
            <div class="mobile-card-value">{{ formatTime(row.log_time) }}</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">时长</div>
            <div class="mobile-card-value">{{ row.duration_desc }}</div>
          </div>
        </div>
        <div v-if="row.note" class="mobile-card-note">{{ row.note }}</div>
        <div class="mobile-card-actions">
          <el-button size="small" type="primary" plain @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
        </div>
      </article>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑运动记录' : '添加运动记录'"
      width="480px"
    >
      <el-form
        :model="form"
        :label-width="isMobile ? 'auto' : '80px'"
        :label-position="isMobile ? 'top' : 'right'"
      >
        <el-form-item label="时间" required>
          <el-date-picker
            v-model="form.log_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择时间"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.exercise_name" placeholder="如：慢跑、游泳" />
        </el-form-item>
        <el-form-item label="时长" required>
          <el-input v-model="form.duration_desc" placeholder="如：30分钟、1小时" />
        </el-form-item>
        <el-form-item label="消耗热量" required>
          <el-input-number v-model="form.calories_kcal" :min="0" :precision="0" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchExerciseLogs,
  createExerciseLog,
  updateExerciseLog,
  deleteExerciseLog,
  type ExerciseLogResponse,
  type ExerciseLogCreate,
} from '../api/exercise'
import { useMobile } from '../composables/useMobile'

const isMobile = useMobile()
const logs = ref<ExerciseLogResponse[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

const form = ref<ExerciseLogCreate>({
  log_time: '',
  exercise_name: '',
  duration_desc: '',
  calories_kcal: 0,
  note: null,
})

function formatTime(value: string): string {
  return value.slice(0, 16).replace('T', ' ')
}

function resetForm() {
  form.value = {
    log_time: '',
    exercise_name: '',
    duration_desc: '',
    calories_kcal: 0,
    note: null,
  }
}

async function loadLogs() {
  loading.value = true
  try {
    logs.value = await fetchExerciseLogs(200)
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: ExerciseLogResponse) {
  editing.value = true
  editingId.value = row.id
  form.value = {
    log_time: row.log_time,
    exercise_name: row.exercise_name,
    duration_desc: row.duration_desc,
    calories_kcal: row.calories_kcal,
    note: row.note,
  }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editing.value && editingId.value != null) {
      await updateExerciseLog(editingId.value, form.value)
      ElMessage.success('已更新')
    } else {
      await createExerciseLog(form.value)
      ElMessage.success('已记录')
    }
    dialogVisible.value = false
    loadLogs()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ExerciseLogResponse) {
  try {
    await ElMessageBox.confirm(
      `确定要删除"${row.exercise_name}"的运动记录吗？`,
      '确认删除',
      { type: 'warning' },
    )
    await deleteExerciseLog(row.id)
    ElMessage.success('已删除')
    loadLogs()
  } catch {
    // cancelled
  }
}

onMounted(() => loadLogs())
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .toolbar {
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .page-title {
    font-size: 18px;
  }

  .toolbar .el-button {
    min-height: 40px;
  }
}
</style>
