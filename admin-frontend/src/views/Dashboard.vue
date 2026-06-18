<template>
  <div class="dashboard">
    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom:16px" closable @close="error=''" />
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" :style="{ backgroundColor: card.color }">
              <el-icon :size="28"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">{{ card.label }}</div>
              <div class="stat-value">{{ card.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { User, Document, View, Collection } from '@element-plus/icons-vue'
import { getDashboardStats } from '../api/dashboard'

const stats = ref({ total_users: 0, total_news: 0, total_views: 0, total_categories: 0 })
const error = ref('')

const cards = computed(() => [
  { label: '用户总数', value: stats.value.total_users, icon: User, color: '#409eff' },
  { label: '新闻总数', value: stats.value.total_news, icon: Document, color: '#67c23a' },
  { label: '总浏览量', value: stats.value.total_views, icon: View, color: '#e6a23c' },
  { label: '分类数量', value: stats.value.total_categories, icon: Collection, color: '#f56c6c' },
])

onMounted(async () => {
  try {
    const res = await getDashboardStats()
    stats.value = res.data
  } catch (e) {
    error.value = e.message || '加载失败'
    console.error('Dashboard load error:', e)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-top: 4px;
}
</style>
