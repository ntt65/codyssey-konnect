import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const source = readFileSync(new URL('../../frontend/js/http.js', import.meta.url), 'utf8');
const { requestJSON, ApiError, formatApiError } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const fetchOriginal = globalThis.fetch;

async function withFetch(fetch, run) {
  globalThis.fetch = fetch;
  try { await run(); } finally { globalThis.fetch = fetchOriginal; }
}

test('successful envelope unwraps Topic data', async () => {
  await withFetch(async () => Response.json({ ok: true, data: { total: 1 } }), async () => {
    assert.deepEqual(await requestJSON('/api/topic/discover'), { total: 1 });
  });
});

test('API errors keep status, code, field issues and request ID', async () => {
  await withFetch(async () => Response.json({ ok: false, error: {
    code: 'ValidationError', message: 'Check input',
    issues: [{ field: 'body.question', message: 'Too long' }],
  } }, { status: 422, headers: { 'X-Request-ID': 'request-123' } }), async () => {
    await assert.rejects(requestJSON('/api/ask'), error => {
      assert.equal(error.status, 422);
      assert.equal(error.code, 'ValidationError');
      assert.match(formatApiError(error), /body.question/);
      assert.match(formatApiError(error), /request-123/);
      return true;
    });
  });
});

test('non-JSON proxy errors preserve status and reference', async () => {
  await withFetch(async () => new Response('<h1>Bad gateway</h1>', {
    status: 502, headers: { 'X-Request-ID': 'proxy-123' },
  }), async () => {
    await assert.rejects(requestJSON('/api/ask'), error =>
      error.code === 'InvalidResponse' && error.status === 502 && error.requestId === 'proxy-123');
  });
});

test('old raw response contract is reported explicitly', async () => {
  await withFetch(async () => Response.json({ total: 1 }), async () => {
    await assert.rejects(requestJSON('/api/topic/discover'), error => error.code === 'InvalidResponse');
  });
});

test('network errors never expose original exception text', async () => {
  await withFetch(async () => { throw new TypeError('TOP_SECRET'); }, async () => {
    await assert.rejects(requestJSON('/api/ask'), error => {
      assert.equal(error.code, 'NetworkError');
      assert.doesNotMatch(formatApiError(error), /TOP_SECRET/);
      return true;
    });
  });
});

test('timeout and caller cancellation are different errors', async () => {
  const pending = async (_url, options) => new Promise((_resolve, reject) => {
    const abort = () => reject(new DOMException('Aborted', 'AbortError'));
    if (options.signal.aborted) abort();
    else options.signal.addEventListener('abort', abort, { once: true });
  });
  await withFetch(pending, async () => {
    await assert.rejects(requestJSON('/api/ask', { timeoutMs: 5 }), error => error.code === 'RequestTimeout');
    const controller = new AbortController();
    controller.abort();
    await assert.rejects(requestJSON('/api/ask', { signal: controller.signal }), error => error.code === 'RequestCancelled');
  });
});

test('unknown UI errors are sanitized', () => {
  assert.doesNotMatch(formatApiError(new Error('TOP_SECRET')), /TOP_SECRET/);
  assert.equal(new ApiError('x').status, 0);
});
