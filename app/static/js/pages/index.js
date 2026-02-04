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
    
    // 타겟 분석 버튼 이벤트 리스너
    const analyzeTargetBtn = $('#analyze_target_btn');
    if (analyzeTargetBtn) {
        analyzeTargetBtn.addEventListener('click', handleAnalyzeTarget);
    }
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
 * 통합 결과 영역 표시 (타겟 분석 | 생성된 포스트)
 * @param {'analysis'|'post'} type - 결과 유형
 */
function showUnifiedResult(type) {
    const wrapper = $('#result-wrapper');
    const badge = $('#result-type-badge');
    const paneAnalysis = $('#result-pane-analysis');
    const panePost = $('#result-pane-post');
    const copyBtn = $('#copy-btn');
    const downloadBtn = $('#download-btn');

    if (!wrapper) return;

    wrapper.style.display = 'block';

    if (badge) {
        badge.textContent = type === 'analysis' ? '타겟 분석 결과' : '생성된 포스트';
        badge.className = 'badge result-type-badge ' + (type === 'analysis' ? 'bg-info' : 'bg-primary');
    }

    const contentStatus = $('#content-status');
    if (contentStatus) {
        contentStatus.textContent = type === 'analysis' ? '분석 완료' : '준비됨';
    }

    if (paneAnalysis) {
        paneAnalysis.style.display = type === 'analysis' ? 'block' : 'none';
    }
    if (panePost) {
        panePost.style.display = type === 'post' ? 'block' : 'none';
    }

    if (copyBtn) {
        copyBtn.classList.toggle('d-none', type === 'analysis');
    }
    if (downloadBtn) {
        downloadBtn.classList.toggle('d-none', type === 'analysis');
    }

    wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * 결과 표시
 */
function displayResult(data) {
    showUnifiedResult('post');

    const resultContainer = $('#result-container');
    const progressContainer = $('#progress-container');
    const copyBtn = $('#copy-btn');
    const downloadBtn = $('#download-btn');

    if (progressContainer) {
        progressContainer.style.display = 'none';
    }

    if (resultContainer && data.content) {
        resultContainer.innerHTML = data.content;
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

    // AI 윤리 평가 결과 표시
    if (data.ai_ethics_evaluation) {
        displayAIEthicsEvaluation(data.ai_ethics_evaluation);
        
        // 출처 및 인용 분석 결과 표시
        if (data.ai_ethics_evaluation.details && data.ai_ethics_evaluation.details.citations) {
            displayCitationAnalysis(data.ai_ethics_evaluation.details.citations);
        }
    } else if (data.ai_ethics_score !== undefined) {
        // 점수만 있는 경우 (간단 표시)
        const ethicsSection = $('#ai-ethics-evaluation');
        if (ethicsSection) {
            const overallScore = $('#ethics-overall-score');
            const progressBar = $('#ethics-progress-bar');
            if (overallScore) {
                overallScore.textContent = `${data.ai_ethics_score.toFixed(1)}/100`;
                overallScore.className = `badge fs-5 ${getScoreBadgeClass(data.ai_ethics_score)}`;
            }
            if (progressBar) {
                progressBar.style.width = `${data.ai_ethics_score}%`;
                progressBar.setAttribute('aria-valuenow', data.ai_ethics_score);
                progressBar.textContent = `${data.ai_ethics_score.toFixed(1)}%`;
            }
            ethicsSection.style.display = 'block';
        }
    }
}

/**
 * AI 윤리 평가 결과 표시
 */
function displayAIEthicsEvaluation(evaluation) {
    const ethicsSection = $('#ai-ethics-evaluation');
    if (!ethicsSection || !evaluation) return;

    const scores = evaluation.scores || {};
    const details = evaluation.details || {};
    const recommendations = evaluation.recommendations || [];

    // 종합 점수
    const overallScore = evaluation.overall_score || 0;
    const overallScoreEl = $('#ethics-overall-score');
    const progressBar = $('#ethics-progress-bar');
    
    if (overallScoreEl) {
        overallScoreEl.textContent = `${overallScore.toFixed(1)}/100`;
        overallScoreEl.className = `badge fs-5 ${getScoreBadgeClass(overallScore)}`;
    }
    
    if (progressBar) {
        progressBar.style.width = `${overallScore}%`;
        progressBar.setAttribute('aria-valuenow', overallScore);
        progressBar.textContent = `${overallScore.toFixed(1)}%`;
        progressBar.className = `progress-bar ${getScoreProgressClass(overallScore)}`;
    }

    // 세부 점수 업데이트
    updateScoreDisplay('ethics-bias', scores.bias || 0);
    updateScoreDisplay('ethics-fairness', scores.fairness || 0);
    updateScoreDisplay('ethics-transparency', scores.transparency || 0);
    updateScoreDisplay('ethics-privacy', scores.privacy || 0);
    updateScoreDisplay('ethics-harmful', scores.harmful_content || 0);
    updateScoreDisplay('ethics-accuracy', scores.accuracy || 0);

    // 권장사항 표시
    const recommendationsEl = $('#ethics-recommendations');
    if (recommendationsEl) {
        if (recommendations.length > 0) {
            recommendationsEl.innerHTML = recommendations.map(rec => 
                `<li class="mb-2"><i class="bi bi-check-circle text-success"></i> ${rec}</li>`
            ).join('');
        } else {
            recommendationsEl.innerHTML = '<li class="text-success"><i class="bi bi-check-circle"></i> 모든 Responsible AI 원칙을 잘 준수하고 있습니다.</li>';
        }
    }

    // 섹션 표시
    ethicsSection.style.display = 'block';
}

/**
 * 개별 점수 표시 업데이트
 */
function updateScoreDisplay(prefix, score) {
    const scoreEl = $(`#${prefix}-score`);
    const progressEl = $(`#${prefix}-progress`);
    
    if (scoreEl) {
        scoreEl.textContent = `${score.toFixed(1)}`;
        scoreEl.className = `badge ${getScoreBadgeClass(score)}`;
    }
    
    if (progressEl) {
        progressEl.style.width = `${score}%`;
        progressEl.className = `progress-bar ${getScoreProgressClass(score)}`;
    }
}

/**
 * 점수에 따른 배지 클래스 반환
 */
function getScoreBadgeClass(score) {
    if (score >= 90) return 'bg-success';
    if (score >= 80) return 'bg-info';
    if (score >= 70) return 'bg-warning';
    return 'bg-danger';
}

/**
 * 점수에 따른 프로그레스 바 클래스 반환
 */
function getScoreProgressClass(score) {
    if (score >= 90) return 'bg-success';
    if (score >= 80) return 'bg-info';
    if (score >= 70) return 'bg-warning';
    return 'bg-danger';
}

/**
 * 출처 및 인용 분석 결과 표시
 */
function displayCitationAnalysis(citationData) {
    const citationSection = $('#citation-analysis');
    if (!citationSection || !citationData) return;

    const citationScore = citationData.citation_score || 0;
    const urls = citationData.urls_found || [];
    const urlValidation = citationData.url_validation || {};
    const sourceCredibility = citationData.source_credibility || {};
    const citationFormats = citationData.citation_formats || [];
    const citationCompleteness = citationData.citation_completeness || {};
    const recommendations = citationData.recommendations || [];

    // 출처 점수 표시
    const scoreBadge = $('#citation-score-badge');
    const scoreProgress = $('#citation-progress-bar');
    
    if (scoreBadge) {
        scoreBadge.textContent = `${citationScore.toFixed(1)}/100`;
        scoreBadge.className = `badge fs-5 ${getScoreBadgeClass(citationScore)}`;
    }
    
    if (scoreProgress) {
        scoreProgress.style.width = `${citationScore}%`;
        scoreProgress.setAttribute('aria-valuenow', citationScore);
        scoreProgress.textContent = `${citationScore.toFixed(1)}%`;
        scoreProgress.className = `progress-bar ${getScoreProgressClass(citationScore)}`;
    }

    // URL 정보 표시
    const urlsContainer = $('#citation-urls');
    if (urlsContainer) {
        if (urls.length > 0) {
            const urlList = urls.slice(0, 5).map(url => {
                const isValid = urlValidation.valid_urls && urlValidation.valid_urls.includes(url);
                const badgeClass = isValid ? 'bg-success' : 'bg-danger';
                return `<div class="mb-1">
                    <span class="badge ${badgeClass} me-2">${isValid ? '✓' : '✗'}</span>
                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="small">${url.length > 60 ? url.substring(0, 60) + '...' : url}</a>
                </div>`;
            }).join('');
            urlsContainer.innerHTML = urlList;
            if (urls.length > 5) {
                urlsContainer.innerHTML += `<p class="text-muted small mt-2 mb-0">외 ${urls.length - 5}개 URL...</p>`;
            }
        } else {
            urlsContainer.innerHTML = '<p class="text-muted small mb-0">발견된 URL이 없습니다.</p>';
        }
    }

    // URL 개수 표시
    const validUrlCount = $('#valid-url-count');
    const invalidUrlCount = $('#invalid-url-count');
    if (validUrlCount) {
        validUrlCount.textContent = `유효: ${urlValidation.valid_count || 0}`;
    }
    if (invalidUrlCount) {
        invalidUrlCount.textContent = `무효: ${urlValidation.invalid_count || 0}`;
    }

    // 출처 신뢰도 표시
    const credibilityDist = sourceCredibility.distribution || {};
    if ($('#high-credibility-count')) {
        $('#high-credibility-count').textContent = credibilityDist.high || 0;
    }
    if ($('#medium-credibility-count')) {
        $('#medium-credibility-count').textContent = credibilityDist.medium || 0;
    }
    if ($('#low-credibility-count')) {
        $('#low-credibility-count').textContent = credibilityDist.low || 0;
    }
    if ($('#unknown-credibility-count')) {
        $('#unknown-credibility-count').textContent = credibilityDist.unknown || 0;
    }
    if ($('#avg-credibility-score')) {
        $('#avg-credibility-score').textContent = `${(sourceCredibility.average_score || 0).toFixed(1)}%`;
    }

    // 인용 형식 표시
    const formatsContainer = $('#citation-formats');
    if (formatsContainer) {
        if (citationFormats.length > 0) {
            formatsContainer.innerHTML = citationFormats.map(format => 
                `<span class="badge bg-primary me-1">${format.toUpperCase()}</span>`
            ).join('');
        } else {
            formatsContainer.innerHTML = '<span class="badge bg-secondary">표준 인용 형식 없음</span>';
        }
    }

    // 출처 완전성 표시
    const completenessScore = citationCompleteness.score || 0;
    const completenessProgress = $('#completeness-progress-bar');
    if (completenessProgress) {
        completenessProgress.style.width = `${completenessScore}%`;
        completenessProgress.textContent = `${completenessScore.toFixed(1)}%`;
        completenessProgress.className = `progress-bar ${getScoreProgressClass(completenessScore)}`;
    }

    const completenessIssues = $('#completeness-issues');
    if (completenessIssues) {
        const issues = citationCompleteness.issues || [];
        if (issues.length > 0) {
            completenessIssues.innerHTML = issues.map(issue => 
                `<p class="mb-1"><i class="bi bi-exclamation-triangle text-warning"></i> ${issue}</p>`
            ).join('');
        } else {
            completenessIssues.innerHTML = '<p class="mb-0 text-success"><i class="bi bi-check-circle"></i> 출처 정보가 완전합니다.</p>';
        }
    }

    // 권장사항 표시
    const recommendationsEl = $('#citation-recommendations');
    if (recommendationsEl) {
        if (recommendations.length > 0) {
            recommendationsEl.innerHTML = recommendations.map(rec => 
                `<li class="mb-2"><i class="bi bi-lightbulb text-warning"></i> ${rec}</li>`
            ).join('');
        } else {
            recommendationsEl.innerHTML = '<li class="text-success"><i class="bi bi-check-circle"></i> 출처 및 인용이 적절합니다.</li>';
        }
    }

    // 섹션 표시
    citationSection.style.display = 'block';
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

/**
 * 타겟 분석 핸들러
 */
async function handleAnalyzeTarget() {
    const targetKeyword = $('#target_keyword')?.value?.trim();
    const targetType = $('#target_type')?.value || 'keyword';
    const additionalContext = $('#additional_context')?.value?.trim() || null;
    const aiProvider = $('#ai_provider')?.value || 'openai';
    
    if (!targetKeyword) {
        showToast('타겟 키워드를 입력해주세요.', 'error');
        return;
    }
    
    const loadingContainer = $('#target_analysis_loading');
    const analysisContent = $('#target_analysis_content');

    if (loadingContainer) {
        loadingContainer.style.display = 'block';
    }
    if (analysisContent) {
        analysisContent.innerHTML = '';
    }

    try {
        const apiClient = new APIClient();
        const useGemini = aiProvider === 'gemini';

        const response = await apiClient.post('/api/v1/target/analyze', {
            target_keyword: targetKeyword,
            target_type: targetType,
            additional_context: additionalContext,
            use_gemini: useGemini
        });

        if (response.success && response.data) {
            displayTargetAnalysis(response.data, targetType);
            showUnifiedResult('analysis');

            if (loadingContainer) {
                loadingContainer.style.display = 'none';
            }
            showToast('타겟 분석이 완료되었습니다.', 'success');
        } else {
            throw new Error('분석 결과를 받아오지 못했습니다.');
        }
    } catch (error) {
        console.error('타겟 분석 오류:', error);
        const friendlyMessage = errorHandler.handleNetworkError(error) || formatError(error);
        showToast(friendlyMessage, 'error');
        if (loadingContainer) {
            loadingContainer.style.display = 'none';
        }
    }
}

/**
 * 타겟 분석 결과 표시
 */
function displayTargetAnalysis(data, targetType) {
    const analysisContent = $('#target_analysis_content');
    if (!analysisContent) return;
    
    let html = '';
    
    // 메타데이터 표시
    if (data.metadata) {
        html += `
            <div class="mb-4 p-3 bg-white rounded">
                <small class="text-muted">
                    <i class="bi bi-info-circle me-1"></i>
                    분석 일시: ${new Date(data.metadata.analyzed_at).toLocaleString('ko-KR')} | 
                    모델: ${data.metadata.model || 'N/A'}
                </small>
            </div>
        `;
    }
    
    // 키워드 분석 결과
    if (targetType === 'keyword' && data.keyword_analysis) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-search me-2"></i>
                    키워드 분석
                </h6>
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded">
                            <strong>검색 의도:</strong>
                            <span class="badge bg-primary ms-2">${data.keyword_analysis.search_intent || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded">
                            <strong>경쟁도:</strong>
                            <span class="badge bg-warning ms-2">${data.keyword_analysis.competition_level || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded">
                            <strong>검색량 추정:</strong>
                            <span class="badge bg-info ms-2">${data.keyword_analysis.search_volume_estimate || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                ${data.keyword_analysis.related_keywords && data.keyword_analysis.related_keywords.length > 0 ? `
                    <div class="mt-3">
                        <strong>관련 키워드:</strong>
                        <div class="mt-2">
                            ${data.keyword_analysis.related_keywords.map(kw => 
                                `<span class="badge bg-secondary me-1 mb-1">${kw}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // 타겟 오디언스 분석 결과
    if (data.target_audience) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-people me-2"></i>
                    타겟 오디언스
                </h6>
                ${data.target_audience.primary_groups && data.target_audience.primary_groups.length > 0 ? `
                    <div class="row g-3">
                        ${data.target_audience.primary_groups.map(group => `
                            <div class="col-md-6">
                                <div class="card border">
                                    <div class="card-body">
                                        <h6 class="card-title">${group.group_name || 'N/A'}</h6>
                                        <p class="card-text small mb-2">
                                            <strong>특성:</strong> ${group.characteristics || 'N/A'}<br>
                                            <strong>니즈:</strong> ${group.needs || 'N/A'}<br>
                                            <strong>관심사:</strong> ${group.interests || 'N/A'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // 콘텐츠 전략 분석 결과
    if (data.content_strategy) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-file-text me-2"></i>
                    콘텐츠 전략
                </h6>
                <div class="p-3 bg-light rounded">
                    <p><strong>추천 콘텐츠 유형:</strong></p>
                    <div class="mb-2">
                        ${data.content_strategy.recommended_types && data.content_strategy.recommended_types.length > 0 ? 
                            data.content_strategy.recommended_types.map(type => 
                                `<span class="badge bg-success me-1">${type}</span>`
                            ).join('') : 'N/A'}
                    </div>
                    <p class="mb-2"><strong>최적의 콘텐츠 길이:</strong> ${data.content_strategy.optimal_length || 'N/A'}</p>
                    ${data.content_strategy.seo_points && data.content_strategy.seo_points.length > 0 ? `
                        <p class="mb-2"><strong>SEO 최적화 포인트:</strong></p>
                        <ul class="mb-0">
                            ${data.content_strategy.seo_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // 경쟁 분석 결과
    if (data.competition_analysis) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-graph-up me-2"></i>
                    경쟁 분석
                </h6>
                <div class="p-3 bg-light rounded">
                    <p class="mb-2"><strong>경쟁 강도:</strong> ${data.competition_analysis.competition_strength || 'N/A'}</p>
                    ${data.competition_analysis.differentiation_points && data.competition_analysis.differentiation_points.length > 0 ? `
                        <p class="mb-2"><strong>차별화 포인트:</strong></p>
                        <ul class="mb-0">
                            ${data.competition_analysis.differentiation_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // 오디언스 분석 결과 (target_type이 audience인 경우)
    if (targetType === 'audience' && data.audience_segments) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-diagram-3 me-2"></i>
                    오디언스 세그먼트
                </h6>
                <div class="row g-3">
                    ${data.audience_segments.map(segment => `
                        <div class="col-md-6">
                            <div class="card border">
                                <div class="card-body">
                                    <h6 class="card-title">${segment.segment_name || 'N/A'}</h6>
                                    <p class="card-text small mb-2">
                                        <strong>인구통계:</strong> ${segment.demographics || 'N/A'}<br>
                                        <strong>심리적 특성:</strong> ${segment.psychographics || 'N/A'}<br>
                                        <strong>규모 추정:</strong> ${segment.size_estimate || 'N/A'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        if (data.behavior_patterns) {
            html += `
                <div class="mb-4">
                    <h6 class="fw-bold mb-3">
                        <i class="bi bi-activity me-2"></i>
                        행동 패턴
                    </h6>
                    <div class="p-3 bg-light rounded">
                        <p><strong>미디어 소비:</strong> ${data.behavior_patterns.media_consumption || 'N/A'}</p>
                        <p><strong>구매 행동:</strong> ${data.behavior_patterns.purchase_behavior || 'N/A'}</p>
                        <p class="mb-0"><strong>온라인 활동:</strong> ${data.behavior_patterns.online_activity || 'N/A'}</p>
                    </div>
                </div>
            `;
        }
        
        if (data.content_preferences) {
            html += `
                <div class="mb-4">
                    <h6 class="fw-bold mb-3">
                        <i class="bi bi-heart me-2"></i>
                        콘텐츠 선호도
                    </h6>
                    <div class="p-3 bg-light rounded">
                        <p><strong>선호 콘텐츠 유형:</strong></p>
                        <div class="mb-2">
                            ${data.content_preferences.preferred_types && data.content_preferences.preferred_types.length > 0 ? 
                                data.content_preferences.preferred_types.map(type => 
                                    `<span class="badge bg-primary me-1">${type}</span>`
                                ).join('') : 'N/A'}
                        </div>
                        <p><strong>톤앤매너:</strong> ${data.content_preferences.tone_and_manner || 'N/A'}</p>
                        ${data.content_preferences.engagement_factors && data.content_preferences.engagement_factors.length > 0 ? `
                            <p class="mb-2"><strong>참여 요인:</strong></p>
                            <ul class="mb-0">
                                ${data.content_preferences.engagement_factors.map(factor => `<li>${factor}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        if (data.marketing_insights) {
            html += `
                <div class="mb-4">
                    <h6 class="fw-bold mb-3">
                        <i class="bi bi-lightbulb me-2"></i>
                        마케팅 인사이트
                    </h6>
                    <div class="p-3 bg-light rounded">
                        <p><strong>효과적인 채널:</strong></p>
                        <div class="mb-2">
                            ${data.marketing_insights.effective_channels && data.marketing_insights.effective_channels.length > 0 ? 
                                data.marketing_insights.effective_channels.map(channel => 
                                    `<span class="badge bg-info me-1">${channel}</span>`
                                ).join('') : 'N/A'}
                        </div>
                        <p><strong>메시징 전략:</strong> ${data.marketing_insights.messaging_strategy || 'N/A'}</p>
                        ${data.marketing_insights.targeting_keywords && data.marketing_insights.targeting_keywords.length > 0 ? `
                            <p class="mb-2"><strong>타겟팅 키워드:</strong></p>
                            <div>
                                ${data.marketing_insights.targeting_keywords.map(kw => 
                                    `<span class="badge bg-secondary me-1 mb-1">${kw}</span>`
                                ).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    }
    
    // 경쟁자 분석 결과 (target_type이 competitor인 경우)
    if (targetType === 'competitor' && data.competitive_environment) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-trophy me-2"></i>
                    경쟁 환경
                </h6>
                <div class="p-3 bg-light rounded">
                    <p><strong>주요 경쟁자:</strong></p>
                    <div class="mb-2">
                        ${data.competitive_environment.main_competitors && data.competitive_environment.main_competitors.length > 0 ? 
                            data.competitive_environment.main_competitors.map(competitor => 
                                `<span class="badge bg-danger me-1">${competitor}</span>`
                            ).join('') : 'N/A'}
                    </div>
                    <p><strong>경쟁 강도:</strong> ${data.competitive_environment.competition_intensity || 'N/A'}</p>
                    <p class="mb-0"><strong>시장 포지셔닝:</strong> ${data.competitive_environment.market_positioning || 'N/A'}</p>
                </div>
            </div>
        `;
        
        if (data.competitor_analysis) {
            html += `
                <div class="mb-4">
                    <h6 class="fw-bold mb-3">
                        <i class="bi bi-bar-chart me-2"></i>
                        경쟁자 분석
                    </h6>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="card border-success">
                                <div class="card-body">
                                    <h6 class="card-title text-success">강점</h6>
                                    <ul class="mb-0">
                                        ${data.competitor_analysis.strengths && data.competitor_analysis.strengths.length > 0 ? 
                                            data.competitor_analysis.strengths.map(strength => `<li>${strength}</li>`).join('') : 
                                            '<li>N/A</li>'}
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-warning">
                                <div class="card-body">
                                    <h6 class="card-title text-warning">약점 및 기회</h6>
                                    <ul class="mb-0">
                                        ${data.competitor_analysis.weaknesses && data.competitor_analysis.weaknesses.length > 0 ? 
                                            data.competitor_analysis.weaknesses.map(weakness => `<li>${weakness}</li>`).join('') : 
                                            '<li>N/A</li>'}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    ${data.competitor_analysis.differentiation_points && data.competitor_analysis.differentiation_points.length > 0 ? `
                        <div class="mt-3">
                            <p><strong>차별화 포인트:</strong></p>
                            <ul>
                                ${data.competitor_analysis.differentiation_points.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        if (data.strategic_recommendations) {
            html += `
                <div class="mb-4">
                    <h6 class="fw-bold mb-3">
                        <i class="bi bi-arrow-right-circle me-2"></i>
                        전략적 제안
                    </h6>
                    <div class="p-3 bg-light rounded">
                        <p><strong>경쟁 우위 확보 방안:</strong></p>
                        <ul class="mb-3">
                            ${data.strategic_recommendations.competitive_advantages && data.strategic_recommendations.competitive_advantages.length > 0 ? 
                                data.strategic_recommendations.competitive_advantages.map(adv => `<li>${adv}</li>`).join('') : 
                                '<li>N/A</li>'}
                        </ul>
                        <p><strong>시장 진입 전략:</strong> ${data.strategic_recommendations.market_entry_strategy || 'N/A'}</p>
                        ${data.strategic_recommendations.content_differentiation && data.strategic_recommendations.content_differentiation.length > 0 ? `
                            <p class="mb-2"><strong>콘텐츠 차별화 전략:</strong></p>
                            <ul class="mb-0">
                                ${data.strategic_recommendations.content_differentiation.map(strategy => `<li>${strategy}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    }
    
    // 에러가 있는 경우
    if (data.error) {
        html += `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${data.error}
            </div>
        `;
    }
    
    analysisContent.innerHTML = html;
}

/**
 * 타겟 분석 섹션으로 스크롤 (해시 링크 처리)
 */
function handleHashScroll() {
    if (window.location.hash === '#target-analyzer') {
        const targetSection = document.getElementById('target-analyzer');
        if (targetSection) {
            setTimeout(() => {
                targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }
}

// 페이지 로드 시 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        init();
        handleHashScroll();
    });
} else {
    init();
    handleHashScroll();
}

// 해시 변경 감지
window.addEventListener('hashchange', handleHashScroll);

