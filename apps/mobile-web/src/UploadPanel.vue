<script setup lang="ts">
import { ref, onUnmounted } from "vue";
import { sendPhoto } from "./api";
const props = defineProps<{ trip: string }>();
const emit = defineEmits<{ done: [] }>();
type Item = {
  file: File;
  key: string;
  url: string;
  progress: number;
  state: string;
};
const items = ref<Item[]>([]);
async function upload(item: Item) {
  item.state = "전송 중";
  try {
    await sendPhoto(
      props.trip,
      item.file,
      item.key,
      (p) => (item.progress = p),
    );
    item.state = "완료";
    emit("done");
  } catch (e) {
    item.state = String(e);
  }
}
async function select(e: Event) {
  const input = e.target as HTMLInputElement;
  for (const file of Array.from(input.files || [])) {
    items.value.push({
      file,
      key: crypto.randomUUID(),
      url: URL.createObjectURL(file),
      progress: 0,
      state: "대기",
    });
    await upload(items.value[items.value.length - 1]);
  }
  input.value = "";
}
onUnmounted(() => items.value.forEach((i) => URL.revokeObjectURL(i.url)));
</script>
<template>
  <section>
    <h2>사진 올리기</h2>
    <label
      >JPEG·PNG 선택 (각 12 MiB 이하)
      <input
        type="file"
        accept="image/jpeg,image/png"
        multiple
        @change="select"
    /></label>
    <ul aria-live="polite">
      <li v-for="i in items" :key="i.key">
        <img :src="i.url" width="56" alt="" /> {{ i.file.name }} ·
        <progress :value="i.progress" max="100" aria-label="업로드 진행률"></progress> {{ i.progress }}% · {{ i.state }}
        <button
          v-if="!['완료', '전송 중', '대기'].includes(i.state)"
          @click="upload(i)"
        >
          재시도
        </button>
      </li>
    </ul>
  </section>
</template>
