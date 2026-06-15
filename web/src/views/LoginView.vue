<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="login-title">makoto</h2>
      <p class="login-desc">输入 Token 登录</p>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="token"
            type="password"
            placeholder="请输入 MAKOTO_TOKEN"
            show-password
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const token = ref('')
const loading = ref(false)
const router = useRouter()

async function handleLogin() {
  if (!token.value) return
  loading.value = true
  try {
    await axios.get('/api/v1/profile', {
      headers: { Authorization: `Bearer ${token.value}` },
    })
    localStorage.setItem('makoto_token', token.value)
    router.push('/')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}

.login-card {
  width: 400px;
  text-align: center;
}

.login-title {
  font-size: 28px;
  letter-spacing: 4px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.login-desc {
  color: var(--el-text-color-secondary);
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
}
</style>
