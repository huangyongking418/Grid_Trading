<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>文档管理</b> — 操作手册等文档的上传与维护</span>
          <el-button type="primary" size="small" @click="openUpload">
            <el-icon><Upload /></el-icon> 上传文档
          </el-button>
        </div>
      </template>
      <el-table :data="docs" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="file_name" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column label="大小" width="90">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
              {{ row.status === 'enabled' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploader" label="上传人" width="110" />
        <el-table-column prop="create_time" label="上传时间" width="160" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="download(row)">下载</el-button>
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" size="small" @click="toggleStatus(row)">
              {{ row.status === 'enabled' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="uploadVisible" title="上传文档" width="520px">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="如：系统操作手册" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width:100%">
            <el-option label="操作手册" value="操作手册" />
            <el-option label="说明文档" value="说明文档" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-exceed="onFileExceed"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.webp"
          >
            <el-button size="small">选择文件</el-button>
          </el-upload>
          <div v-if="selectedFile" style="font-size:12px;color:#909399;margin-top:6px">
            {{ selectedFile.name }}（{{ formatSize(selectedFile.size) }}）
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑文档" width="480px">
      <el-form :model="form" label-width="80px" size="small">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width:100%">
            <el-option label="操作手册" value="操作手册" />
            <el-option label="说明文档" value="说明文档" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="enabled">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDocuments, uploadDocument, updateDocument, deleteDocument, downloadDocumentFile } from '../../api/index.js'

const docs = ref([])
const loading = ref(false)
const saving = ref(false)
const uploadVisible = ref(false)
const editVisible = ref(false)
const editId = ref(null)
const selectedFile = ref(null)
const form = ref({ title: '', category: '操作手册', description: '', status: 'enabled' })

const ALLOWED_EXTS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'webp']

function formatSize(bytes) {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

async function fetchData() {
  loading.value = true
  try {
    const r = await getDocuments()
    docs.value = r.data
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function openUpload() {
  form.value = { title: '', category: '操作手册', description: '', status: 'enabled' }
  selectedFile.value = null
  uploadVisible.value = true
}

function onFileChange(file) {
  const raw = file.raw
  if (!raw) return
  const ext = (raw.name || '').split('.').pop()?.toLowerCase()
  if (!ALLOWED_EXTS.includes(ext)) {
    ElMessage.error('不支持的文件类型')
    return
  }
  if (raw.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB')
    return
  }
  selectedFile.value = raw
}

function onFileExceed() {
  ElMessage.warning('只能选择一个文件')
}

async function submitUpload() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    fd.append('title', form.value.title.trim())
    fd.append('category', form.value.category)
    fd.append('description', form.value.description || '')
    await uploadDocument(fd)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    await fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  } finally {
    saving.value = false
  }
}

function openEdit(row) {
  editId.value = row.id
  form.value = {
    title: row.title,
    category: row.category,
    description: row.description || '',
    status: row.status,
  }
  editVisible.value = true
}

async function saveEdit() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    await updateDocument(editId.value, form.value)
    ElMessage.success('保存成功')
    editVisible.value = false
    await fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row) {
  try {
    await updateDocument(row.id, { status: row.status === 'enabled' ? 'disabled' : 'enabled' })
    ElMessage.success('状态已更新')
    await fetchData()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除文档「${row.title}」吗？文件将一并删除`, '确认')
    await deleteDocument(row.id)
    ElMessage.success('已删除')
    await fetchData()
  } catch {}
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
</script>
