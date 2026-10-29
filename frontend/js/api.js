/**
 * API 요청 래퍼 — Core
 * JWT 자동 부착, Envelope 파싱, 오류 throw
 */
import { getToken } from "./auth.js";
import { ApiError, requestJSON } from "./http.js";
export { ApiError, formatApiError } from "./http.js";

const _BASE = (() => {
  const h = window.location.hostname;
  if (h === "localhost" || h === "127.0.0.1") return "http://localhost:8000";
  return window.__APP_CONFIG__?.apiBase ?? "";
})();

/**
 * @param {string} path
 * @param {RequestInit} options
 * @returns {Promise<any>} Envelope.data
 */
export async function request(path, options = {}) {
  let token;
  try {
    token = await getToken();
  } catch {
    throw new ApiError("로그인 상태를 확인하지 못했습니다. 다시 로그인해 주세요.", { code: "AuthSessionError" });
  }
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers ?? {}),
  };

  return requestJSON(`${_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

}

// ── 편의 함수 ──────────────────────────────────────
export const get  = (path, opts = {}) => request(path, { method: "GET",    ...opts });
export const post = (path, body, opts = {}) => request(path, { method: "POST",   body, ...opts });
export const put  = (path, body, opts = {}) => request(path, { method: "PUT",    body, ...opts });
export const del  = (path, opts = {}) => request(path, { method: "DELETE",  ...opts });
