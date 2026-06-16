<template>
  <div>
    <div class="toolbar">
      <h2 style="margin:0">食物库</h2>
      <div style="display:flex;gap:12px">
        <el-input
          v-model="searchQuery"
          placeholder="搜索食物..."
          clearable
          style="width:240px"
          @input="onSearchInput"
        />
        <el-button type="primary" @click="openAdd">添加食物</el-button>
      </div>
    </div>

    <el-table :data="foods" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="calories_per_100g" label="热量/100g" width="100" />
      <el-table-column prop="protein_per_100g" label="蛋白/100g" width="100" />
      <el-table-column prop="carbs_per_100g" label="碳水/100g" width="100" />
      <el-table-column prop="fat_per_100g" label="脂肪/100g" width="100" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editingFood ? '编辑食物' : '添加食物'"
      width="520px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="热量/100g">
          <el-input-number v-model="form.calories_per_100g" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="蛋白/100g">
          <el-input-number v-model="form.protein_per_100g" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="碳水/100g">
          <el-input-number v-model="form.carbs_per_100g" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="脂肪/100g">
          <el-input-number v-model="form.fat_per_100g" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="搜索关键词">
          <el-input v-model="keywordsStr" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="2" />
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
  fetchFoods,
  createFood,
  updateFood,
  deleteFood,
  searchFoods,
  type FoodResponse,
  type FoodCreate,
} from '../api/foods'

const foods = ref<FoodResponse[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingFood = ref<FoodResponse | null>(null)
const searchQuery = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null

const form = ref<FoodCreate>({
  name: '',
  calories_per_100g: 0,
  protein_per_100g: 0,
  carbs_per_100g: 0,
  fat_per_100g: 0,
  search_keywords: [],
  note: null,
})

const keywordsStr = ref('')

function resetForm() {
  form.value = {
    name: '',
    calories_per_100g: 0,
    protein_per_100g: 0,
    carbs_per_100g: 0,
    fat_per_100g: 0,
    search_keywords: [],
    note: null,
  }
  keywordsStr.value = ''
}

async function loadFoods() {
  loading.value = true
  try {
    foods.value = await fetchFoods()
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!searchQuery.value.trim()) {
      loadFoods()
      return
    }
    loading.value = true
    try {
      const results = await searchFoods(searchQuery.value, 50)
      const allFoods = await fetchFoods()
      const idSet = new Set(results.map((r) => r.id))
      foods.value = allFoods.filter((f) => idSet.has(f.id))
    } finally {
      loading.value = false
    }
  }, 300)
}

function openAdd() {
  editingFood.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: FoodResponse) {
  editingFood.value = row
  form.value = {
    name: row.name,
    calories_per_100g: row.calories_per_100g,
    protein_per_100g: row.protein_per_100g,
    carbs_per_100g: row.carbs_per_100g,
    fat_per_100g: row.fat_per_100g,
    search_keywords: [...row.search_keywords],
    note: row.note,
  }
  keywordsStr.value = row.search_keywords.join(',')
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const keywords = keywordsStr.value
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s)
    const data = { ...form.value, search_keywords: keywords }
    if (editingFood.value) {
      await updateFood(editingFood.value.id, data)
      ElMessage.success('已更新')
    } else {
      await createFood(data)
      ElMessage.success('已添加')
    }
    dialogVisible.value = false
    loadFoods()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: FoodResponse) {
  try {
    await ElMessageBox.confirm(`确定要删除"${row.name}"吗？`, '确认删除', {
      type: 'warning',
    })
    await deleteFood(row.id)
    ElMessage.success('已删除')
    loadFoods()
  } catch {
    // cancelled
  }
}

onMounted(() => loadFoods())
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
