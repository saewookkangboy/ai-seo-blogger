/**
 * API 클라이언트 모듈
 * 모든 API 통신을 담당합니다.
 */

export class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * 콘텐츠 생성 (스트리밍)
     */
    async *generateContentStream(data) {
        const response = await fetch(`${this.baseURL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

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
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * 콘텐츠 생성 (일반)
     */
    async generateContent(data) {
        const response = await fetch(`${this.baseURL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
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
}

