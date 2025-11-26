/**
 * 유틸리티 함수 모듈
 */

/**
 * DOM 요소를 안전하게 가져옵니다.
 */
export function $(selector, parent = document) {
    return parent.querySelector(selector);
}

/**
 * 모든 DOM 요소를 가져옵니다.
 */
export function $$(selector, parent = document) {
    return Array.from(parent.querySelectorAll(selector));
}

/**
 * 디바운스 함수
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 스로틀 함수
 */
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 텍스트를 클립보드에 복사
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // 폴백: 구식 방법
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}

/**
 * 파일 다운로드
 */
export function downloadFile(content, filename, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * 텍스트에서 단어 수 계산
 */
export function countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * 텍스트에서 문자 수 계산
 */
export function countCharacters(text) {
    if (!text) return 0;
    return text.length;
}

/**
 * 안전한 HTML 이스케이프
 */
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 포맷된 숫자 표시
 */
export function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num);
}

/**
 * 에러 메시지 포맷팅
 */
export function formatError(error) {
    if (typeof error === 'string') {
        return error;
    }
    if (error.message) {
        return error.message;
    }
    return '알 수 없는 오류가 발생했습니다.';
}

