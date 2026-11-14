<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, ApiError } from "./api";
import OwnerRecovery from "./OwnerRecovery.vue";
import TripRoom from "./TripRoom.vue";
import ServerStatus from "./ServerStatus.vue";
const params = new URLSearchParams(location.hash.slice(1));
const token = ref(params.get("invite") || ""),
  pair = params.get("pair") || "",
  target = params.get("trip") || "";
const id = ref(""),
  nickname = ref(""),
  title = ref(""),
  error = ref(""),
  busy = ref(false);
function recovered(tid: string) {
  enter(tid);
  window.location.reload();
}
function enter(trip: string) {
  localStorage.setItem("trip", trip);
  history.replaceState(null, "", location.pathname);
  id.value = trip;
}
function networkError(e: unknown) {
  return e instanceof ApiError ? e.message : "서버에 연결하지 못했습니다. 네트워크를 확인하고 다시 시도하세요.";
}
async function lookup() {
  if (busy.value) return;
  title.value = ""; error.value = ""; busy.value = true;
  try { title.value = (await api<{title: string}>("/invite", "POST", {token: token.value.trim()})).title; }
  catch (e) { error.value = networkError(e); }
  finally { busy.value = false; }
}
async function join() {
  busy.value = true;
  try {
    const r = await api<{ tripId: string }>("/join", "POST", {
      token: token.value.trim(),
      nickname: nickname.value,
    });
    enter(r.tripId);
  } catch (e) {
    error.value = networkError(e);
  } finally {
    busy.value = false;
  }
}
async function confirmPair() {
  if (busy.value) return;
  busy.value = true;
  try {
    await api("/trips/" + target + "/vehicle-session/actor", "PUT", {
      token: pair,
    });
    enter(target);
  } catch (e) {
    error.value = networkError(e);
  } finally {busy.value = false;}
}
onMounted(async () => {
  try {
    if (token.value) await lookup();
    else if (!pair && !params.has("invite")) id.value = localStorage.getItem("trip") || "";
  } catch (e) {
    error.value = networkError(e);
  }
});
</script>
<template>
  <main>
    <p v-if="error" role="alert">{{ error }}</p>
    <TripRoom v-if="id" :id="id" />
    <section v-else-if="pair">
      <h1>차량에 내 계정 연결</h1>
      <p>연결 후 차량의 좋아요가 내 이름으로 기록됩니다.</p>
      <button :disabled="busy" @click="confirmPair">연결 확인</button>
    </section>
    <form v-else-if="title" @submit.prevent="join">
      <h1>{{ title || "여행 초대" }}</h1>
      <p>참여하면 이 여행에 사진을 올리고 좋아요를 남길 수 있어요.</p>
      <label>닉네임 <input required maxlength="80" v-model="nickname" /></label
      ><button :disabled="busy || !title">여행 참여</button>
    </form>
    <section v-else>
      <h1>TripPick 여행 참여</h1>
      <form @submit.prevent="lookup"><label>차량 화면의 참여 코드
        <input v-model.trim="token" required autocomplete="off" autocapitalize="none" spellcheck="false" /></label>
        <button :disabled="busy">{{ busy ? '초대 확인 중…' : '초대 확인' }}</button>
      </form><ServerStatus />
    </section><OwnerRecovery
      v-if="!id && !pair && !title"
      @recovered="recovered"
    />
  </main>
</template>
<style>
body {
  margin: 0;
  background: #f5f7f4;
  color: #183c35;
  font-family: system-ui, sans-serif;
}
main {
  max-width: 58rem;
  margin: auto;
  padding: 1.3rem;
}
section,
article,
form {
  background: white;
  padding: 1rem;
  border-radius: 12px;
  margin-block: 0.8rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.7rem;
}
.grid img {
  width: 100%;
  aspect-ratio: 4/3;
  object-fit: cover;
}
button,
input {
  font: inherit;
  padding: 0.55rem;
}
button {
  cursor: pointer;
}
li {
  margin: 0.5rem;
}
button, input:not([type=checkbox]):not([type=radio]), .grid a { min-height:44px; box-sizing:border-box }
button { border:1px solid #397168; border-radius:8px; background:white; color:#12473d }
form button, button[aria-pressed=true] { background:#165b50; color:white }
button:disabled { opacity:.6 } button:active { background:#d2e6df }
label { display:inline-block; max-width:100% } input { max-width:100% }
h1,h2,p,li { overflow-wrap:anywhere } .grid a { display:inline-flex; align-items:center; color:#085648 }
@media(max-width:480px){main{padding:.75rem}section,article,form{padding:.75rem}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
main { line-height:1.55 }
h1,h2 { line-height:1.25; letter-spacing:-.035em }
h1 { font-size:clamp(1.65rem,5vw,2.4rem) }
main > section, main > form { border:1px solid #ceded8; padding:clamp(1rem,3vw,2rem) }
main > section > form, main > form { display:grid; gap:.8rem }
main > form label, main > section > form label { display:grid; gap:.35rem; font-weight:600 }
input:not([type=checkbox]):not([type=radio]) { border:1px solid #728980; border-radius:8px }
:focus-visible { outline:3px solid #236bc2; outline-offset:3px }
[role=alert] { padding:.75rem 1rem; border-left:4px solid #963b22; background:#fff3ec; color:#74290f }
</style>
