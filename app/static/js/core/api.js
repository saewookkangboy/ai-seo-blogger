/**
 * API 클라이언트 모듈
 * 모든 API 통신을 담당합니다.
 */

export class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * 콘텐츠 생성 (스트리밍) — /api/v1/generate-post-stream 사용
     */
    async *generateContentStream(data) {
        const body = {
            ...data,
            content_length: data.content_length != null ? String(data.content_length) : '3000',
        };
        const response = await fetch(`${this.baseURL}/api/v1/generate-post-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                const chunk = value ? decoder.decode(value, { stream: true }) : '';
                if (chunk) buffer += chunk;
                if (done && !buffer.trim()) break;

                const lines = buffer.split('\n');
                buffer = done ? '' : (lines.pop() ?? '');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            yield data;
                        } catch (e) {
                            // JSON 파싱 실패는 무시
                        }
                    }
                }
                if (done) break;
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * 콘텐츠 생성 (일반, 비스트리밍)
     */
    async generateContent(data) {
        const body = {
            ...data,
            content_length: data.content_length != null ? String(data.content_length) : '3000',
        };
        const response = await fetch(`${this.baseURL}/api/v1/generate-post`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * 시스템 통계 조회
     */
    async getStats() {
        const response = await fetch(`${this.baseURL}/api/stats`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    /**
     * 헬스체크
     */
    async healthCheck() {
        const response = await fetch(`${this.baseURL}/api/health`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    /**
     * POST 요청 (범용)
     */
    async post(url, data) {
        const response = await fetch(`${this.baseURL}${url}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * GET 요청 (범용)
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${this.baseURL}${url}?${queryString}` : `${this.baseURL}${url}`;
        
        const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}

