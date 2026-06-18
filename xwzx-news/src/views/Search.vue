<template>
  <div class="search-page">
    <van-nav-bar title="搜索" left-text="返回" left-arrow @click-left="$router.back()" fixed />

    <div class="search-input-wrap">
      <van-search
        v-model="keyword"
        placeholder="搜索新闻标题"
        shape="round"
        @search="doSearch"
      />
    </div>

    <div class="search-content">
      <div v-if="!hasSearched" class="empty-hint">输入关键词搜索新闻</div>

      <van-empty v-else-if="list.length === 0 && !loading" description="未找到相关新闻" />

      <van-list
        v-else
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <news-item v-for="item in list" :key="item.id" :news="item" />
      </van-list>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { apiConfig } from '../config/api'
import NewsItem from '../components/NewsItem.vue'
import TabBar from '../components/TabBar.vue'

const route = useRoute()
const keyword = ref('')
const list = ref([])
const loading = ref(false)
const finished = ref(false)
const hasSearched = ref(false)
let page = 1

// 从 URL 参数初始化
watch(() => route.query.keyword, (kw) => {
  if (kw) {
    keyword.value = kw
    list.value = []
    page = 1
    finished.value = false
    doSearch()
  }
}, { immediate: true })

async function doSearch() {
  if (!keyword.value.trim()) return
  list.value = []
  page = 1
  finished.value = false
  hasSearched.value = true
  await fetchResults()
}

async function onLoad() {
  await fetchResults()
}

async function fetchResults() {
  loading.value = true
  try {
    const res = await axios.get(`${apiConfig.baseURL}/api/news/search`, {
      params: { keyword: keyword.value.trim(), page, pageSize: 10 }
    })
    if (res.data.code === 200) {
      const data = res.data.data
      list.value = page === 1 ? data.list : [...list.value, ...data.list]
      if (data.list.length < 10) finished.value = true
      page++
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-page {
  padding-top: 46px;
  padding-bottom: 50px;
  min-height: 100vh;
  background: #f7f8fa;
}

.search-input-wrap {
  background: #fff;
}

.search-content {
  padding: 10px 0;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 60px 0;
  font-size: 14px;
}
</style>
