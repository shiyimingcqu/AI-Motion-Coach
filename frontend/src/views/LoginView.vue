<template>
  <div class="login-page">
    <Aurora
      :colorStops="['#7cff67', '#B497CF', '#5227FF']"
      :amplitude="1.4"
      :blend="0.5"
      :speed="0.7"
    />

    <!-- 项目名称 + 标题 -->
    <div class="login-header">
      <SplitText
        text="姿态棱镜"
        tag="h1"
        className="brand-title"
        :delay="70"
        :duration="0.8"
        :from="{ opacity: 0, y: 60 }"
        :to="{ opacity: 1, y: 0 }"
        splitType="chars"
        textAlign="center"
      />
      <SplitText
        text="运动姿态评估与纠错系统"
        tag="p"
        className="brand-sub"
        :delay="25"
        :duration="0.5"
        :from="{ opacity: 0, y: 20 }"
        :to="{ opacity: 1, y: 0 }"
        splitType="words"
        textAlign="center"
      />
      <TextType
        :text="['看见每一度偏差', '让每次抬手都有意义', '练对 · 比练多更重要']"
        :typingSpeed="60"
        :deletingSpeed="25"
        :pauseDuration="2000"
        :initialDelay="1500"
        :showCursor="true"
        cursorCharacter="▍"
        as="p"
        className="slogan-typing"
      />
    </div>

    <!-- 登录 / 注册 切换 -->
    <div class="mode-bar">
      <button :class="['mode-btn', { on: mode === 'login' }]" @click="switchTo('login')">登录</button>
      <button :class="['mode-btn', { on: mode === 'reg' }]" @click="switchTo('reg')">注册</button>
    </div>

    <!-- ===== 登录 Stepper (2步) ===== -->
    <Stepper
      v-if="mode === 'login'"
      :key="'login'"
      :start="1"
      bk="← 上一步"
      nx="下一步 →"
      fn="登  录"
      :ld="busy"
      @finish="submit"
    >
      <div class="page">
        <h2 class="pg-title">欢迎回来</h2>
        <p class="pg-desc">请输入用户名。</p>
        <div class="field">
          <label>用户名</label>
          <input v-model="login.user" type="text" placeholder="admin" autocomplete="off" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">输入密码</h2>
        <p class="pg-desc"><strong>{{ login.user }}</strong>，请输入密码。</p>
        <div class="field">
          <label>密码</label>
          <input v-model="login.pass" type="password" placeholder="••••••••" autocomplete="off" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
      </div>
    </Stepper>

    <!-- ===== 注册 Stepper (3步) ===== -->
    <Stepper
      v-if="mode === 'reg'"
      :key="'reg'"
      :start="1"
      bk="← 上一步"
      nx="下一步 →"
      fn="注  册"
      :ld="busy"
      @finish="submit"
    >
      <div class="page">
        <h2 class="pg-title">创建账号</h2>
        <p class="pg-desc">选择一个用户名。</p>
        <div class="field">
          <label>用户名</label>
          <input v-model="reg.user" type="text" placeholder="3~32个字符" minlength="3" autocomplete="off" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">设置密码</h2>
        <p class="pg-desc">至少6个字符。</p>
        <div class="field">
          <label>密码</label>
          <input v-model="reg.pass" type="password" placeholder="创建密码" minlength="6" autocomplete="new-password" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">最后一步</h2>
        <p class="pg-desc">确认密码并选择角色。</p>
        <div class="field">
          <label>确认密码</label>
          <input v-model="reg.confirm" type="password" placeholder="再次输入密码" autocomplete="new-password" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
        <div class="field">
          <label>账号类型</label>
          <div class="roles">
            <label class="role" :class="{ sel: reg.role === 'user' }">
              <input v-model="reg.role" type="radio" value="user" />
              <span>用户</span>
            </label>
            <label class="role" :class="{ sel: reg.role === 'admin' }">
              <input v-model="reg.role" type="radio" value="admin" />
              <span>管理员</span>
            </label>
          </div>
        </div>
      </div>
    </Stepper>

    <!-- 状态提示 -->
    <Transition name="fade">
      <div v-if="msg" class="toast" :class="msgType">{{ msg }}</div>
    </Transition>

    <!-- 默认账号提示 -->
    <div class="hint">
      默认账号：<strong>admin / admin123</strong>（管理员）&nbsp;·&nbsp;
      <strong>user / user123</strong>（普通用户）
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Aurora from '@/components/Aurora.vue';
import Stepper from '@/components/Stepper.vue';
import SplitText from '@/components/SplitText.vue';
import TextType from '@/components/TextType.vue';

const router = useRouter();
const auth = useAuthStore();

const mode = ref('login');
const busy = ref(false);
const msg = ref('');
const msgType = ref<'err'|'ok'>('err');
let timer: ReturnType<typeof setTimeout> | null = null;

const login = reactive({ user: '', pass: '' });
const reg   = reactive({ user: '', pass: '', confirm: '', role: 'user' as 'user'|'admin' });

// 防止浏览器自动填充：密码框初始 readonly，聚焦后解除
const passReadonly = ref(true);

function onPassFocus() {
  passReadonly.value = false;
}

// 每次进入页面重置 readonly 状态
onMounted(() => {
  passReadonly.value = true;
  login.pass = '';
  reg.pass = '';
  reg.confirm = '';
});

function flash(text: string, type: 'err'|'ok') {
  if (timer) clearTimeout(timer);
  msg.value = text; msgType.value = type;
  timer = setTimeout(() => msg.value = '', 4000);
}

function switchTo(m: string) {
  mode.value = m; msg.value = '';
  login.user = ''; login.pass = '';
  reg.user = ''; reg.pass = ''; reg.confirm = ''; reg.role = 'user';
  passReadonly.value = true;
}

async function submit() {
  if (busy.value) return;

  if (mode.value === 'login') {
    if (!login.user || !login.pass) { flash('请填写所有字段。', 'err'); return; }
    busy.value = true;
    try {
      const u = await auth.login(login.user, login.pass);
      router.push(u.role === 'admin' ? '/rules' : '/');
    } catch (e: any) { flash(e.message || '用户名或密码错误。', 'err');
    } finally { busy.value = false; }
  } else {
    if (!reg.user || !reg.pass || !reg.confirm) { flash('请填写所有字段。', 'err'); return; }
    if (reg.pass !== reg.confirm) { flash('两次密码输入不一致。', 'err'); return; }
    if (reg.pass.length < 6) { flash('密码至少6个字符。', 'err'); return; }
    busy.value = true;
    try {
      await auth.register(reg.user, reg.pass, reg.role);
      flash('账号创建成功！请登录。', 'ok');
      setTimeout(() => { switchTo('login'); msg.value = ''; login.user = reg.user; }, 1200);
    } catch (e: any) { flash(e.message || '注册失败。', 'err');
    } finally { busy.value = false; }
  }
}
</script>

<style scoped>
.login-page {
  position: relative; min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 2rem;
  background: #0a0a0f; padding: 24px; overflow: hidden;
}

/* ─── 首页头部 ─── */
.login-header {
  position: relative; z-index: 2;
  display: flex; flex-direction: column; align-items: center; gap: 1rem;
}

.login-header :deep(.brand-title) {
  font-size: 4rem;
  font-weight: 800;
  color: #f0eeeb;
  letter-spacing: 0.12em;
  margin: 0;
  line-height: 1.1;
}

.login-header :deep(.brand-sub) {
  font-size: 1.05rem;
  color: rgba(255, 255, 255, 0.35);
  margin: 0;
  letter-spacing: 0.18em;
  font-weight: 400;
}

.login-header :deep(.slogan-typing) {
  font-size: 1.15rem;
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
  letter-spacing: 0.06em;
  font-weight: 400;
  min-height: 1.6em;
}

/* ─── 模式切换 ─── */
.mode-bar {
  position: relative; z-index: 2; display: flex;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 9999px; padding: 3px;
}
.mode-btn {
  font: inherit; font-size: 0.8125rem; font-weight: 500;
  padding: 0.5rem 1.25rem; border: none; border-radius: 9999px;
  background: transparent; color: rgba(255,255,255,0.4);
  cursor: pointer; transition: all 0.25s; letter-spacing: 0.01em;
}
.mode-btn.on {
  background: linear-gradient(135deg, #5227ff, #6d3aff);
  color: #fff; box-shadow: 0 4px 14px rgba(82,39,255,0.35);
}
.mode-btn:not(.on):hover { color: rgba(255,255,255,0.7); }

/* ─── 步骤内容 ─── */
.page { display: flex; flex-direction: column; gap: 1rem; }

.pg-title {
  margin: 0; font-size: 1.5rem; font-weight: 700;
  color: #f0eeeb; letter-spacing: -0.02em;
}
.pg-desc {
  margin: 0; font-size: 0.9375rem; color: rgba(255,255,255,0.45);
}
.pg-desc strong { color: rgba(255,255,255,0.7); font-weight: 600; }

/* ─── 输入框 ─── */
.field { display: flex; flex-direction: column; gap: 0.5rem; }
.field label {
  font-size: 0.75rem; font-weight: 700;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase; letter-spacing: 0.06em;
}
.field input {
  width: 100%; padding: 0.875rem 1rem;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  color: #f0eeeb; font: inherit; font-size: 1rem;
  outline: none; transition: all 0.2s; box-sizing: border-box;
}
.field input::placeholder { color: rgba(255,255,255,0.15); }
.field input:focus {
  border-color: #5227ff;
  background: rgba(82,39,255,0.06);
  box-shadow: 0 0 0 3px rgba(82,39,255,0.1);
}

/* ─── 角色选择 ─── */
.roles { display: flex; gap: 0.75rem; }
.role { flex: 1; cursor: pointer; }
.role input { position: absolute; opacity: 0; pointer-events: none; }
.role span {
  display: flex; align-items: center; justify-content: center;
  padding: 0.75rem;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.5);
  font-size: 0.875rem; font-weight: 500; transition: all 0.2s;
}
.role.sel span {
  border-color: #5227ff;
  background: rgba(82,39,255,0.12);
  color: #f0eeeb;
}

/* ─── 状态提示 ─── */
.toast {
  position: relative; z-index: 2;
  padding: 0.75rem 1.25rem; border-radius: 10px;
  font-size: 0.8125rem; font-weight: 500;
  max-width: 28rem; width: 100%; text-align: center; box-sizing: border-box;
}
.toast.err { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #fca5a5; }
.toast.ok  { background: rgba(34,197,94,0.1);  border: 1px solid rgba(34,197,94,0.2);  color: #86efac;  }

/* ─── 底部提示 ─── */
.hint {
  position: relative; z-index: 2;
  font-size: 0.75rem; color: rgba(255,255,255,0.2); text-align: center;
  line-height: 1.5;
}
.hint strong { color: rgba(255,255,255,0.35); font-weight: 600; }

/* ─── 动画 ─── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
