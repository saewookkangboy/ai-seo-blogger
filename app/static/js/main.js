/**
 * 메인 진입점
 * 모든 모듈을 여기서 import하고 초기화합니다.
 */

import { init as initIndex } from './pages/index.js';
import { errorHandler } from './core/error-handler.js';

// 페이지별 초기화
const path = window.location.pathname;

if (path === '/' || path === '/index.html') {
    initIndex();
}

// 전역 에러 핸들러는 error-handler.js에서 처리됨

