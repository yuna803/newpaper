<template>
  <div class="news-form">
    <el-card>
      <template #header>
        <span>{{ isEdit ? '编辑新闻' : '新建新闻' }}</span>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="分类" prop="categoryId">
          <el-select v-model="form.categoryId" placeholder="选择分类" style="width:100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="12" />
        </el-form-item>
        <el-form-item label="封面图">
          <el-input v-model="form.image" placeholder="图片URL" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="form.author" />
        </el-form-item>
        <el-form-item label="发布时间">
          <el-date-picker v-model="form.publishTime" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createNews, updateNews, getNewsDetail } from '../../api/news'
import { getCategories } from '../../api/categories'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const categories = ref([])

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  title: '',
  categoryId: null,
  description: '',
  content: '',
  image: '',
  author: '',
  publishTime: '',
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  categoryId: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

onMounted(async () => {
  const res = await getCategories()
  categories.value = res.data
  if (isEdit.value) {
    const { data } = await getNewsDetail(route.params.id)
    Object.assign(form, {
      title: data.title,
      categoryId: data.category_id,
      description: data.description || '',
      content: data.content,
      image: data.image || '',
      author: data.author || '',
      publishTime: data.publish_time || '',
    })
  }
})

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      title: form.title,
      categoryId: form.categoryId,
      content: form.content,
    }
    if (form.description) payload.description = form.description
    if (form.image) payload.image = form.image
    if (form.author) payload.author = form.author
    if (form.publishTime) payload.publishTime = form.publishTime

    if (isEdit.value) {
      await updateNews(route.params.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createNews(payload)
      ElMessage.success('创建成功')
    }
    router.push('/news')
  } finally {
    submitting.value = false
  }
}
</script>
