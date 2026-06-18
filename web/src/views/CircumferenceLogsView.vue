<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">围度记录</h2>
      <el-button type="primary" @click="openAdd">添加记录</el-button>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
      <el-table-column prop="log_date" label="日期" width="120" />
      <el-table-column label="腰围" width="100" align="right">
        <template #default="{ row }">
          {{ row.waist_cm != null ? row.waist_cm.toFixed(1) + ' cm' : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="臂围" width="100" align="right">
        <template #default="{ row }">
          {{ row.arm_cm != null ? row.arm_cm.toFixed(1) + ' cm' : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="大腿围" width="100" align="right">
        <template #default="{ row }">
          {{ row.thigh_cm != null ? row.thigh_cm.toFixed(1) + ' cm' : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="150" />
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      title="添加围度记录"
      width="400px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="form.log_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="腰围">
          <el-input-number v-model="form.waist_cm" :min="0" :precision="1" placeholder="cm" />
        </el-form-item>
        <el-form-item label="臂围">
          <el-input-number v-model="form.arm_cm" :min="0" :precision="1" placeholder="cm" />
        </el-form-item>
        <el-form-item label="大腿围">
          <el-input-number v-model="form.thigh_cm" :min="0" :precision="1" placeholder="cm" />
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
  fetchCircumferenceLogs,
  createCircumferenceLog,
  deleteCircumferenceLog,
  type CircumferenceRecord,
  type CircumferenceCreate,
} from '../api/circumference'

const logs = ref<CircumferenceRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)

const form = ref<CircumferenceCreate>({
  log_date: '',
  waist_cm: null,
  arm_cm: null,
  thigh_cm: null,
  note: null,
})

function resetForm() {
  form.value = {
    log_date: '',
    waist_cm: null,
    arm_cm: null,
    thigh_cm: null,
    note: null,
  }
}

async function loadLogs() {
  loading.value = true
  try {
    logs.value = await fetchCircumferenceLogs()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  resetForm()
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.log_date) {
    ElMessage.warning('请选择日期')
    return
  }
  saving.value = true
  try {
    await createCircumferenceLog(form.value)
    ElMessage.success('已记录')
    dialogVisible.value = false
    loadLogs()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: CircumferenceRecord) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.log_date} 的围度记录吗？`,
      '确认删除',
      { type: 'warning' },
    )
    await deleteCircumferenceLog(row.id)
    ElMessage.success('已删除')
    loadLogs()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
