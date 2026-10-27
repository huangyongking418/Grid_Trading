<template>
  <div>
    <el-card shadow="never" class="smtp-card">
      <template #header><span><b>邮件服务配置</b></span></template>
      <el-form label-width="120px" size="small">
        <el-form-item label="SMTP 服务器">
          <el-input v-model="cfg.smtp_host" placeholder="smtp.example.com" style="width:320px" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="cfg.smtp_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="账号">
          <el-input v-model="cfg.smtp_user" placeholder="SMTP 账号" style="width:320px" />
        </el-form-item>
        <el-form-item label="授权码/密码">
          <el-input v-model="cfg.smtp_password" type="password" placeholder="留空则保持原密码" style="width:320px" />
        </el-form-item>
        <el-form-item label="发件人邮箱">
          <el-input v-model="cfg.from_email" placeholder="发件人邮箱" style="width:320px" />
        </el-form-item>
        <el-form-item label="测试收件人">
          <el-input v-model="testTo" placeholder="测试邮件收件人" style="width:320px" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="cfg.enabled" active-text="启用" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
          <el-button type="warning" @click="testEmail" :loading="testing">发送测试邮件</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSmtpConfig, updateSmtpConfig, sendTestEmail } from '../../api/index.js'

const cfg = ref({ smtp_host: '', smtp_port: 465, smtp_user: '', smtp_password: '', from_email: '', enabled: false })
const testTo = ref('')
const saving = ref(false)
const testing = ref(false)

async function fetchConfig() {
  try {
    const r = await getSmtpConfig()
    cfg.value = { ...cfg.value, ...r.data, smtp_password: '' }
  } catch {
    ElMessage.error('获取配置失败')
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await updateSmtpConfig(cfg.value)
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testEmail() {
  if (!testTo.value.trim()) {
    ElMessage.warning('请先填写测试收件人邮箱')
    return
  }
  testing.value = true
  try {
    const r = await sendTestEmail({ to_email: testTo.value.trim() })
    if (r.data.ok) ElMessage.success('测试邮件发送成功')
    else ElMessage.error('发送失败：' + (r.data.error || '未知错误'))
  } catch {
    ElMessage.error('发送失败')
  } finally {
    testing.value = false
  }
}

onMounted(fetchConfig)
</script>

<style scoped>
.smtp-card {
  max-width: 720px;
}
</style>
