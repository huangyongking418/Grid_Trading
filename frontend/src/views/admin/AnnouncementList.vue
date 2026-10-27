<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>公告配置</b></span>
          <el-button type="primary" size="small" @click="openCreate">
            <el-icon><Plus /></el-icon> 发布公告
          </el-button>
        </div>
      </template>
      <el-table :data="announcements" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column label="图片" width="120">
          <template #default="{ row }">
            <div v-if="row.image_url">
              <el-image
                :src="row.image_url"
                fit="cover"
                style="width:64px;height:40px;border-radius:4px"
                :preview-src-list="[row.image_url]"
                preview-teleported
              />
              <div style="font-size:12px;color:#909399;margin-top:2px;max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center">
                {{ row.image_name || '未命名' }}
              </div>
            </div>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="260" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
              {{ row.status === 'enabled' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发布时间" width="170" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" size="small"
              @click="toggleStatus(row)">
              {{ row.status === 'enabled' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑公告' : '发布公告'" width="520px">
      <el-form :model="form" label-width="70px" size="small">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="图片">
          <div style="display:flex;gap:8px;align-items:center;width:100%">
            <el-upload
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              :http-request="uploadImage"
              accept=".jpg,.jpeg,.png,.webp"
            >
              <el-button size="small">上传图片</el-button>
            </el-upload>
            <el-image
              v-if="form.image_url"
              :src="form.image_url"
              fit="cover"
              style="width:70px;height:46px;border-radius:4px"
            />
            <el-button v-if="form.image_url" link type="danger" size="small" @click="form.image_url = ''">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="图片名称">
          <el-input v-model="form.image_name" placeholder="如：活动海报" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAnnouncements, createAnnouncement, updateAnnouncement, uploadAnnouncementImage } from '../../api/index.js'

const announcements = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref(null)
const form = ref({})

async function fetchData() {
  loading.value = true
  try {
    const r = await getAnnouncements()
    announcements.value = r.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  form.value = { title: '', content: '', image_url: '', image_name: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.value = { title: row.title, content: row.content, image_url: row.image_url || '', image_name: row.image_name || '' }
  dialogVisible.value = true
}

function beforeImageUpload(file) {
  const ext = (file.name || '').split('.').pop()?.toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
    ElMessage.error('仅支持 JPG / PNG / WebP 图片')
    return false
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

async function uploadImage(options) {
  try {
    const r = await uploadAnnouncementImage(options.file)
    form.value.image_url = r.data.url
    options.onSuccess?.(r.data)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '图片上传失败')
    options.onError?.(e)
  }
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      await updateAnnouncement(editId.value, form.value)
    } else {
      await createAnnouncement(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function toggleStatus(row) {
  try {
    const newStatus = row.status === 'enabled' ? 'disabled' : 'enabled'
    await updateAnnouncement(row.id, { status: newStatus })
    ElMessage.success('状态已更新')
    await fetchData()
  } catch { ElMessage.error('操作失败') }
}

onMounted(fetchData)
</script>
