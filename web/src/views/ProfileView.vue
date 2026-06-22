<template>
  <div>
    <h2 style="margin-bottom:20px">个人画像</h2>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="120px" style="max-width:600px">
        <el-form-item label="昵称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别" required>
          <el-select v-model="form.gender" style="width:100%">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄" required>
          <el-input-number v-model="form.age" :min="1" :max="120" />
        </el-form-item>
        <el-form-item label="身高 cm" required>
          <el-input-number v-model="form.height_cm" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="体重 kg" required>
          <el-input-number v-model="form.weight_kg" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="体脂率 %" required>
          <el-input-number v-model="form.body_fat_pct" :min="0" :max="60" :precision="1" />
        </el-form-item>
        <el-form-item label="目标体重 kg" required>
          <el-input-number v-model="form.target_weight_kg" :min="0" :precision="1" />
        </el-form-item>
        <el-form-item label="目标日期">
          <el-date-picker
            v-model="form.target_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择目标日期"
          />
        </el-form-item>
        <el-form-item label="活动水平" required>
          <el-select v-model="form.activity_level" style="width:100%">
            <el-option label="久坐（极少运动）" value="sedentary" />
            <el-option label="轻度活跃（1-3天/周）" value="light" />
            <el-option label="中度活跃（3-5天/周）" value="moderate" />
            <el-option label="非常活跃（6-7天/周）" value="active" />
            <el-option label="极度活跃（高强度/职业）" value="very_active" />
          </el-select>
        </el-form-item>
        <el-form-item label="Keep Token">
          <el-input v-model="form.keep_token" placeholder="粘贴 Keep JWT Token" type="textarea" :rows="3" />
          <div style="font-size:12px;color:var(--el-text-color-secondary);margin-top:4px">
            用于同步 Keep 运动数据（体能水平、周运动负荷）
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存画像</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="profile" style="margin-top:20px">
      <template #header><strong>计算结果</strong></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="BMR">{{ profile.bmr_kcal.toFixed(0) }} kcal/天</el-descriptions-item>
        <el-descriptions-item label="REE">{{ profile.ree_kcal.toFixed(0) }} kcal/天</el-descriptions-item>
        <el-descriptions-item label="去脂体重">{{ profile.ffm_kg.toFixed(1) }} kg</el-descriptions-item>
        <el-descriptions-item label="每周缺口目标">
          {{ profile.weekly_deficit_needed != null ? profile.weekly_deficit_needed.toFixed(0) + ' kcal' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="距离目标">
          {{ profile.days_remaining > 0 ? profile.days_remaining + ' 天' : '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchProfile,
  updateProfile,
  type ProfileCreate,
  type ProfileResponse,
} from '../api/profile'

const profile = ref<ProfileResponse | null>(null)
const loading = ref(false)
const saving = ref(false)

const form = ref<ProfileCreate>({
  name: '',
  gender: 'male',
  age: 30,
  height_cm: 170,
  weight_kg: 70,
  body_fat_pct: 20,
  target_weight_kg: 65,
  target_date: '',
  activity_level: 'moderate',
  keep_token: null,
})

async function loadProfile() {
  loading.value = true
  try {
    const p = await fetchProfile()
    profile.value = p
    form.value = {
      name: p.name,
      gender: p.gender,
      age: p.age,
      height_cm: p.height_cm,
      weight_kg: p.weight_kg,
      body_fat_pct: p.body_fat_pct,
      target_weight_kg: p.target_weight_kg,
      target_date: p.target_date,
      activity_level: p.activity_level,
      keep_token: p.keep_token,
    }
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const p = await updateProfile(form.value)
    profile.value = p
    ElMessage.success('画像已保存')
  } finally {
    saving.value = false
  }
}

onMounted(() => loadProfile())
</script>
