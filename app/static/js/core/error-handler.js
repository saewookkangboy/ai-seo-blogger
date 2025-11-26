/**
 * 에러 처리 모듈
 */

export class ErrorHandler {
    constructor() {
        this.setupGlobalHandlers();
    }

    /**
     * 전역 에러 핸들러 설정
     */
    setupGlobalHandlers() {
        window.addEventListener('error', (event) => {
            this.handleError(event.error || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, {
                type: 'unhandledrejection',
            });
            event.preventDefault();
        });
    }

    /**
     * 에러 처리
     */
    handleError(error, context = {}) {
        const errorInfo = {
            message: this.extractErrorMessage(error),
            context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
        };

        // 콘솔에 로그
        console.error('Error:', errorInfo);

        // 사용자에게 친화적인 메시지 표시
        this.showUserFriendlyError(errorInfo.message);

        // 필요시 서버로 에러 전송
        // this.sendErrorToServer(errorInfo);
    }

    /**
     * 에러 메시지 추출
     */
    extractErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        if (error?.message) {
            return error.message;
        }
        if (error?.toString) {
            return error.toString();
        }
        return '알 수 없는 오류가 발생했습니다.';
    }

    /**
     * 사용자 친화적인 에러 메시지 표시
     */
    showUserFriendlyError(message) {
        // 이미 표시된 에러는 무시
        if (document.querySelector('.error-toast')) {
            return;
        }

        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.innerHTML = `
            <div class="error-toast-content">
                <i class="bi bi-exclamation-triangle-fill me-2" aria-hidden="true"></i>
                <span>${this.escapeHtml(message)}</span>
                <button class="error-toast-close" aria-label="닫기" onclick="this.parentElement.parentElement.remove()">
                    <i class="bi bi-x" aria-hidden="true"></i>
                </button>
            </div>
        `;

        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            max-width: 400px;
            background: #ef4444;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        // 자동 제거
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }

    /**
     * HTML 이스케이프
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 서버로 에러 전송 (선택사항)
     */
    async sendErrorToServer(errorInfo) {
        try {
            await fetch('/api/errors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(errorInfo),
            });
        } catch (err) {
            // 에러 전송 실패는 무시
            console.error('Failed to send error to server:', err);
        }
    }

    /**
     * 네트워크 에러 처리
     */
    handleNetworkError(error) {
        if (error.message.includes('fetch')) {
            return '네트워크 연결을 확인해주세요.';
        }
        if (error.message.includes('timeout')) {
            return '요청 시간이 초과되었습니다. 다시 시도해주세요.';
        }
        return '네트워크 오류가 발생했습니다.';
    }

    /**
     * API 에러 처리
     */
    handleAPIError(response) {
        if (response.status === 400) {
            return '잘못된 요청입니다. 입력값을 확인해주세요.';
        }
        if (response.status === 401) {
            return '인증이 필요합니다.';
        }
        if (response.status === 403) {
            return '권한이 없습니다.';
        }
        if (response.status === 404) {
            return '요청한 리소스를 찾을 수 없습니다.';
        }
        if (response.status === 500) {
            return '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
        }
        return `오류가 발생했습니다. (${response.status})`;
    }
}

// 전역 에러 핸들러 인스턴스
export const errorHandler = new ErrorHandler();

