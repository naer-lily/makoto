<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">运动记录</h2>
      <el-button type="primary" @click="openAdd">添加记录</el-button>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑运动记录' : '添加运动记录'"
      width="480px"
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
  margin-bottom: 20px;
}
</style>
