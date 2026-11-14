<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { checkHealth } from './health'

const state = ref<'loading'|'online'|'offline'>('loading')
async function refresh() {
  state.value = 'loading'
  state.value = await checkHealth() ? 'online' : 'offline'
}
onMounted(refresh)
</script>
<template>
  <aside>

    <p role="status">{{ {loading:'서버 연결 확인 중…', online:'여행 서버에 연결되었습니다.', offline:'여행 서버에 연결할 수 없습니다.'}[state] }}</p>
    <button v-if="state === 'offline'" @click="refresh">다시 연결</button>
  </aside>
</template>
<style scoped>
body { margin:0; background:#f3f6f3; color:#183c35; font-family:system-ui,sans-serif }
main { max-width:32rem; margin:15vh auto; padding:2rem }
button { padding:.75rem 1rem; font:inherit }
</style>
