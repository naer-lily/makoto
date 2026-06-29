<template>
  <el-container class="layout">
    <el-aside :width="isCollapse ? '64px' : '200px'" class="aside">
      <div class="logo">{{ isCollapse ? 'M' : 'makoto' }}</div>
      <el-menu :default-active="route.path" router :collapse="isCollapse" class="menu">
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/foods">
          <el-icon><Bowl /></el-icon>
          <span>食物库</span>
        </el-menu-item>
        <el-menu-item index="/body">
          <el-icon><Monitor /></el-icon>
          <span>身体测量</span>
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
        <el-menu-item index="/circumference">
          <el-icon><SetUp /></el-icon>
          <span>围度记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-button text class="collapse-btn" @click="isCollapse = !isCollapse">
          <el-icon :size="18">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </el-button>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'

const { mode, modeLabel, toggleTheme } = useTheme()
const route = useRoute()
const router = useRouter()

const isCollapse = ref(false)

function handleResize() {
  isCollapse.value = window.innerWidth < 768
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

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
  transition: width 0.2s;
  overflow: hidden;
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
  white-space: nowrap;
}

.menu {
  border-right: none;
  flex: 1;
}

.menu:not(.el-menu--collapse) {
  width: 200px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.collapse-btn {
  padding: 8px;
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

@media (max-width: 768px) {
  .logo {
    font-size: 16px;
    letter-spacing: 0;
  }
}
</style>
