<template>
  <div class="news-list">
    <div class="toolbar">
      <el-radio-group v-model="params.status" @change="onStatusChange">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="published">已发布</el-radio-button>
        <el-radio-button value="draft">待审核</el-radio-button>
      </el-radio-group>
      <el-input v-model="params.keyword" placeholder="搜索标题" clearable style="width:200px;margin-left:16px" @clear="fetchData" @keyup.enter="fetchData" />
      <el-select v-model="params.categoryId" placeholder="分类筛选" clearable @change="fetchData" style="width:150px;margin-left:8px">
        <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
      </el-select>
      <div style="flex:1" />
      <el-button @click="$router.push('/news/import')">导入JSON</el-button>
      <el-button type="primary" @click="$router.push('/news/create')">新建新闻</el-button>
    </div>

    <div v-if="params.status === 'draft' && selectedIds.length > 0" class="batch-bar">
      <span>已选 {{ selectedIds.length }} 条</span>
      <el-button type="success" @click="handleBatchApprove">全部通过</el-button>
      <el-button type="danger" @click="handleBatchReject">全部驳回</el-button>
    </div>

    <el-card>
      <el-table :data="list" v-loading="loading" stripe @selection-change="onSelectionChange">
        <el-table-column type="selection" width="40" v-if="params.status === 'draft'" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="showDetail(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryName(row.category_id) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column prop="views" label="浏览" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'draft' ? 'warning' : 'success'" size="small">
              {{ row.status === 'draft' ? '待审核' : '已发布' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="160">
          <template #default="{ row }">
            {{ row.publish_time ? new Date(row.publish_time).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'draft'">
              <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
              <el-button size="small" type="danger" @click="handleReject(row)">驳回</el-button>
            </template>
            <template v-else>
              <el-button size="small" @click="$router.push(`/news/${row.id}/edit`)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="新闻详情" width="700px" top="5vh">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ detail.title }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ getCategoryName(detail.category_id) }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ detail.author || '-' }}</el-descriptions-item>
          <el-descriptions-item label="浏览量">{{ detail.views }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detail.status === 'draft' ? 'warning' : 'success'" size="small">
              {{ detail.status === 'draft' ? '待审核' : '已发布' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ detail.publish_time ? new Date(detail.publish_time).toLocaleString() : '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detail.updated_at ? new Date(detail.updated_at).toLocaleString() : '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源URL" :span="2">
            <a v-if="detail.source_url" :href="detail.source_url" target="_blank" style="color:#409eff">{{ detail.source_url }}</a>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="摘要" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="detail.image" style="margin-top:16px;text-align:center">
          <el-image :src="detail.image" style="max-width:100%;max-height:300px" fit="contain" />
        </div>
        <div style="margin-top:16px">
          <h4>正文</h4>
          <div class="content-box">{{ detail.content }}</div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getNewsList, getNewsDetail, deleteNews, approveNews, rejectNews, batchApproveNews, batchRejectNews } from '../../api/news'
import { getCategories } from '../../api/categories'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const categories = ref([])
const detailVisible = ref(false)
const detail = ref(null)
const selectedIds = ref([])

const params = reactive({
  page: 1,
  pageSize: 10,
  categoryId: null,
  keyword: '',
  status: '',
})

onMounted(() => {
  fetchData()
  loadCategories()
})

function onStatusChange() {
  params.page = 1
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const query = { page: params.page, pageSize: params.pageSize }
    if (params.categoryId) query.categoryId = params.categoryId
    if (params.keyword) query.keyword = params.keyword
    if (params.status) query.status = params.status
    const res = await getNewsList(query)
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const res = await getCategories()
  categories.value = res.data
}

function getCategoryName(category_id) {
  const cat = categories.value.find(c => c.id === category_id)
  return cat ? cat.name : '-'
}

async function handleApprove(row) {
  await approveNews(row.id)
  ElMessage.success('审核通过')
  fetchData()
}

async function handleReject(row) {
  await ElMessageBox.confirm(`确定驳回「${row.title}」吗？驳回后将被删除。`, '驳回确认', { type: 'warning' })
  await rejectNews(row.id)
  ElMessage.success('已驳回')
  fetchData()
}

async function showDetail(row) {
  const res = await getNewsDetail(row.id)
  detail.value = res.data
  detailVisible.value = true
}

function onSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

async function handleBatchApprove() {
  await ElMessageBox.confirm(`确定通过选中的 ${selectedIds.value.length} 条新闻吗？`, '批量通过', { type: 'info' })
  await batchApproveNews(selectedIds.value)
  ElMessage.success('批量通过完成')
  selectedIds.value = []
  fetchData()
}

async function handleBatchReject() {
  await ElMessageBox.confirm(`确定驳回选中的 ${selectedIds.value.length} 条新闻吗？驳回后将被删除。`, '批量驳回', { type: 'warning' })
  await batchRejectNews(selectedIds.value)
  ElMessage.success('批量驳回完成')
  selectedIds.value = []
  fetchData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定要删除「${row.title}」吗？`, '确认删除', { type: 'warning' })
  await deleteNews(row.id)
  ElMessage.success('删除成功')
  fetchData()
}
</script>

<style scoped>
.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.content-box {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.8;
}

.batch-bar {
  margin-bottom: 12px;
  padding: 10px 16px;
  background: #ecf5ff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #409eff;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
