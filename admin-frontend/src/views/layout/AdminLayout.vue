<template>
  <el-container class="admin-layout">
    <el-aside width="220px">
      <div class="logo">新闻管理后台</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/news">
          <el-icon><Document /></el-icon>
          <span>新闻管理</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/categories">
          <el-icon><Collection /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <span class="admin-name">{{ adminStore.adminInfo?.nickname || adminStore.adminInfo?.username }}</span>
        <el-button text @click="handleLogout">退出登录</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../../store/admin'
import { DataAnalysis, Document, User, Collection } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

function handleLogout() {
  adminStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  overflow-y: auto;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  border-bottom: 1px solid #e6e6e6;
  background: #fff;
}

.admin-name {
  color: #606266;
}

.el-main {
  background: #f0f2f5;
}
</style>
