<template>
  <div>
    <div class="toolbar">
      <h2 class="page-title">饮食记录</h2>
      <el-button type="primary" @click="openAdd">添加记录</el-button>
    </div>

    <el-table v-if="!isMobile" :data="logs" v-loading="loading" stripe>
      <el-table-column prop="log_time" label="时间" min-width="150" />
      <el-table-column prop="food_name" label="食物" min-width="120" />
      <el-table-column prop="grams" label="克数" width="80" />
      <el-table-column prop="calories_kcal" label="热量" width="80" />
      <el-table-column prop="protein_g" label="蛋白" width="70" />
      <el-table-column prop="carbs_g" label="碳水" width="70" />
      <el-table-column prop="fat_g" label="脂肪" width="70" />
      <el-table-column prop="fiber_g" label="纤维" width="70" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-else v-loading="loading" class="mobile-card-list">
      <el-empty v-if="!logs.length && !loading" description="暂无饮食记录" :image-size="72" />
      <article v-for="row in logs" :key="row.id" class="mobile-card">
        <div class="mobile-card-head">
          <div class="mobile-card-title">{{ row.food_name }}</div>
          <el-tag size="small" effect="plain" type="warning">{{ row.calories_kcal }} kcal</el-tag>
        </div>
        <div class="mobile-card-grid">
          <div class="mobile-card-field">
            <div class="mobile-card-label">时间</div>
            <div class="mobile-card-value">{{ formatTime(row.log_time) }}</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">克数</div>
            <div class="mobile-card-value">{{ row.grams }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">蛋白质</div>
            <div class="mobile-card-value">{{ row.protein_g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">碳水</div>
            <div class="mobile-card-value">{{ row.carbs_g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">脂肪</div>
            <div class="mobile-card-value">{{ row.fat_g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">纤维</div>
            <div class="mobile-card-value">{{ row.fiber_g }} g</div>
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
      :title="editing ? '编辑饮食记录' : '添加饮食记录'"
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
        <el-form-item label="食物" required>
          <el-select v-model="form.food_id" filterable placeholder="选择食物" style="width:100%">
            <el-option
              v-for="food in foodOptions"
              :key="food.id"
              :label="food.name"
              :value="food.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="克数" required>
          <el-input-number v-model="form.grams" :min="0" :precision="1" />
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
  fetchDietLogs,
  createDietLog,
  updateDietLog,
  deleteDietLog,
  type DietLogResponse,
  type DietLogCreate,
} from '../api/diet'
import { fetchFoods, type FoodResponse } from '../api/foods'
import { useMobile } from '../composables/useMobile'

const isMobile = useMobile()
const logs = ref<DietLogResponse[]>([])
const foodOptions = ref<FoodResponse[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)

interface DietForm {
  log_time: string
  food_id: number | null
  grams: number
  note: string | null
}

const form = ref<DietForm>({
  log_time: '',
  food_id: null,
  grams: 0,
  note: null,
})

function formatTime(value: string): string {
  return value.slice(0, 16).replace('T', ' ')
}

function resetForm() {
  form.value = {
    log_time: '',
    food_id: null,
    grams: 0,
    note: null,
  }
}

async function loadLogs() {
  loading.value = true
  try {
    logs.value = await fetchDietLogs(200)
  } finally {
    loading.value = false
  }
}

async function loadFoods() {
  foodOptions.value = await fetchFoods()
}

function openAdd() {
  editing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: DietLogResponse) {
  editing.value = true
  editingId.value = row.id
  form.value = {
    log_time: row.log_time,
    food_id: row.food_id,
    grams: row.grams,
    note: row.note,
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (form.value.food_id == null) {
    ElMessage.error('请选择食物')
    return
  }
  saving.value = true
  const payload: DietLogCreate = {
    log_time: form.value.log_time,
    food_id: form.value.food_id,
    grams: form.value.grams,
    note: form.value.note,
  }
  try {
    if (editing.value && editingId.value != null) {
      await updateDietLog(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createDietLog(payload)
      ElMessage.success('已记录')
    }
    dialogVisible.value = false
    loadLogs()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: DietLogResponse) {
  try {
    await ElMessageBox.confirm(
      `确定要删除"${row.food_name} ${row.grams}g"的饮食记录吗？`,
      '确认删除',
      { type: 'warning' },
    )
    await deleteDietLog(row.id)
    ElMessage.success('已删除')
    loadLogs()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  loadLogs()
  loadFoods()
})
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
