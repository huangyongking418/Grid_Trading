<template>
  <router-view v-if="isLoginPage" />
  <div v-else class="app-container">
    <el-container>
      <el-aside width="210px">
        <div class="logo">网格策</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#001529"
          text-color="#ffffff"
          active-text-color="#409eff"
        >
          <el-menu-item index="/strategies">
            <el-icon><Setting /></el-icon>
            <span>策略管理</span>
          </el-menu-item>
          <el-menu-item index="/operations">
            <el-icon><List /></el-icon>
            <span>操作明细</span>
          </el-menu-item>
          <el-menu-item index="/monitor">
            <el-icon><Monitor /></el-icon>
            <span>监控设置</span>
          </el-menu-item>
          <el-menu-item index="/profit">
            <el-icon><TrendCharts /></el-icon>
            <span>收益分析</span>
          </el-menu-item>
          <el-menu-item index="/backtest">
            <el-icon><DataAnalysis /></el-icon>
            <span>模拟回测</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><Document /></el-icon>
            <span>操作手册</span>
          </el-menu-item>
          <el-menu-item index="/messages">
            <el-icon><Message /></el-icon>
            <span>站内消息</span>
            <el-tag v-if="unreadCount > 0" type="danger" size="small" style="margin-left:auto">{{ unreadCount }}</el-tag>
          </el-menu-item>
          <el-sub-menu v-if="isAdmin" index="/admin">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
            <el-menu-item index="/admin/roles">角色管理</el-menu-item>
            <el-menu-item index="/admin/params">系统参数</el-menu-item>
            <el-menu-item index="/admin/announcements">公告配置</el-menu-item>
            <el-menu-item index="/admin/scheduler">定时任务</el-menu-item>
            <el-menu-item index="/admin/email-config">邮件服务配置</el-menu-item>
            <el-menu-item index="/admin/documents">文档管理</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-left">
            <h2>{{ pageTitle }}</h2>
          </div>
          <div class="header-right">
            <el-popover
              v-for="(ann, i) in announcements"
              :key="ann.id"
              placement="bottom"
              trigger="hover"
              width="320"
              popper-class="announcement-popper"
            >
              <template #reference>
                <div class="announcement-item" :style="{ animationDelay: (i * 120) + 'ms' }">
                  <el-icon class="announcement-icon"><Bell /></el-icon>
                  <span class="announcement-title">{{ ann.title }}</span>
                </div>
              </template>
              <div class="announcement-body">
              <div class="announcement-head">
                <span class="announcement-name">{{ ann.title }}</span>
              </div>
              <el-image
                v-if="ann.image_url"
                :src="ann.image_url"
                fit="contain"
                style="width:100%;max-height:180px;margin-bottom:8px;border-radius:4px"
                :preview-src-list="[ann.image_url]"
                preview-teleported
              />
              <div v-if="ann.image_url && ann.image_name" style="margin:-2px 0 8px;color:#8a6d1a;font-size:13px;font-weight:600;text-align:center">
                {{ ann.image_name }}
              </div>
              <p class="announcement-content">{{ ann.content || '暂无详细内容' }}</p>
                <div class="announcement-time">{{ formatTime(ann.create_time) }}</div>
              </div>
            </el-popover>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                {{ user?.username || '未登录' }}
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>角色: {{ user?.role_name || '-' }}</el-dropdown-item>
                  <el-dropdown-item disabled>有效期至: {{ user?.expire_date?.slice(0,10) || '-' }}</el-dropdown-item>
                  <el-dropdown-item command="changePassword">密码修改</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
      <el-dialog v-model="passwordDialogVisible" title="密码修改" width="420px">
        <el-form :model="passwordForm" label-width="90px" size="small">
          <el-form-item label="原密码">
            <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="passwordSaving" @click="submitPassword">确认修改</el-button>
        </template>
      </el-dialog>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUnreadCount, getAnnouncements, changePassword } from './api/index.js'

const route = useRoute()
const router = useRouter()
const isLoginPage = computed(() => route.path === '/login')
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '网格策')
const unreadCount = ref(0)
const announcements = ref([])
const user = ref(JSON.parse(localStorage.getItem('gts_user') || 'null'))
const isAdmin = computed(() => user.value?.role_name === '管理员')
const passwordDialogVisible = ref(false)
const passwordSaving = ref(false)
const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })

async function fetchUnread() {
  try {
    const r = await getUnreadCount()
    unreadCount.value = r.data.count
  } catch {}
}

async function fetchAnnouncements() {
  try {
    const r = await getAnnouncements()
    announcements.value = r.data.filter(a => a.status === 'enabled').slice(0, 2)
  } catch {}
}

function handleCommand(cmd) {
  if (cmd === 'changePassword') {
    passwordDialogVisible.value = true
    return
  }
  if (cmd === 'logout') {
    localStorage.removeItem('gts_token')
    localStorage.removeItem('gts_user')
    router.push('/login')
  }
}

async function submitPassword() {
  const { old_password, new_password, confirm_password } = passwordForm.value
  if (!old_password || !new_password || !confirm_password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于 6 位')
    return
  }
  if (new_password !== confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (new_password === old_password) {
    ElMessage.warning('新密码不能与原密码相同')
    return
  }
  passwordSaving.value = true
  try {
    await changePassword({ old_password, new_password })
    ElMessage.success('密码修改成功，请重新登录')
    passwordDialogVisible.value = false
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    localStorage.removeItem('gts_token')
    localStorage.removeItem('gts_user')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '密码修改失败')
  } finally {
    passwordSaving.value = false
  }
}

function formatTime(t) {
  return t ? String(t).replace('T', ' ').slice(0, 16) : ''
}

onMounted(() => {
  if (localStorage.getItem('gts_token')) {
    fetchUnread()
    fetchAnnouncements()
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
.app-container { height: 100%; }
.el-aside { background-color: #001529; min-height: 100vh; }
.logo {
  height: 60px;
  line-height: 60px;
  padding-left: 20px;
  text-align: left;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0;
  border-bottom: 1px solid #0a2538;
}
/* 统一侧边栏上中下三段左侧基线 */
.el-aside .el-menu {
  border-right: none;
}
.el-aside .el-menu-item {
  padding-left: 20px !important;
}
.el-aside .el-sub-menu .el-menu-item {
  padding-left: 44px !important;
}
.el-aside .el-sub-menu__title {
  padding-left: 20px !important;
  padding-right: 20px !important;
}
.el-aside .el-menu-item .el-icon,
.el-aside .el-sub-menu__title .el-icon {
  width: 24px;
  margin-right: 6px;
  flex-shrink: 0;
}
.el-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.el-header h2 { font-size: 18px; font-weight: 500; }
.header-right { display: flex; align-items: center; }
.announcement-item {
  display: flex;
  align-items: center;
  gap: 5px;
  max-width: 240px;
  height: 28px;
  margin-right: 10px;
  padding: 0 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(250, 204, 21, 0.16), rgba(56, 189, 248, 0.12));
  border: 1px solid rgba(250, 204, 21, 0.4);
  color: #8a6d1a;
  cursor: pointer;
  animation:
    announcement-enter 0.5s ease both,
    announcement-pulse 2.6s ease-in-out 0.5s infinite;
}
.announcement-icon {
  flex-shrink: 0;
  color: #e6a23c;
}
.announcement-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}
@keyframes announcement-enter {
  from { opacity: 0; transform: translateY(-8px) scale(0.9); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes announcement-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(250, 204, 21, 0.3); }
  50% { box-shadow: 0 0 14px 2px rgba(250, 204, 21, 0.45); }
}
.announcement-body {
  padding: 4px 2px;
}
.announcement-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px dashed #e5e7eb;
}
.announcement-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.announcement-content {
  margin: 0;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-line;
  word-break: break-word;
  animation: announcement-in 0.35s ease both;
}
.announcement-time {
  margin-top: 10px;
  color: #9ca3af;
  font-size: 11px;
}
@keyframes announcement-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
  outline: none;
}
.el-main { background: #f5f7fa; min-height: calc(100vh - 60px); }
</style>
