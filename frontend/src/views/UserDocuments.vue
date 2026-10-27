<template>
  <div>
    <el-card shadow="never">
      <template #header><span><b>操作手册</b> — 系统使用文档查看与下载</span></template>
      <el-table :data="docs" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="description" label="说明" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="大小" width="90">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="更新时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="download(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="previewVisible" title="文档查看" width="860px" top="6vh">
      <iframe v-if="previewType === 'pdf'" :src="previewUrl" style="width:100%;height:70vh;border:1px solid #ebeef5;border-radius:4px"></iframe>
      <div v-else-if="previewType === 'image'" style="text-align:center">
        <el-image :src="previewUrl" fit="contain" style="max-width:100%;max-height:70vh" :preview-src-list="[previewUrl]" preview-teleported />
      </div>
      <pre v-else-if="previewType === 'txt'" style="max-height:70vh;overflow:auto;background:#f8f8f8;border:1px solid #ebeef5;border-radius:4px;padding:12px;font-size:13px;white-space:pre-wrap;word-break:break-word">{{ previewText }}</pre>
      <el-empty v-else-if="previewType === 'office'" description="该格式暂不支持在线预览，请下载后查看" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDocuments, downloadDocumentFile } from '../api/index.js'

const docs = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const previewType = ref('')
const previewUrl = ref('')
const previewText = ref('')

const IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'webp']

function formatSize(bytes) {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

async function fetchData() {
  loading.value = true
  try {
    const r = await getDocuments({ enabled_only: true })
    docs.value = r.data
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function view(row) {
  try {
    const r = await downloadDocumentFile(row.id)
    const ext = (row.file_ext || '').toLowerCase()
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    if (ext === 'pdf') {
      previewType.value = 'pdf'
      previewUrl.value = URL.createObjectURL(r.data)
    } else if (IMAGE_EXTS.includes(ext)) {
      previewType.value = 'image'
      previewUrl.value = URL.createObjectURL(r.data)
    } else if (ext === 'txt') {
      previewType.value = 'txt'
      previewText.value = await r.data.text()
    } else {
      previewType.value = 'office'
    }
    previewVisible.value = true
  } catch {
    ElMessage.error('文档加载失败')
  }
}

async function download(row) {
  try {
    const r = await downloadDocumentFile(row.id)
    const url = URL.createObjectURL(r.data)
    const a = document.createElement('a')
    a.href = url
    a.download = row.file_name
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

onMounted(fetchData)
onUnmounted(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>
