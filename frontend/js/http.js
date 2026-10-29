/** Shared transport for the RAG screen and authenticated API wrapper.
 * ApiError carries safe diagnostics; neither bodies nor tokens are logged.
 */
export class ApiError extends Error {
  constructor(message, { code = "RequestFailed", status = 0, requestId = null, issues = [] } = {}) {
    super(message);
    this.name = "ApiError";
    Object.assign(this, { code, status, requestId, issues });
  }
}

export function formatApiError(error) {
  if (!(error instanceof ApiError)) return "요청 처리 중 오류가 발생했습니다. 다시 시도해 주세요.";
  const first = error.issues[0];
  const detail = first ? ` (${first.field}: ${first.message})` : "";
  const reference = error.requestId ? ` [요청 ID: ${error.requestId}]` : "";
  return error.message + detail + reference;
}

export async function requestJSON(url, { timeoutMs = 90000, ...options } = {}) {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  if (options.signal?.aborted) cancel();
  options.signal?.addEventListener("abort", cancel, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  let response;
  try {
    response = await fetch(url, { ...options, signal: controller.signal });
    const requestId = response.headers.get("X-Request-ID");
    let envelope;
    try {
      envelope = await response.json();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      throw new ApiError("서버 응답 형식이 올바르지 않습니다. 서버 주소와 배포 상태를 확인해 주세요.",
        { code: "InvalidResponse", status: response.status, requestId });
    }
    if (!envelope || typeof envelope.ok !== "boolean") {
      throw new ApiError("서버 응답 계약이 맞지 않습니다. API의 Envelope 형식을 확인해 주세요.",
        { code: "InvalidResponse", status: response.status, requestId });
    }
    if (!response.ok || !envelope.ok) {
      throw new ApiError(envelope.error?.message || "요청을 처리하지 못했습니다.", {
        code: envelope.error?.code || `HTTP${response.status}`, status: response.status,
        requestId: requestId || envelope.request_id,
        issues: Array.isArray(envelope.error?.issues) ? envelope.error.issues : [],
      });
    }
    if (!("data" in envelope)) {
      throw new ApiError("서버 응답에 data가 없습니다.",
        { code: "InvalidResponse", status: response.status, requestId });
    }
    return envelope.data;
  } catch (cause) {
    const error = cause instanceof ApiError ? cause : controller.signal.aborted
      ? new ApiError(timedOut ? "응답 시간이 길어지고 있습니다. 잠시 후 다시 시도해 주세요." : "요청이 취소되었습니다.",
        { code: timedOut ? "RequestTimeout" : "RequestCancelled" })
      : new ApiError("서버에 연결하지 못했습니다. 서버 실행·주소·CORS 설정을 확인해 주세요.",
        { code: "NetworkError" });
    // Share these fields with the backend developer; do not log the raw cause.
    console.error("[API]", { code: error.code, status: error.status, requestId: error.requestId });
    throw error;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }
}
