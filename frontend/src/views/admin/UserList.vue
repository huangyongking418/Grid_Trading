<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>用户管理</b></span>
          <el-button type="primary" size="small" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增用户
          </el-button>
        </div>
      </template>
      <el-table :data="pagedUsers" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="90">
          <template #header>
            <div class="header-filter">
              <span>ID</span>
              <el-input v-model="userFilters.id" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="账号" min-width="140">
          <template #header>
            <div class="header-filter">
              <span>账号</span>
              <el-input v-model="userFilters.username" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140">
          <template #header>
            <div class="header-filter">
              <span>手机号</span>
              <el-input v-model="userFilters.phone" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role_name" label="角色" width="110">
          <template #header>
            <div class="header-filter">
              <span>角色</span>
              <el-input v-model="userFilters.role_name" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #header>
            <div class="header-filter">
              <span>状态</span>
              <el-input v-model="userFilters.status" placeholder="搜索" size="small" clearable />
            </div>
          </template>
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expire_date" label="账号有效期" min-width="180">
          <template #header>
            <div class="header-filter">
              <span>账号有效期</span>
              <el-input v-model="userFilters.expire_date" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="userPage"
          v-model:page-size="userPageSize"
          :total="filteredUsers.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新增用户'" width="420px">
      <el-form :model="form" label-width="90px" size="small">
        <el-form-item label="账号" required>
          <el-input v-model="form.username" :disabled="editing" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.phone" maxlength="11" />
        </el-form-item>
        <el-form-item v-if="!editing" label="密码" required>
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" style="width:100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期(天)">
          <el-input-number v-model="form.expire_days" :min="1" :max="3650" style="width:100%" />
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
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUsers, createUser, updateUser, getRoles } from '../../api/index.js'

const users = ref([])
const roles = ref([])
const loading = ref(false)
const userFilters = ref({ id: '', username: '', phone: '', role_name: '', status: '', expire_date: '' })
const userPage = ref(1)
const userPageSize = ref(10)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref(null)

const form = ref({})

const filteredUsers = computed(() => {
  const f = userFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return users.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return users.value.filter(row => (
    match(f.id, row.id)
    && match(f.username, row.username)
    && match(f.phone, row.phone)
    && match(f.role_name, row.role_name)
    && match(f.status, row.status === 'active' ? '启用' : '停用')
    && match(f.expire_date, row.expire_date)
  ))
})
const pagedUsers = computed(() => {
  const start = (userPage.value - 1) * userPageSize.value
  return filteredUsers.value.slice(start, start + userPageSize.value)
})
watch([filteredUsers, userPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredUsers.value.length / userPageSize.value))
  if (userPage.value > maxPage) userPage.value = maxPage
})
watch(userPageSize, () => { userPage.value = 1 })

async function fetchData() {
  loading.value = true
  try {
    const [u, r] = await Promise.all([getUsers(), getRoles()])
    users.value = u.data
    roles.value = r.data
  } catch (e) { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  editId.value = null
  form.value = {
    username: '', phone: '', password: '',
    role_id: roles.value.find(r => r.name === '普通用户')?.id,
    status: 'active', expire_days: 5,
  }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.value = {
    username: row.username, phone: row.phone,
    role_id: row.role_id, status: row.status,
    expire_days: 30,
  }
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      await updateUser(editId.value, form.value)
    } else {
      await createUser(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.header-filter {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.header-filter .el-input {
  width: 100%;
}
.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
