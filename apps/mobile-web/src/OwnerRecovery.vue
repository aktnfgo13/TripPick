<script setup lang="ts">
import { ref } from "vue";
import { api } from "./api";
const props = defineProps<{ ownerTrip?: string }>();
const emit = defineEmits<{ recovered: [id: string] }>();
const trip = ref(""),
  code = ref(""),
  message = ref(""),
  issued = ref("");
async function submit() {
  try {
    if (props.ownerTrip)
      issued.value = (
        await api<{ code: string }>(
          "/trips/" + props.ownerTrip + "/recovery/issue",
          "POST",
        )
      ).code;
    else
      emit(
        "recovered",
        (
          await api<{ tripId: string }>(
            "/trips/" + encodeURIComponent(trip.value.trim()) + "/recovery",
            "POST",
            { code: code.value },
          )
        ).tripId,
      );
    message.value = "";
  } catch (e) {
    message.value = String(e);
  }
}
</script>
<template>
  <details>
    <summary>관리자 소유권 복구</summary>
    <form @submit.prevent="submit">
      <template v-if="ownerTrip"
        ><p>
          여행 ID와 일회용 코드를 따로 보관하세요. 재발급하면 이전 코드는
          만료됩니다.
        </p>
        <p>{{ ownerTrip }}</p>
        <output>{{ issued }}</output></template
      >
      <template v-else
        ><label>여행 ID <input v-model="trip" required /></label
        ><label
          >복구 코드 <input type="password" v-model="code" required /></label
      ></template>
      <button>{{ ownerTrip ? "복구 코드 발급" : "소유권 복구" }}</button>
      <p role="status">{{ message }}</p>
    </form>
  </details>
</template>
