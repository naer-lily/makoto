<template>
  <el-container class="layout">
    <el-aside v-if="!isMobile" :width="isCollapse ? '64px' : '200px'" class="aside">
      <div class="logo">{{ isCollapse ? 'M' : 'makoto' }}</div>
      <el-menu :default-active="route.path" router :collapse="isCollapse" class="menu">
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon><span>仪表盘</span></el-menu-item>
        <el-menu-item index="/foods"><el-icon><Bowl /></el-icon><span>食物库</span></el-menu-item>
        <el-menu-item index="/body"><el-icon><Monitor /></el-icon><span>身体测量</span></el-menu-item>
        <el-menu-item index="/diet"><el-icon><DishDot /></el-icon><span>饮食记录</span></el-menu-item>
        <el-menu-item index="/exercise"><el-icon><Baseball /></el-icon><span>运动记录</span></el-menu-item>
        <el-menu-item index="/profile"><el-icon><UserFilled /></el-icon><span>个人画像</span></el-menu-item>
        <el-menu-item index="/circumference"><el-icon><SetUp /></el-icon><span>围度记录</span></el-menu-item>
      </el-menu>
    </el-aside>

    <el-drawer v-model="drawerVisible" direction="ltr" size="220px" :with-header="false">
      <div class="drawer-logo">makoto</div>
      <el-menu :default-active="route.path" router class="drawer-menu" @select="drawerVisible = false">
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon><span>仪表盘</span></el-menu-item>
        <el-menu-item index="/foods"><el-icon><Bowl /></el-icon><span>食物库</span></el-menu-item>
        <el-menu-item index="/body"><el-icon><Monitor /></el-icon><span>身体测量</span></el-menu-item>
        <el-menu-item index="/diet"><el-icon><DishDot /></el-icon><span>饮食记录</span></el-menu-item>
        <el-menu-item index="/exercise"><el-icon><Baseball /></el-icon><span>运动记录</span></el-menu-item>
        <el-menu-item index="/profile"><el-icon><UserFilled /></el-icon><span>个人画像</span></el-menu-item>
        <el-menu-item index="/circumference"><el-icon><SetUp /></el-icon><span>围度记录</span></el-menu-item>
      </el-menu>
      <div class="drawer-footer">
        <el-button type="danger" text @click="handleLogout">退出登录</el-button>
      </div>
    </el-drawer>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button v-if="!isMobile" text class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon :size="18"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </el-button>
          <el-button v-else text class="collapse-btn" @click="drawerVisible = true">
            <el-icon :size="20"><Menu /></el-icon>
          </el-button>
          <span v-if="isMobile" class="mobile-title">makoto</span>
        </div>
        <div class="header-right">
          <el-tooltip :content="modeLabel" placement="bottom">
            <el-button text class="theme-btn" @click="toggleTheme">
              <el-icon :size="18">
                <Sunny v-if="mode === 'light'" /><Moon v-else-if="mode === 'dark'" /><Setting v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-button v-if="!isMobile" text @click="handleLogout">退出登录</el-button>
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

const isMobile = ref(false)
const isCollapse = ref(false)
const drawerVisible = ref(false)

function handleResize() {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) isCollapse.value = false
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

.drawer-logo {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: var(--el-color-primary);
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: 8px;
}

.drawer-menu {
  border-right: none;
}

.drawer-footer {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-light);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  height: 48px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--el-color-primary);
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
</style>
