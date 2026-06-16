<template>
  <el-container class="layout">
    <el-aside width="200px" class="aside">
      <div class="logo">makoto</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/foods">
          <el-icon><Bowl /></el-icon>
          <span>食物库</span>
        </el-menu-item>
        <el-menu-item index="/diet">
          <el-icon><DishDot /></el-icon>
          <span>饮食记录</span>
        </el-menu-item>
        <el-menu-item index="/exercise">
          <el-icon><Baseball /></el-icon>
          <span>运动记录</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><UserFilled /></el-icon>
          <span>个人画像</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-right">
          <el-tooltip :content="modeLabel" placement="bottom">
            <el-button text class="theme-btn" @click="toggleTheme">
              <el-icon :size="18">
                <Sunny v-if="mode === 'light'" />
                <Moon v-else-if="mode === 'dark'" />
                <Setting v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-button text @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'

const { mode, modeLabel, toggleTheme } = useTheme()
const route = useRoute()
const router = useRouter()

function handleLogout() {
  localStorage.removeItem('makoto_token')
  router.push('/login')
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  color: var(--el-color-primary);
  border-bottom: 1px solid var(--el-border-color-light);
  letter-spacing: 2px;
}

.menu {
  border-right: none;
  flex: 1;
}

.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.theme-btn {
  padding: 8px;
  font-size: 18px;
}
</style>
