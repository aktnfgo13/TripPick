import { RegionMap } from "./renderer.js";
const $ = (s) => document.getElementById(s);
const params = new URLSearchParams(location.search),
  trip = params.get("trip"),
  vehicle = params.get("vehicle") === "1";
const base = "/api/v1/trips/" + encodeURIComponent(trip),
  stateKey = "journal-view/" + trip;
let region = "",
  place = "",
  features = [],
  data = { visits: [], links: [] },
  photos = [],
  info = {},
  renderer;
try {
  [region, place] = JSON.parse(localStorage.getItem(stateKey) || '["",""]');
} catch {}
async function request(path, method = "GET", body) {
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(12000),
  });
  if (!r.ok) throw Error((await r.json()).detail || "연결 실패");
  return r.json();
}
function button(text, fn) {
  const b = document.createElement("button");
  b.textContent = text;
  b.onclick = () => Promise.resolve().then(fn).catch(err);
  return b;
}
function err(e) {
  $("message").textContent = String(e);
}
function line(parent, text) {
  const p = document.createElement("p");
  p.textContent = text;
  parent.append(p);
}
function choose(r, p = "") {
  region = r;
  place = p;
  localStorage.setItem(stateKey, JSON.stringify([r, p]));
  render();
}
function statuses(status) {
  return (
    {
      CANDIDATE: "후보",
      ARRIVED: "도착 확인",
      CONFIRMED: "사용자 확인",
      EXCLUDED: "사용자 제외",
    }[status] || status
  );
}
function render() {
  const kept = data.visits.filter((v) => v.status !== "EXCLUDED");
  const places = Array.from(new Map(kept.map((v) => [v.place_id, v])).values());
  region = features.find((f) => f.properties.predecessors?.includes(region))?.properties.code || region;
  if (region && !features.some((f) => f.properties.code === region))
    region = "";
  renderer.draw(region, places);
  $("zoom").hidden = !region;
  $("heading").textContent =
    features.find((f) => f.properties.code === region)?.properties.name ||
    "대한민국";
  const choices = $("choices"),
    detail = $("detail");
  choices.replaceChildren();
  detail.replaceChildren();
  $("region-search").hidden = !!region;
  if (!region) {
    for (const f of features) {
      const p = f.properties,
        n = places.filter((v) => v.region_code === p.code).length;
      if (![p.name, ...(p.aliases || [])].some(name => name.includes($("query").value.trim()))) continue;
      choices.append(button(p.name + " " + n, () => choose(p.code)));
    }
    const unknown = places.filter((v) => !v.region_code);
    for (const v of unknown)
      choices.append(
        button("지역 미확인 · " + v.name, () => choose("", v.place_id)),
      );
  } else {
    const shown = places.filter((v) => v.region_code === region);
    for (const v of shown)
      choices.append(button(v.name, () => choose(region, v.place_id)));
    if (!shown.length) line(choices, "이 지역의 방문 기록이 없습니다.");
  }
  const visits = kept.filter((v) => v.place_id === place);
  if (visits.length) {
    const v = visits[0],
      ids = new Set(visits.map((x) => x.id));
    const links = data.links.filter((l) => ids.has(l.visit_id));
    line(
      detail,
      v.name + " · " + v.category + " · 사진 " + links.length + "장",
    );
    for (const l of links) {
      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = base + "/photos/" + l.photo_id + "/preview";
      img.alt = l.status === "CANDIDATE" ? "연결 후보 사진" : "장소 사진";
      detail.append(img);
    }
    const log = document.createElement("details"),
      title = document.createElement("summary");
    title.textContent = "여행일지";
    log.append(title);
    for (const visit of visits) {
      line(
        log,
        new Date(visit.observed_at).toLocaleString() +
          " · " +
          statuses(visit.status) +
          " · " +
          visit.source,
      );
      if (info.role === "owner" && !vehicle) {
        for (const [text, status] of [
          ["이름 수정·방문 확인", "CONFIRMED"],
          ["방문 제외", "EXCLUDED"],
        ])
          log.append(
            button(text, async () => {
              const name =
                status === "CONFIRMED"
                  ? prompt("장소명", visit.name)
                  : visit.name;
              if (!name) return;
              await request(base + "/visits/" + visit.id, "PATCH", {
                name,
                status,
              });
              await load();
            }),
          );
      }
    }
    detail.append(log);
  }
  $("manage").hidden = vehicle;
  $("newvisit").hidden = info.role !== "owner";
  $("photo").replaceChildren(
    ...photos
      .filter((p) => info.role === "owner" || p.uploaderId === info.memberId)
      .map((p) => {
        const link = data.links.find((l) => l.photo_id === p.id),
          v = data.visits.find((v) => v.id === link?.visit_id);
        return new Option(
          p.uploader +
            " · " +
            p.id.slice(0, 8) +
            " · " +
            (v ? v.name + " " + statuses(link.status) : "미분류"),
          p.id,
        );
      }),
  );
  $("visit").replaceChildren(
    new Option("연결 해제", ""),
    ...kept.map(
      (v) =>
        new Option(
          v.name + " · " + new Date(v.observed_at).toLocaleDateString(),
          v.id,
        ),
    ),
  );
}
async function load() {
  $("message").textContent = "불러오는 중…";
  info = await request(base);
  data = await request(base + "/journal");
  if (!vehicle) {
    photos = [];
    let cursor = "";
    do {
      const page = await request(base + "/photos?cursor=" + cursor);
      photos.push(...page.items);
      cursor = page.nextCursor;
    } while (cursor);
  }
  if (!renderer) {
    features = (await request("/api/v1/regions")).features;
    renderer = new RegionMap(
      $("map"),
      features,
      (r) => choose(r),
      (p) => choose(region, p),
    );
  }
  $("message").textContent = "";
  render();
}
$("query").oninput = render;
$("home").onclick = () => choose("");
$("plus").onclick = () => renderer?.zoom(0.7);
$("minus").onclick = () => renderer?.zoom(1 / 0.7);
$("refresh").onclick = () => load().catch(err);
$("newvisit").onsubmit = async (e) => {
  e.preventDefault();
  try {
    await request(base + "/visits", "POST", {
      name: $("name").value,
      category: $("category").value,
      districtCode: $("district").value || null,
      latitude: +$("lat").value,
      longitude: +$("lon").value,
      source: "MANUAL",
      kind: "CONFIRMED",
      key: crypto.randomUUID(),
      observedAt: new Date().toISOString(),
    });
    await load();
  } catch (e) {
    err(e);
  }
};
$("link").onclick = async () => {
  try {
    await request(base + "/photos/" + $("photo").value + "/place", "PUT", {
      visitId: $("visit").value || null,
    });
    await load();
  } catch (e) {
    err(e);
  }
};
load().catch(err);
