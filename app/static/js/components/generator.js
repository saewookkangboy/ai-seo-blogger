/**
 * 콘텐츠 생성기 컴포넌트
 */

import { APIClient } from '../core/api.js';
import { $, formatError } from '../core/utils.js';

export class ContentGenerator {
    constructor(apiClient) {
        this.api = apiClient || new APIClient();
        this.abortController = null;
    }

    /**
     * 폼 데이터 수집
     */
    collectFormData() {
        const rules = [];
        const ruleInputs = document.querySelectorAll('input[name="rules"]:checked');
        ruleInputs.forEach(input => rules.push(input.value));

        return {
            text: $('#text_input')?.value.trim() || '',
            url: $('#url_input')?.value.trim() || '',
            rules: rules,
            ai_mode: $('#ai_mode')?.value || '',
            content_length: parseInt($('#content_length')?.value || '2000'),
            policy_auto: $('#policy_auto')?.checked || false,
        };
    }

    /**
     * 폼 검증
     */
    validateForm(data) {
        if (!data.text && !data.url) {
            throw new Error('주제/문맥 또는 URL을 입력해주세요.');
        }
        return true;
    }

    /**
     * 콘텐츠 생성 시작
     */
    async generate(onProgress, onComplete, onError) {
        try {
            const formData = this.collectFormData();
            
            // 폼 검증
            try {
                this.validateForm(formData);
            } catch (error) {
                onError?.(error);
                return;
            }

            // 이전 요청 취소
            if (this.abortController) {
                this.abortController.abort();
            }

            this.abortController = new AbortController();

            // UI 업데이트
            this.setLoadingState(true);

            // 스트리밍 생성
            let fullContent = '';
            for await (const chunk of this.api.generateContentStream(formData)) {
                if (this.abortController.signal.aborted) {
                    break;
                }

                if (chunk.type === 'content') {
                    fullContent += chunk.data;
                    onProgress?.({
                        content: fullContent,
                        progress: chunk.progress || 0,
                        message: chunk.message || '생성 중...',
                    });
                } else if (chunk.type === 'complete') {
                    onComplete?.(chunk.data);
                    break;
                } else if (chunk.type === 'error') {
                    throw new Error(chunk.message || '생성 중 오류가 발생했습니다.');
                }
            }

            this.setLoadingState(false);
        } catch (error) {
            this.setLoadingState(false);
            if (error.name === 'AbortError') {
                onError?.(new Error('생성이 취소되었습니다.'));
            } else {
                onError?.(error);
            }
        }
    }

    /**
     * 생성 취소
     */
    cancel() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.setLoadingState(false);
    }

    /**
     * 로딩 상태 설정
     */
    setLoadingState(loading) {
        const generateBtn = $('#generate-btn');
        const cancelBtn = $('#cancel-btn');
        const btnSpinner = $('#btn-spinner');
        const btnText = $('#btn-text');

        if (generateBtn) {
            generateBtn.disabled = loading;
        }
        if (cancelBtn) {
            cancelBtn.style.display = loading ? 'block' : 'none';
        }
        if (btnSpinner) {
            btnSpinner.classList.toggle('d-none', !loading);
        }
        if (btnText) {
            btnText.textContent = loading ? '생성 중...' : '콘텐츠 생성';
        }
    }
}

