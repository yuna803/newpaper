<template>
  <div class="import-news">
    <!-- 一键爬取 -->
    <el-card>
      <template #header>
        <span>一键爬取新浪新闻</span>
        <span style="margin-left:8px;color:#909399;font-size:13px">爬取的新闻将保存为「待审核」状态</span>
      </template>

      <el-form :inline="true">
        <el-form-item label="频道">
          <el-select v-model="scrapeForm.channel" style="width:160px">
            <el-option label="全部" value="all" />
            <el-option label="财经" value="finance" />
            <el-option label="科技" value="tech" />
            <el-option label="体育" value="sports" />
            <el-option label="娱乐" value="ent" />
            <el-option label="国际" value="world" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-select v-model="scrapeForm.count" style="width:120px">
            <el-option :value="20" label="20 条" />
            <el-option :value="40" label="40 条" />
            <el-option :value="60" label="60 条" />
            <el-option :value="100" label="100 条" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="scrapeForm.deep">深度抓取正文</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="scraping" @click="handleScrape">
            <el-icon v-if="!scraping"><Download /></el-icon>
            开始爬取
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="scrapeResult" style="margin-top:8px">
        <el-alert
          :type="scrapeResult.imported > 0 ? 'success' : 'info'"
          :closable="false"
          show-icon
        >
          <template #title>
            爬取 {{ scrapeResult.total }} 条，成功导入 {{ scrapeResult.imported }} 条，
            跳过 {{ scrapeResult.skipped }} 条（重复）
            <el-button v-if="scrapeResult.imported > 0" type="primary" text size="small" @click="goToPending">去审核 →</el-button>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- JSON 导入 -->
    <el-card style="margin-top:16px">
      <template #header>
        <span>JSON 文件导入</span>
      </template>

      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".json"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽 JSON 文件到此处 或 <em>点击选择</em></div>
        </el-upload>
        <div style="margin-top:12px;color:#909399;font-size:13px">
          或粘贴 JSON：
        </div>
        <el-input
          v-model="jsonText"
          type="textarea"
          :rows="6"
          placeholder='粘贴 JSON 数组，例如: [{"title":"...","categoryId":1,"sourceUrl":"..."}]'
          style="margin-top:8px"
        />
      </div>

      <div v-if="preview.length > 0" style="margin-top:16px">
        <el-table :data="preview" max-height="300" stripe>
          <el-table-column type="index" label="#" width="40" />
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column label="分类" width="100">
            <template #default="{ row }">
              {{ getCategoryName(row.categoryId) }}
            </template>
          </el-table-column>
          <el-table-column prop="author" label="作者" width="100" />
        </el-table>

        <div style="margin-top:12px;display:flex;gap:12px">
          <el-button type="primary" :loading="importing" @click="handleImport">
            确认导入 ({{ preview.length }} 条)
          </el-button>
          <el-button @click="handleClear">清空</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Download } from '@element-plus/icons-vue'
import { importNews, scrapeNews } from '../../api/news'
import { getCategories } from '../../api/categories'

const router = useRouter()

// --- 一键爬取 ---
const scraping = ref(false)
const scrapeResult = ref(null)
const scrapeForm = reactive({ channel: 'all', count: 40, deep: true })

async function handleScrape() {
  scraping.value = true
  scrapeResult.value = null
  try {
    const res = await scrapeNews({ channel: scrapeForm.channel, count: scrapeForm.count, deep: scrapeForm.deep })
    scrapeResult.value = res.data
    ElMessage.success(res.message)
  } catch (e) {
    ElMessage.error(e.message || '爬取失败')
  } finally {
    scraping.value = false
  }
}

function goToPending() {
  router.push('/news?status=draft')
}

// --- JSON 导入 ---
const jsonText = ref('')
const preview = ref([])
const importing = ref(false)
const categories = ref([])

getCategories().then(res => { categories.value = res.data })

function getCategoryName(id) {
  const cat = categories.value.find(c => c.id === id)
  return cat ? cat.name : `ID:${id}`
}

function parseJSON(text) {
  try {
    if (!text || !text.trim()) return []
    const data = JSON.parse(text)
    if (!Array.isArray(data)) return []
    return data.filter(item => item.title && item.categoryId)
  } catch {
    return []
  }
}

function handleFileChange(file) {
  const reader = new FileReader()
  reader.onload = e => {
    const items = parseJSON(e.target.result)
    if (items.length === 0) return ElMessage.error('JSON 格式不正确')
    preview.value = items
    jsonText.value = JSON.stringify(items, null, 2)
    ElMessage.success(`已加载 ${items.length} 条`)
  }
  reader.readAsText(file.raw)
}

async function handleImport() {
  importing.value = true
  try {
    const res = await importNews(preview.value)
    ElMessage.success(`导入完成：成功${res.data.imported}条，跳过${res.data.skipped}条`)
    handleClear()
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

function handleClear() {
  preview.value = []
  jsonText.value = ''
}
</script>

<style scoped>
.upload-area {
  margin-bottom: 16px;
}
</style>
