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
  min-height: 100vh;
  min-height: 100dvh;
  height: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(16px, env(safe-area-inset-top, 0px)) 16px
    max(16px, env(safe-area-inset-bottom, 0px));
  box-sizing: border-box;
  overflow-y: auto;
  background: var(--el-bg-color-page);
}

.login-card {
  width: min(400px, calc(100vw - 32px));
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
  min-height: 44px;
}

@media (max-width: 767px) {
  .login-card :deep(.el-card__body) {
    padding: 20px 16px;
  }

  .login-title {
    font-size: 24px;
  }

  .login-desc {
    margin-bottom: 18px;
  }
}

@media (max-height: 520px) {
  .login-page {
    align-items: flex-start;
  }
}
</style>
