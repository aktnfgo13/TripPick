<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { api, ApiError, type Trip, type Photo, type Album } from "./api";
import OwnerRecovery from "./OwnerRecovery.vue";
import UploadPanel from "./UploadPanel.vue";
const controller = new AbortController();
const mapOpen = ref(false);
const visibleLimit = ref(40);
const props = defineProps<{ id: string }>();
const base = "/trips/" + props.id;
const trip = ref<Trip>(),
  photos = ref<Photo[]>([]),
  album = ref<Album>(),
  error = ref(""),
  mine = ref(false),
  working = ref(false);
const selected = ref<string[]>([]),
  cover = ref(""),
  editing = ref(false),
  editRevision = ref(0);
let timer: ReturnType<typeof setInterval>,
  loading = false,
  ws: WebSocket | undefined;
const media = (id: string, kind: string) =>
  "/api/v1" + base + "/photos/" + id + "/" + kind;
const visible = computed(() =>
  mine.value
    ? photos.value.filter((p) => p.uploaderId === trip.value?.memberId)
    : photos.value,
);
async function refresh() {
  if (loading) return;
  loading = true;
  try {
    const info = await api<Trip>(base, "GET", undefined, controller.signal),
      list: Photo[] = [];
    if (trip.value?.revision === info.revision && !error.value) return;
    let cursor = "";
    do {
      const page = await api<{ items: Photo[]; nextCursor: string | null }>(
        base + "/photos?cursor=" + cursor,
        "GET",
        undefined,
        controller.signal,
      );
      list.push(...page.items);
      cursor = page.nextCursor || "";
    } while (cursor);
    album.value = await api<Album>(
      base + "/album",
      "GET",
      undefined,
      controller.signal,
    );
    photos.value = list;
    trip.value = info;
    error.value = "";
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      trip.value = undefined;
      photos.value = [];
      album.value = undefined;
      error.value =
        "세션이 만료되었습니다. 참여 QR을 다시 열거나 관리자 복구 코드를 사용하세요.";
    } else if (!controller.signal.aborted) error.value = String(e);
  } finally {
    loading = false;
  }
}
async function act(fn: () => Promise<unknown>) {
  working.value = true;
  try {
    await fn();
    await refresh();
  } catch (e) {
    error.value = String(e);
  } finally {
    working.value = false;
  }
}
function edit() {
  selected.value = album.value?.albumId
    ? [...album.value.orderedPhotoIds]
    : photos.value.filter((p) => p.voteCount > 0).map((p) => p.id);
  cover.value = album.value?.coverPhotoId || selected.value[0] || "";
  editRevision.value = album.value?.revision || 0;
  editing.value = true;
}
async function save() {
  await act(async () => {
    await api(base + "/album", "PUT", {
      orderedPhotoIds: selected.value,
      coverPhotoId: selected.value.includes(cover.value)
        ? cover.value
        : selected.value[0],
      expectedRevision: editRevision.value,
    });
    editing.value = false;
  });
}
onMounted(() => {
  refresh();
  timer = setInterval(refresh, 5000);
  connectSocket();
});
let disposed = false;
let retry: ReturnType<typeof setTimeout>;
function connectSocket() {
  ws = new WebSocket(
    (location.protocol === "https:" ? "wss://" : "ws://") +
      location.host +
      "/api/v1" +
      base +
      "/events",
  );
  ws.onmessage = refresh;
  ws.onopen = refresh;
  ws.onclose = () => {
    if (!disposed) retry = setTimeout(connectSocket, 2000);
  };
}
onUnmounted(() => {
  disposed = true;
  controller.abort();
  clearTimeout(retry);
  clearInterval(timer);
  ws?.close();
});
</script>
<template>
  <p v-if="error" role="alert">
    {{ error }} <button @click="refresh">다시 조회</button>
  </p>
  <template v-if="trip"
    ><h1>{{ trip.title }}</h1>
    <p>
      {{ trip.state }} · {{ trip.members.map((m) => m.nickname).join(", ") }} ·
      사진 {{ trip.photoCount }}장
    </p>
    <button
      v-if="trip.role === 'owner' && ['ACTIVE', 'REVIEW'].includes(trip.state)"
      @click="
        act(() =>
          api(base, 'PATCH', {
            state: trip?.state === 'ACTIVE' ? 'REVIEW' : 'ACTIVE',
          }),
        )
      "
    >
      {{
        trip.state === "ACTIVE" ? "업로드 마감 · 검토 시작" : "업로드 다시 열기"
      }}
    </button>
    <button @click="mapOpen = !mapOpen">
      {{ mapOpen ? "지도 닫기" : "여행 지도" }}
    </button>
    <iframe
      v-if="mapOpen"
      :src="'/journal/?trip=' + encodeURIComponent(id)"
      title="여행 지도와 장소 편집"
      style="width: 100%; height: 70vh; border: 0"
    ></iframe>
    <OwnerRecovery v-if="trip.role === 'owner'" :owner-trip="id" />
    <UploadPanel v-if="trip.state === 'ACTIVE'" :trip="id" @done="refresh" />
    <h2>여행 사진</h2>
    <label><input type="checkbox" v-model="mine" /> 내 업로드만</label>
    <p v-if="!visible.length">아직 사진이 없습니다.</p>
    <div class="grid">
      <article v-for="p in visible.slice(0, visibleLimit)" :key="p.id">
        <img
          loading="lazy"
          :src="media(p.id, 'preview')"
          :alt="p.uploader + '의 사진'"
        />
        <p>{{ p.uploader }}</p>
        <button
          :disabled="working"
          :aria-pressed="!!p.myVote"
          @click="
            act(() =>
              api(
                base + '/photos/' + p.id + '/vote',
                p.myVote ? 'DELETE' : 'PUT',
              ),
            )
          "
        >
          {{ p.myVote ? "좋아요 취소" : "좋아요" }} {{ p.voteCount }}
        </button>
      </article>
    </div>
    <button v-if="visible.length > visibleLimit" @click="visibleLimit += 40">
      사진 더 보기
    </button>
    <h2>공유 앨범</h2>
    <p v-if="!album?.albumId">아직 확정된 앨범이 없습니다.</p>
    <div class="grid">
      <article v-for="pid in album?.orderedPhotoIds" :key="pid">
        <img loading="lazy" :src="media(pid, 'preview')" alt="앨범 사진" /><span
          v-if="pid === album?.coverPhotoId"
          >대표 사진 · </span
        ><a :href="media(pid, 'download')" download>다운로드</a>
      </article>
    </div>
    <button v-if="trip.role === 'owner' && !editing" @click="edit">
      앨범 편집
    </button>
    <section v-if="editing">
      <h2>최종 사진 선정</h2>
      <div v-for="p in photos" :key="p.id">
        <img
          loading="lazy"
          width="64"
          :src="media(p.id, 'preview')"
          alt=""
        /><label
          ><input type="checkbox" :value="p.id" v-model="selected" /> 포함 ·
          {{ p.uploader }}</label
        ><label
          ><input
            type="radio"
            v-model="cover"
            :value="p.id"
            :disabled="!selected.includes(p.id)"
          />
          표지</label
        >
      </div>
      <button :disabled="working || !selected.length" @click="save">
        앨범 확정</button
      ><button @click="editing = false">취소</button>
    </section>
  </template>
  <p v-else-if="!error">여행을 불러오는 중…</p>
</template>
