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
        :text="$t('login.title')"
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
        :text="$t('login.subtitle')"
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
        :text="[$t('login.tagline1'), $t('login.tagline2'), $t('login.tagline3')]"
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
      <button :class="['mode-btn', { on: mode === 'login' }]" @click="switchTo('login')">{{ $t('login.login') }}</button>
      <button :class="['mode-btn', { on: mode === 'reg' }]" @click="switchTo('reg')">{{ $t('login.register') }}</button>
    </div>

    <!-- ===== 登录 Stepper (2步) ===== -->
    <Stepper
      v-if="mode === 'login'"
      :key="'login'"
      :start="1"
      :bk="$t('login.prevStep')"
      :nx="$t('login.nextStep')"
      :fn="$t('login.login')"
      :ld="busy"
      @finish="submit"
    >
      <div class="page">
        <h2 class="pg-title">{{ $t('login.welcome') }}</h2>
        <p class="pg-desc">{{ $t('login.enterUsername') }}</p>
        <div class="field">
          <label>{{ $t('common.username') }}</label>
          <input v-model="login.user" type="text" placeholder="admin" autocomplete="off" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">{{ $t('login.enterPassword') }}</h2>
        <p class="pg-desc"><strong>{{ login.user }}</strong>，{{ $t('login.enterPassword') }}</p>
        <div class="field">
          <label>{{ $t('common.password') }}</label>
          <input v-model="login.pass" type="password" placeholder="••••••••" autocomplete="off" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
      </div>
    </Stepper>

    <!-- ===== 注册 Stepper (3步) ===== -->
    <Stepper
      v-if="mode === 'reg'"
      :key="'reg'"
      :start="1"
      :bk="$t('login.prevStep')"
      :nx="$t('login.nextStep')"
      :fn="$t('login.register')"
      :ld="busy"
      @finish="submit"
    >
      <div class="page">
        <h2 class="pg-title">{{ $t('login.createAccount') }}</h2>
        <p class="pg-desc">{{ $t('login.chooseUsername') }}</p>
        <div class="field">
          <label>{{ $t('common.username') }}</label>
          <input v-model="reg.user" type="text" :placeholder="$t('login.usernamePlaceholder')" minlength="3" autocomplete="off" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">{{ $t('login.setPassword') }}</h2>
        <p class="pg-desc">{{ $t('login.minChars') }}</p>
        <div class="field">
          <label>{{ $t('common.password') }}</label>
          <input v-model="reg.pass" type="password" :placeholder="$t('login.passwordPlaceholder')" minlength="6" autocomplete="new-password" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
      </div>
      <div class="page">
        <h2 class="pg-title">{{ $t('login.lastStep') }}</h2>
        <p class="pg-desc">{{ $t('login.confirmAndRole') }}</p>
        <div class="field">
          <label>{{ $t('login.confirmPassword') }}</label>
          <input v-model="reg.confirm" type="password" :placeholder="$t('login.confirmPlaceholder')" autocomplete="new-password" :readonly="passReadonly" @focus="onPassFocus" />
        </div>
        <div class="field">
          <label>{{ $t('login.accountType') }}</label>
          <div class="roles">
            <label class="role" :class="{ sel: reg.role === 'user' }">
              <input v-model="reg.role" type="radio" value="user" />
              <span>{{ $t('login.user') }}</span>
            </label>
            <label class="role" :class="{ sel: reg.role === 'admin' }">
              <input v-model="reg.role" type="radio" value="admin" />
              <span>{{ $t('login.admin') }}</span>
            </label>
          </div>
        </div>
      </div>
    </Stepper>

    <!-- 微信登录 -->
    <div class="wechat-login-row">
      <button class="wechat-login-btn" type="button" @click="showWechatLogin = true">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.045c.134 0 .24-.11.24-.245 0-.06-.024-.12-.04-.178l-.325-1.233a.492.492 0 0 1 .177-.554C23.028 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-7.062-6.122zm-2.18 2.908c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982z"/>
        </svg>
        <span>微信登录</span>
      </button>
    </div>

    <!-- 状态提示 -->
    <Transition name="fade">
      <div v-if="msg" class="toast" :class="msgType">{{ msg }}</div>
    </Transition>

    <!-- 微信登录弹窗 -->
    <WechatLoginModal v-if="showWechatLogin" @close="showWechatLogin = false" />

    <!-- 默认账号提示 -->
    <div class="hint">
      {{ $t('login.defaultAccounts') }}<strong>admin / admin123</strong>（{{ $t('login.admin') }}）&nbsp;·&nbsp;
      <strong>user / user123</strong>（{{ $t('login.user') }}）
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import Aurora from '@/components/Aurora.vue';
import Stepper from '@/components/Stepper.vue';
import SplitText from '@/components/SplitText.vue';
import TextType from '@/components/TextType.vue';
import WechatLoginModal from '@/components/WechatLoginModal.vue';

const { t } = useI18n();
const router = useRouter();
const auth = useAuthStore();

const mode = ref('login');
const busy = ref(false);
const msg = ref('');
const msgType = ref<'err'|'ok'>('err');
const showWechatLogin = ref(false);
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
    if (!login.user || !login.pass) { flash(t('login.fillAll'), 'err'); return; }
    busy.value = true;
    try {
      const u = await auth.login(login.user, login.pass);
      router.push(u.role === 'admin' ? '/rules' : '/');
    } catch (e: any) { flash(e.message || t('login.wrongCredentials'), 'err');
    } finally { busy.value = false; }
  } else {
    if (!reg.user || !reg.pass || !reg.confirm) { flash(t('login.fillAll'), 'err'); return; }
    if (reg.pass !== reg.confirm) { flash(t('login.passwordMismatch'), 'err'); return; }
    if (reg.pass.length < 6) { flash(t('login.passwordTooShort'), 'err'); return; }
    busy.value = true;
    try {
      await auth.register(reg.user, reg.pass, reg.role);
      flash(t('login.registerSuccess'), 'ok');
      setTimeout(() => { switchTo('login'); msg.value = ''; login.user = reg.user; }, 1200);
    } catch (e: any) { flash(e.message || t('login.registerFailed'), 'err');
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

/* ─── 微信登录 ─── */
.wechat-login-row {
  position: relative; z-index: 2;
  display: flex; justify-content: center;
}
.wechat-login-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 28px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.wechat-login-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
  border-color: rgba(255,255,255,0.2);
}
.wechat-login-btn svg { color: #22c55e; }

/* ─── 动画 ─── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
