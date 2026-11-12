<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "./api";
import OwnerRecovery from "./OwnerRecovery.vue";
import TripRoom from "./TripRoom.vue";
import ServerStatus from "./ServerStatus.vue";
const params = new URLSearchParams(location.hash.slice(1));
const token = params.get("invite") || "",
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
async function join() {
  busy.value = true;
  try {
    const r = await api<{ tripId: string }>("/join", "POST", {
      token,
      nickname: nickname.value,
    });
    enter(r.tripId);
  } catch (e) {
    error.value = String(e);
  } finally {
    busy.value = false;
  }
}
async function confirmPair() {
  try {
    await api("/trips/" + target + "/vehicle-session/actor", "PUT", {
      token: pair,
    });
    enter(target);
  } catch (e) {
    error.value = String(e);
  }
}
onMounted(async () => {
  try {
    if (token) {
      title.value = (
        await api<{ title: string }>("/invite", "POST", { token })
      ).title;
    } else if (!pair) id.value = localStorage.getItem("trip") || "";
  } catch (e) {
    error.value = String(e);
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
      <button @click="confirmPair">연결 확인</button>
    </section>
    <form v-else-if="token" @submit.prevent="join">
      <h1>{{ title || "여행 초대" }}</h1>
      <label>닉네임 <input required maxlength="80" v-model="nickname" /></label
      ><button :disabled="busy || !title">여행 참여</button>
    </form>
    <ServerStatus v-else /><OwnerRecovery
      v-if="!pair && !token"
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
</style>
