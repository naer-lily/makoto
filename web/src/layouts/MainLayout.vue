<template>
  <el-container class="layout" :class="{ 'is-mobile': isMobile }">
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
        <el-menu-item index="/painting"><el-icon><Brush /></el-icon><span>绘画记录</span></el-menu-item>
        <el-menu-item index="/weather"><el-icon><Sunny /></el-icon><span>天气监视</span></el-menu-item>
      </el-menu>
    </el-aside>

    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="280px"
      :with-header="false"
      class="more-drawer"
    >
      <div class="drawer-logo">makoto</div>
      <el-menu :default-active="route.path" router class="drawer-menu" @select="drawerVisible = false">
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon><span>仪表盘</span></el-menu-item>
        <el-menu-item index="/foods"><el-icon><Bowl /></el-icon><span>食物库</span></el-menu-item>
        <el-menu-item index="/body"><el-icon><Monitor /></el-icon><span>身体测量</span></el-menu-item>
        <el-menu-item index="/diet"><el-icon><DishDot /></el-icon><span>饮食记录</span></el-menu-item>
        <el-menu-item index="/exercise"><el-icon><Baseball /></el-icon><span>运动记录</span></el-menu-item>
        <el-menu-item index="/profile"><el-icon><UserFilled /></el-icon><span>个人画像</span></el-menu-item>
        <el-menu-item index="/circumference"><el-icon><SetUp /></el-icon><span>围度记录</span></el-menu-item>
        <el-menu-item index="/painting"><el-icon><Brush /></el-icon><span>绘画记录</span></el-menu-item>
        <el-menu-item index="/weather"><el-icon><Sunny /></el-icon><span>天气监视</span></el-menu-item>
      </el-menu>

      <div class="drawer-footer">
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </el-drawer>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button v-if="!isMobile" text class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon :size="18"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </el-button>
          <el-button
            v-else
            text
            class="collapse-btn menu-btn"
            aria-label="打开更多菜单"
            @click="drawerVisible = true"
          >
            <el-icon :size="20"><Menu /></el-icon>
          </el-button>
          <span v-if="isMobile" class="mobile-title">makoto</span>
        </div>
        <div class="header-right">
          <el-tooltip :content="modeLabel" placement="bottom">
            <el-button text class="theme-btn" :aria-label="modeLabel" @click="toggleTheme">
              <el-icon :size="18">
                <Sunny v-if="mode === 'light'" /><Moon v-else-if="mode === 'dark'" /><Setting v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-button v-if="!isMobile" text @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main-scroll" :class="{ 'with-bottom-nav': isMobile }">
        <router-view />
      </el-main>
    </el-container>

    <nav v-if="isMobile" class="bottom-nav" aria-label="主导航">
      <button
        type="button"
        class="bottom-nav-item"
        :class="{ active: route.path === '/' }"
        :aria-current="route.path === '/' ? 'page' : undefined"
        @click="go('/')"
      >
        <el-icon :size="21"><DataAnalysis /></el-icon>
        <span>总览</span>
      </button>
      <button
        type="button"
        class="bottom-nav-item"
        :class="{ active: route.path === '/diet' }"
        :aria-current="route.path === '/diet' ? 'page' : undefined"
        @click="go('/diet')"
      >
        <el-icon :size="21"><DishDot /></el-icon>
        <span>饮食</span>
      </button>
      <button
        type="button"
        class="bottom-nav-item"
        :class="{ active: route.path === '/exercise' }"
        :aria-current="route.path === '/exercise' ? 'page' : undefined"
        @click="go('/exercise')"
      >
        <el-icon :size="21"><Baseball /></el-icon>
        <span>运动</span>
      </button>
      <button
        type="button"
        class="bottom-nav-item"
        :class="{ active: route.path === '/body' }"
        :aria-current="route.path === '/body' ? 'page' : undefined"
        @click="go('/body')"
      >
        <el-icon :size="21"><Monitor /></el-icon>
        <span>身体</span>
      </button>
      <button
        type="button"
        class="bottom-nav-item"
        :class="{ active: moreActive }"
        :aria-expanded="drawerVisible"
        @click="drawerVisible = true"
      >
        <el-icon :size="21"><MoreFilled /></el-icon>
        <span>更多</span>
      </button>
    </nav>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useMobile } from '../composables/useMobile'

const { mode, modeLabel, toggleTheme } = useTheme()
const route = useRoute()
const router = useRouter()
const isMobile = useMobile()

const isCollapse = ref(false)
const drawerVisible = ref(false)

const moreActive = computed(
  () => !['/', '/diet', '/exercise', '/body'].includes(route.path),
)

watch(
  () => route.path,
  () => {
    drawerVisible.value = false
  },
)

function go(path: string): void {
  if (route.path !== path) void router.push(path)
}

function handleLogout(): void {
  localStorage.removeItem('makoto_token')
  void router.push('/login')
}
</script>

<style scoped>
.layout {
  height: 100vh;
  height: 100dvh;
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

.drawer-menu :deep(.el-menu-item) {
  min-height: 48px;
}

.drawer-footer {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-light);
}

.drawer-footer .el-button {
  width: 100%;
  min-height: 44px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  height: 48px;
  flex: 0 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.mobile-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.collapse-btn {
  padding: 8px;
  min-width: 40px;
  min-height: 40px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

.theme-btn {
  padding: 8px;
  min-width: 40px;
  min-height: 40px;
  font-size: 18px;
}

.main-scroll {
  padding: 24px;
}

.main-scroll.with-bottom-nav {
  padding: 8px 8px calc(72px + env(safe-area-inset-bottom, 0px));
}

.layout.is-mobile .header {
  padding-top: env(safe-area-inset-top, 0px);
  height: calc(48px + env(safe-area-inset-top, 0px));
  box-sizing: border-box;
}

.layout.is-mobile .header-left {
  gap: 2px;
}

.bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  /* Below Element Plus overlays (2000+) so a drawer/dialog dims the nav too. */
  z-index: 1900;
  display: flex;
  align-items: stretch;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.bottom-nav-item {
  position: relative;
  flex: 1 1 0;
  min-width: 0;
  min-height: 56px;
  padding: 6px 2px;
  border: 0;
  background: transparent;
  color: var(--el-text-color-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font: inherit;
  font-size: 11px;
  line-height: 1.2;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.bottom-nav-item:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: -2px;
}

.bottom-nav-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.bottom-nav-item.active {
  color: var(--el-color-primary);
  font-weight: 600;
}

.bottom-nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 2px;
  border-radius: 0 0 2px 2px;
  background: var(--el-color-primary);
}

@media (min-width: 768px) {
  .main-scroll {
    overflow-y: auto;
  }
}
</style>
