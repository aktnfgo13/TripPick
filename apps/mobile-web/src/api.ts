export type Member = { id: string; nickname: string; role: string };
export type Trip = {
  id: string;
  title: string;
  state: string;
  role: string;
  memberId: string;
  members: Member[];
  photoCount: number;
  revision: number;
};
export type Photo = {
  id: string;
  uploader: string;
  uploaderId: string;
  voteCount: number;
  myVote: number;
};
export type Album = {
  albumId: string | null;
  orderedPhotoIds: string[];
  coverPhotoId: string | null;
  revision: number;
};
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: signal ? AbortSignal.any([signal,AbortSignal.timeout(12000)]) : AbortSignal.timeout(12000),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "요청을 처리하지 못했습니다.",
    );
  return data;
}
export function sendPhoto(
  trip: string,
  file: File,
  key: string,
  progress: (value: number) => void,
) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/trips/" + trip + "/photos");
    xhr.timeout = 90000;
    xhr.setRequestHeader("Idempotency-Key", key);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) progress(Math.round((100 * e.loaded) / e.total));
    };
    xhr.onload = () =>
      xhr.status === 201
        ? resolve()
        : reject(new Error(xhr.response?.detail || "업로드 실패"));
    xhr.onerror = xhr.ontimeout = () =>
      reject(new Error("연결을 확인하고 다시 시도하세요."));
    xhr.responseType = "json";
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}
