<template>
  <div>
    <div class="toolbar">
      <h2 class="page-title">食物库</h2>
      <div class="toolbar-actions">
        <el-input
          v-model="searchQuery"
          class="food-search"
          placeholder="搜索食物..."
          clearable
          @input="onSearchInput"
        />
        <el-button type="primary" @click="openAdd">添加食物</el-button>
      </div>
    </div>

    <el-table v-if="!isMobile" :data="foods" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="calories_per_100g" label="热量/100g" width="100" />
      <el-table-column prop="protein_per_100g" label="蛋白/100g" width="100" />
      <el-table-column prop="carbs_per_100g" label="碳水/100g" width="100" />
      <el-table-column prop="fat_per_100g" label="脂肪/100g" width="100" />
      <el-table-column prop="fiber_per_100g" label="纤维/100g" width="100" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-else v-loading="loading" class="mobile-card-list">
      <el-empty v-if="!foods.length && !loading" description="暂无食物" :image-size="72" />
      <article v-for="food in foods" :key="food.id" class="mobile-card">
        <div class="mobile-card-head">
          <div class="mobile-card-title">{{ food.name }}</div>
          <el-tag size="small" effect="plain" type="warning">{{ food.calories_per_100g }} kcal</el-tag>
        </div>
        <div class="mobile-card-grid">
          <div class="mobile-card-field">
            <div class="mobile-card-label">蛋白质 / 100g</div>
            <div class="mobile-card-value">{{ food.protein_per_100g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">碳水 / 100g</div>
            <div class="mobile-card-value">{{ food.carbs_per_100g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">脂肪 / 100g</div>
            <div class="mobile-card-value">{{ food.fat_per_100g }} g</div>
          </div>
          <div class="mobile-card-field">
            <div class="mobile-card-label">纤维 / 100g</div>
            <div class="mobile-card-value">{{ food.fiber_per_100g }} g</div>
          </div>
        </div>
        <div v-if="food.note" class="mobile-card-note">{{ food.note }}</div>
        <div class="mobile-card-actions">
          <el-button size="small" type="primary" plain @click="openEdit(food)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="handleDelete(food)">删除</el-button>
        </div>
      </article>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingFood ? '编辑食物' : '添加食物'"
      width="520px"
    >
      <el-form
        :model="form"
        :label-width="isMobile ? 'auto' : '100px'"
        :label-position="isMobile ? 'top' : 'right'"
      >
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
        <el-form-item label="纤维/100g">
          <el-input-number v-model="form.fiber_per_100g" :min="0" :precision="1" />
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
import { useMobile } from '../composables/useMobile'

const isMobile = useMobile()
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
  fiber_per_100g: 0,
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
    fiber_per_100g: 0,
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
    fiber_per_100g: row.fiber_per_100g,
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
  gap: 12px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  white-space: nowrap;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.food-search {
  width: 240px;
}

@media (max-width: 767px) {
  .toolbar {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
  }

  .page-title {
    font-size: 18px;
  }

  .toolbar-actions {
    gap: 8px;
  }

  .food-search {
    flex: 1 1 auto;
    width: auto;
    min-width: 0;
  }

  .toolbar-actions .el-button {
    min-height: 40px;
    flex: 0 0 auto;
  }
}
</style>
