/**
 * 프론트엔드 페이지 템플릿
 * 복사 후 [PageName], [feature] 교체
 * router.js에 등록: import { show[PageName] } from './pages/[page].js'
 */
import { request } from '../api.js';
import { formatApiError } from '../http.js';
import { state } from '../state.js';
import { CONTENT } from '../content.js';

// 상태: 페이지 내부에서만 관리
let _pageState = 'idle'; // idle | loading | success | empty | error
let _errorMessage = '';

export function show[PageName](container) {
  _pageState = 'idle';
  _render(container);
}

function _render(container) {
  container.innerHTML = `
    <div class="page-[feature]">
      ${_pageState === 'idle'    ? _renderIdle()    : ''}
      ${_pageState === 'loading' ? _renderLoading() : ''}
      ${_pageState === 'success' ? _renderSuccess() : ''}
      ${_pageState === 'empty'   ? _renderEmpty()   : ''}
      ${_pageState === 'error'   ? _renderError()   : ''}
    </div>
  `;
  const errorNode = container.querySelector('[data-error]');
  if (errorNode) errorNode.textContent = _errorMessage;
  _attachEvents(container);
}

function _attachEvents(container) {
  container.querySelector('#btn-[feature]')?.addEventListener('click', async () => {
    _pageState = 'loading';
    _render(container);
    try {
      const data = await request('/api/[feature]', { method: 'POST', body: {} });
      state.[feature] = data;
      _pageState = data ? 'success' : 'empty';
    } catch (error) {
      _errorMessage = formatApiError(error);
      _pageState = 'error';
    }
    _render(container);
  });
}

function _renderIdle()    { return `<button id="btn-[feature]">시작</button>`; }
function _renderLoading() { return `<p>로딩 중…</p>`; }
function _renderSuccess() { return `<p>완료</p>`; }
function _renderEmpty()   { return `<p>결과가 없습니다.</p>`; }
// Use textContent for server-provided messages; never interpolate them into HTML.
function _renderError() { return '<p role="alert" data-error></p>'; }
