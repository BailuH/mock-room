<template>
  <div class="page-container">
    <div class="bg-blur-circle circle-1"></div>
    <div class="bg-blur-circle circle-2"></div>

    <el-card class="main-card" :body-style="{ padding: '0px' }">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <el-tab-pane label="个人资料" name="profile">
          <div class="pane-content profile-layout">
            
            <div class="avatar-column">
              <div class="avatar-upload-box" @click="triggerFileSelect">
                <img :src="localForm.avatarUrl" alt="Avatar" />
                <div class="upload-overlay">
                  <el-icon :size="24"><Camera /></el-icon>
                  <span>更换预览图</span>
                </div>
              </div>
              <p class="hint-text">点击修改预览，保存后正式生效</p>
            </div>

            <div class="form-column">
              <el-form label-position="top">
                <el-form-item label="昵称">
                  <el-input v-model="localForm.username" placeholder="设置您的昵称" />
                </el-form-item>
                <el-form-item label="电子邮箱">
                  <el-input v-model="localForm.email" placeholder="example@mail.com" />
                </el-form-item>
                <el-form-item label="手机号码">
                  <el-input v-model="localForm.phone" placeholder="输入11位手机号" disabled />
                </el-form-item>

                <div class="action-footer">
                  <el-button type="primary" class="btn-save" :loading="isSaving" @click="handleFinalSave">
                    保存更改
                  </el-button>
                  <el-button class="btn-reset" @click="resetLocalData">取消修改</el-button>
                </div>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="安全设置" name="security">
          <div class="pane-content security-layout">
            <div class="security-card">
              <div class="sec-header">
                <span class="sec-label">账户安全等级</span>
                <span class="sec-status" :class="securityStatus">{{ securityStatusText }}</span>
              </div>
              <el-progress 
                :percentage="userStore.security.level" 
                :status="securityStatus"
                :stroke-width="10"
                striped
              />
            </div>

            <div class="security-list">
              <div class="sec-item">
                <div class="sec-info">
                  <h4>账号密码</h4>
                  <p>保障账户安全，建议定期更换高强度密码</p>
                </div>
                <el-button text type="primary">修改密码</el-button>
              </div>
              <div class="sec-item">
                <div class="sec-info">
                  <h4>登录设备管理</h4>
                  <p>当前共有 2 台受信任设备正在使用</p>
                </div>
                <el-button text type="primary">查看详情</el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="cropVisible" title="裁剪预览图" width="440px" center destroy-on-close>
      <div class="cropper-wrapper">
        <div class="canvas-box">
          <canvas ref="canvasRef" class="main-canvas"></canvas>
          <div class="crop-frame" :style="cropBoxStyle" @mousedown="initDrag"></div>
        </div>
        <div class="zoom-slider">
          <el-icon><ZoomOut /></el-icon>
          <el-slider v-model="zoomScale" :min="0.5" :max="2" :step="0.01" />
          <el-icon><ZoomIn /></el-icon>
        </div>
      </div>
      <template #footer>
        <el-button @click="cropVisible = false">取消</el-button>
        <el-button type="primary" @click="applyCrop">应用预览</el-button>
      </template>
      <input ref="fileInput" type="file" accept="image/*" hidden @change="onFilePicked" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { useUserStore } from '@/tools/useUserStore';
import { Camera, ZoomIn, ZoomOut } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const userStore = useUserStore();
const activeTab = ref('profile');
const isSaving = ref(false);

// 1. 本地临时状态 (Local State)
const localForm = reactive({
  username: '',
  email: '',
  phone: '',
  avatarUrl: ''
});

// 初始化：从 Store 拷贝数据到本地
const resetLocalData = () => {
  Object.assign(localForm, { ...userStore.form });
};

onMounted(resetLocalData);

// 2. 保存逻辑
const handleFinalSave = () => {
  isSaving.value = true;
  // 模拟请求延迟
  setTimeout(() => {
    userStore.saveGlobalInfo({ ...localForm });
    isSaving.value = false;
    ElMessage.success({ message: '个人信息保存成功', plain: true });
  }, 600);
};

// 3. 安全状态计算
const securityStatus = computed(() => userStore.security.level > 80 ? 'success' : 'warning');
const securityStatusText = computed(() => userStore.security.level > 80 ? '高' : '一般');

// 4. 头像裁剪核心逻辑
const cropVisible = ref(false);
const fileInput = ref(null);
const canvasRef = ref(null);
const zoomScale = ref(1);
const sourceImage = new Image();
const cropState = reactive({ x: 75, y: 75, size: 150 });

const cropBoxStyle = computed(() => ({
  left: `${cropState.x}px`,
  top: `${cropState.y}px`,
  width: `${cropState.size}px`,
  height: `${cropState.size}px`,
}));

const triggerFileSelect = () => {
  cropVisible.value = true;
  setTimeout(() => fileInput.value?.click(), 100);
};

const onFilePicked = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => sourceImage.src = reader.result;
  reader.readAsDataURL(file);
};

sourceImage.onload = () => refreshCanvas();
watch(zoomScale, refreshCanvas);

function refreshCanvas() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  // 这里的 size 建议与 cropState 保持逻辑一致，通常为容器宽度
  canvas.width = 300;
  canvas.height = 300;
  ctx.clearRect(0, 0, 300, 300);

  // 修复：直接使用 zoomScale.value
  const w = sourceImage.width * zoomScale.value;
  const h = sourceImage.height * zoomScale.value;
  
  ctx.drawImage(sourceImage, (300 - w) / 2, (300 - h) / 2, w, h);
}

// 拖拽逻辑
let isDragging = false;
let startOffset = { x: 0, y: 0 };
const initDrag = (e) => {
  isDragging = true;
  startOffset.x = e.clientX - cropState.x;
  startOffset.y = e.clientY - cropState.y;
  document.addEventListener('mousemove', handleDragging);
  document.addEventListener('mouseup', stopDragging);
};
const handleDragging = (e) => {
  if (!isDragging) return;
  cropState.x = Math.max(0, Math.min(300 - cropState.size, e.clientX - startOffset.x));
  cropState.y = Math.max(0, Math.min(300 - cropState.size, e.clientY - startOffset.y));
};
const stopDragging = () => {
  isDragging = false;
  document.removeEventListener('mousemove', handleDragging);
  document.removeEventListener('mouseup', stopDragging);
};

const applyCrop = () => {
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = cropState.size;
  tempCanvas.height = cropState.size;
  const tCtx = tempCanvas.getContext('2d');
  tCtx.drawImage(canvasRef.value, cropState.x, cropState.y, cropState.size, cropState.size, 0, 0, cropState.size, cropState.size);
  
  // 只更新本地预览地址
  localForm.avatarUrl = tempCanvas.toDataURL('image/png');
  cropVisible.value = false;
};
</script>

<style scoped>
/* ========== 全局背景与容器 ========== */
.page-container {
  --text-main: #1d1d1f;
  --text-dim: #86868b;
  --accent: #0071e3;
  --card-bg: rgba(255, 255, 255, 0.85);
  --border-subtle: rgba(0, 0, 0, 0.08);

  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f2f2f7;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.bg-blur-circle {
  position: absolute;
  filter: blur(80px);
  z-index: 0;
  border-radius: 50%;
  opacity: 0.15;
}
.circle-1 { width: 400px; height: 400px; background: #0071e3; top: -100px; right: -50px; }
.circle-2 { width: 300px; height: 300px; background: #a855f7; bottom: -50px; left: -50px; }

/* ========== 主卡片设计 ========== */
.main-card {
  width: 90%;
  max-width: 880px;
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid var(--border-subtle);
  z-index: 1;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.05);
  transform: translateY(-60px);
}

.profile-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 20px 40px 0;
}
.profile-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }

.pane-content { padding: 40px; }
/* ========== 个人资料布局 ========== */
.profile-layout {
  display: flex;
  gap: 60px;
}

.avatar-column {
  flex: 0 0 160px;
  text-align: center;
}

.avatar-upload-box {
  width: 160px;
  height: 160px;
  border-radius: 38px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  background: #fff;
  border: 1px solid var(--border-subtle);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.avatar-upload-box:hover { transform: scale(1.02); }
.avatar-upload-box img { width: 100%; height: 100%; object-fit: cover; }

.upload-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  font-size: 15px; /* 原13px -> 调大至15px */
}
.avatar-upload-box:hover .upload-overlay { opacity: 1; }

.hint-text { 
  font-size: 14px; /* 原12px -> 调大至14px */
  color: var(--text-dim); 
  margin-top: 15px; 
  line-height: 1.5; /* 微调行高以适应大字体 */
}

.form-column { flex: 1; }
.form-column :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-main);
  font-size: 16px; /* 原14px -> 调大至16px */
}
.form-column :deep(.el-input__wrapper) {
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.6);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08) inset;
  font-size: 16px; /* 新增：确保输入框文字也同步变大 */
}

.action-footer {
  margin-top: 40px;
  display: flex;
  gap: 12px;
}
.btn-save { 
  padding: 12px 30px; 
  border-radius: 12px; 
  font-weight: 600; 
  background: var(--text-main); 
  border: none; 
  font-size: 16px; /* 新增：按钮文字调大 */
}
.btn-reset { 
  border-radius: 12px; 
  font-size: 16px; /* 新增：按钮文字调大 */
}

/* ========== 安全设置布局 ========== */
.security-layout { max-width: 600px; }
.security-card {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 30px;
}
.sec-header { display: flex; justify-content: space-between; margin-bottom: 12px; align-items: center; }
.sec-label { 
  font-weight: 600; 
  font-size: 18px; /* 原15px -> 调大至18px */
}
.sec-status { 
  font-size: 14px; /* 原12px -> 调大至14px */
  padding: 4px 14px; /* 微调内边距适应字体 */
  border-radius: 20px; 
  font-weight: 700; 
}
.sec-status.success { background: #e3f9eb; color: #10b981; }
.sec-status.warning { background: #fff5e6; color: #f59e0b; }

.sec-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 0; /* 微调间距 */
  border-bottom: 1px solid var(--border-subtle);
}
.sec-info h4 { 
  margin: 0 0 6px; 
  font-size: 17px; /* 原15px -> 调大至17px */
  color: var(--text-main); 
}
.sec-info p { 
  margin: 0; 
  font-size: 14px; /* 原13px -> 调大至14px */
  color: var(--text-dim); 
}

/* ========== 裁剪弹窗样式 ========== */
.cropper-wrapper { display: flex; flex-direction: column; align-items: center; }
.canvas-box { position: relative; border-radius: 12px; overflow: hidden; background: #f0f0f0; border: 1px solid #ddd; }
.crop-frame {
  position: absolute;
  border: 2px solid var(--accent);
  border-radius: 20px;
  box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.4);
  cursor: move;
}
.zoom-slider { display: flex; align-items: center; width: 80%; gap: 15px; margin-top: 25px; }
</style>