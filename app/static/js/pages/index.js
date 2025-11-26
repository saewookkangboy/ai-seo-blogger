/**
 * 메인 페이지 로직
 */

import { ContentGenerator } from '../components/generator.js';
import { FormValidator } from '../components/form-validator.js';
import { APIClient } from '../core/api.js';
import { errorHandler } from '../core/error-handler.js';
import { $, copyToClipboard, downloadFile, formatError } from '../core/utils.js';

// 전역 인스턴스
let contentGenerator;
let formValidator;

/**
 * 페이지 초기화
 */
export function init() {
    const apiClient = new APIClient();
    contentGenerator = new ContentGenerator(apiClient);

    // 폼 검증 초기화
    const form = document.querySelector('#generator-form');
    if (form) {
        formValidator = new FormValidator(form);
    }

    // 이벤트 리스너 설정
    setupEventListeners();
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
    const generateBtn = $('#generate-btn');
    const cancelBtn = $('#cancel-btn');
    const copyBtn = $('#copy-btn');
    const downloadBtn = $('#download-btn');

    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerate);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', handleCancel);
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', handleCopy);
    }

    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownload);
    }

    // 키보드 단축키
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter: 생성
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleGenerate();
        }
        // Escape: 취소
        if (e.key === 'Escape') {
            handleCancel();
        }
    });
}

/**
 * 콘텐츠 생성 핸들러
 */
async function handleGenerate() {
    if (!contentGenerator) return;

    try {
        await contentGenerator.generate(
            // onProgress
            (progress) => {
                updateProgress(progress);
            },
            // onComplete
            (data) => {
                displayResult(data);
            },
            // onError
            (error) => {
                const friendlyMessage = errorHandler.handleNetworkError(error) || formatError(error);
                showError(friendlyMessage);
            }
        );
    } catch (error) {
        showError(formatError(error));
    }
}

/**
 * 생성 취소 핸들러
 */
function handleCancel() {
    if (contentGenerator) {
        contentGenerator.cancel();
    }
}

/**
 * 복사 핸들러
 */
async function handleCopy() {
    const resultContainer = $('#result-container');
    if (!resultContainer) return;

    const text = resultContainer.textContent || resultContainer.innerText;
    const success = await copyToClipboard(text);

    if (success) {
        showToast('복사되었습니다.', 'success');
    } else {
        showToast('복사에 실패했습니다.', 'error');
    }
}

/**
 * 다운로드 핸들러
 */
function handleDownload() {
    const resultContainer = $('#result-container');
    if (!resultContainer) return;

    const text = resultContainer.textContent || resultContainer.innerText;
    const filename = `content-${new Date().toISOString().split('T')[0]}.txt`;
    downloadFile(text, filename, 'text/plain');
    showToast('다운로드되었습니다.', 'success');
}

/**
 * 진행 상황 업데이트
 */
function updateProgress(progress) {
    const progressContainer = $('#progress-container');
    const progressBar = $('#progress-bar');
    const progressMessage = $('#progress-message');
    const aiStatus = $('#ai-status');
    const seoStatus = $('#seo-status');

    if (progressContainer) {
        progressContainer.style.display = 'block';
    }

    if (progressBar) {
        progressBar.style.width = `${progress.progress || 0}%`;
        progressBar.setAttribute('aria-valuenow', progress.progress || 0);
    }

    if (progressMessage) {
        progressMessage.textContent = progress.message || '생성 중...';
    }

    if (progress.content) {
        const resultContainer = $('#result-container');
        if (resultContainer) {
            resultContainer.textContent = progress.content;
        }
    }
}

/**
 * 결과 표시
 */
function displayResult(data) {
    const resultContainer = $('#result-container');
    const progressContainer = $('#progress-container');
    const copyBtn = $('#copy-btn');
    const downloadBtn = $('#download-btn');

    if (progressContainer) {
        progressContainer.style.display = 'none';
    }

    if (resultContainer && data.content) {
        resultContainer.textContent = data.content;
    }

    if (copyBtn) {
        copyBtn.classList.remove('d-none');
    }

    if (downloadBtn) {
        downloadBtn.classList.remove('d-none');
    }

    // 통계 업데이트
    if (data.stats) {
        updateStatistics(data.stats);
    }
}

/**
 * 통계 업데이트
 */
function updateStatistics(stats) {
    // 키워드, 단어 수, 길이 등 통계 업데이트
    // 기존 코드와 통합 필요
}

/**
 * 에러 표시
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * 토스트 메시지 표시
 */
function showToast(message, type = 'info') {
    // 간단한 토스트 구현
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        animation: fadeIn 0.3s;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 페이지 로드 시 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

