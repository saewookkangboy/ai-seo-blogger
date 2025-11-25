// Admin Dashboard JavaScript - Simplified and Optimized
// Core functionality with proper API integration

// ============================================================================
// Global State
// ============================================================================
let currentSection = 'dashboard';
let postsData = [];
let keywordsData = [];
let currentPage = 1;
const itemsPerPage = 10;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Unified API call function with error handling
 */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Call Error:', error);
        showToast(`API 오류: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="bi bi-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x"></i>
        </button>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'exclamation-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };
    return icons[type] || icons.info;
}

/**
 * Show loading state
 */
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (!element) return;

    if (isLoading) {
        element.innerHTML = '<div class="loading">로딩 중...</div>';
    }
}

// ============================================================================
// Navigation
// ============================================================================

function showContent(section) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(el => {
        el.classList.remove('active');
    });

    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(el => {
        el.classList.remove('active');
    });

    // Show selected section
    const sectionElement = document.getElementById(`${section}-content`);
    if (sectionElement) {
        sectionElement.classList.add('active');
    }

    // Add active class to clicked nav link
    event?.target?.closest('.nav-link')?.classList.add('active');

    currentSection = section;

    // Load section data
    loadSectionData(section);
}

async function loadSectionData(section) {
    switch (section) {
        case 'dashboard':
            await loadDashboardStats();
            break;
        case 'posts':
            await loadPosts();
            break;
        case 'keywords':
            await loadKeywords();
            break;
        case 'system':
            await loadSystemInfo();
            break;
    }
}

// ============================================================================
// Dashboard Statistics
// ============================================================================

async function loadDashboardStats() {
    try {
        // Load various stats in parallel
        const [dailyStats, apiUsage, postsStats] = await Promise.all([
            apiCall('/api/v1/stats/daily?days=7'),
            apiCall('/api/v1/stats/api-usage'),
            apiCall('/api/v1/admin/posts/stats')
        ]);

        // Update stat cards
        updateStatCard('total-posts', postsStats.total || 0);
        updateStatCard('total-keywords', postsStats.total_keywords || 0);
        updateStatCard('api-calls', (apiUsage.openai || 0) + (apiUsage.gemini || 0));

        showToast('통계 로드 완료', 'success');
    } catch (error) {
        console.error('Dashboard stats error:', error);
        showToast('통계 로드 실패', 'error');
    }
}

function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value.toLocaleString();
    }
}

// ============================================================================
// Posts Management
// ============================================================================

async function loadPosts(page = 1) {
    try {
        setLoading('posts-table-body', true);

        const skip = (page - 1) * itemsPerPage;
        const data = await apiCall(`/api/v1/posts?skip=${skip}&limit=${itemsPerPage}`);

        postsData = data.posts || data || [];
        currentPage = page;

        renderPostsTable();
        renderPagination('posts', data.total || postsData.length);

    } catch (error) {
        console.error('Load posts error:', error);
        document.getElementById('posts-table-body').innerHTML =
            '<tr><td colspan="5" class="text-center text-danger">포스트 로드 실패</td></tr>';
    }
}

function renderPostsTable() {
    const tbody = document.getElementById('posts-table-body');
    if (!tbody) return;

    if (postsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">포스트가 없습니다</td></tr>';
        return;
    }

    tbody.innerHTML = postsData.map(post => `
        <tr>
            <td>
                <div class="fw-bold">${escapeHtml(post.title || '제목 없음')}</div>
                <small class="text-muted">${escapeHtml(post.original_url || 'N/A')}</small>
            </td>
            <td><span class="badge bg-primary">${escapeHtml(post.keywords || 'N/A')}</span></td>
            <td>${post.word_count || 0}자</td>
            <td>${formatDate(post.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewPost(${post.id})">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deletePost(${post.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deletePost(id) {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
        await apiCall(`/api/v1/posts/${id}`, { method: 'DELETE' });
        showToast('포스트가 삭제되었습니다', 'success');
        await loadPosts(currentPage);
    } catch (error) {
        showToast('삭제 실패', 'error');
    }
}

function viewPost(id) {
    const post = postsData.find(p => p.id === id);
    if (!post) return;

    // Open in new window or show modal
    window.open(`/posts/${id}`, '_blank');
}

// ============================================================================
// Keywords Management
// ============================================================================

async function loadKeywords(page = 1) {
    try {
        setLoading('keywords-table-body', true);

        const skip = (page - 1) * itemsPerPage;
        const data = await apiCall(`/api/v1/admin/keywords-list?skip=${skip}&limit=${itemsPerPage}`);

        keywordsData = data.keywords || data || [];
        currentPage = page;

        renderKeywordsTable();
        renderPagination('keywords', data.total || keywordsData.length);

    } catch (error) {
        console.error('Load keywords error:', error);
        document.getElementById('keywords-table-body').innerHTML =
            '<tr><td colspan="4" class="text-center text-danger">키워드 로드 실패</td></tr>';
    }
}

function renderKeywordsTable() {
    const tbody = document.getElementById('keywords-table-body');
    if (!tbody) return;

    if (keywordsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">키워드가 없습니다</td></tr>';
        return;
    }

    tbody.innerHTML = keywordsData.map(keyword => `
        <tr>
            <td>${escapeHtml(keyword.keyword)}</td>
            <td><span class="badge bg-info">${escapeHtml(keyword.type || 'general')}</span></td>
            <td>${formatDate(keyword.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteKeyword('${keyword.type}', '${escapeHtml(keyword.keyword)}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteKeyword(type, keyword) {
    if (!confirm(`"${keyword}" 키워드를 삭제하시겠습니까?`)) return;

    try {
        await apiCall(`/api/v1/admin/keywords-list?type=${type}&keyword=${encodeURIComponent(keyword)}`, {
            method: 'DELETE'
        });
        showToast('키워드가 삭제되었습니다', 'success');
        await loadKeywords(currentPage);
    } catch (error) {
        showToast('삭제 실패', 'error');
    }
}

// ============================================================================
// System Management
// ============================================================================

async function loadSystemInfo() {
    try {
        const health = await apiCall('/health');
        document.getElementById('system-status').textContent = health.status || 'unknown';
        document.getElementById('system-version').textContent = health.version || 'N/A';
    } catch (error) {
        console.error('System info error:', error);
    }
}

// ============================================================================
// Helper Functions
// ============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR');
}

function renderPagination(type, total) {
    const totalPages = Math.ceil(total / itemsPerPage);
    const container = document.getElementById(`${type}-pagination`);
    if (!container) return;

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <button class="btn btn-sm ${i === currentPage ? 'btn-primary' : 'btn-outline-primary'}" 
                    onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(${i})">
                ${i}
            </button>
        `;
    }
    container.innerHTML = html;
}

// ============================================================================
// SEO Guidelines Management
// ============================================================================

async function loadSEOGuidelines() {
    try {
        const versionInfo = await apiCall('/api/v1/admin/seo-guidelines/version');

        // Update version badge
        const versionBadge = document.getElementById('seo-version');
        if (versionBadge) {
            versionBadge.textContent = `버전: ${versionInfo.version}`;
        }

        // Update last updated time
        const lastUpdated = document.getElementById('seo-last-updated');
        if (lastUpdated) {
            const date = new Date(versionInfo.last_updated || '2025-01-25T01:06:54+09:00');
            lastUpdated.textContent = `최종 업데이트: ${date.toLocaleDateString('ko-KR')} ${date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
        }

        console.log('SEO Guidelines loaded:', versionInfo);
    } catch (error) {
        console.error('SEO Guidelines load error:', error);
    }
}

// ============================================================================
// SEO Update Actions
// ============================================================================

async function triggerSeoUpdate() {
    try {
        const result = await apiCall('/api/v1/admin/seo-guidelines/update', { method: 'POST' });
        showToast('SEO 업데이트가 완료되었습니다.', 'success');
        // Reload version info
        await loadSEOGuidelines();
        // Optionally refresh history
        await loadSeoUpdateHistory();
    } catch (error) {
        console.error('SEO update error:', error);
        showToast('SEO 업데이트에 실패했습니다.', 'error');
    }
}

async function loadSeoUpdateHistory() {
    try {
        const history = await apiCall('/api/v1/admin/seo-guidelines/history');
        const tbody = document.getElementById('seo-history-body');
        if (!tbody) return;
        tbody.innerHTML = history.map(item => {
            const date = new Date(item.updated_at);
            const formatted = date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
            return `
                <tr>
                    <td>${item.version}</td>
                    <td>${formatted}</td>
                    <td>${item.changes_summary || ''}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="rollbackSeoVersion('${item.version}')">Rollback</button>
                        <a href="${item.report_path}" target="_blank" class="btn btn-sm btn-outline-secondary ms-1">Report</a>
                    </td>
                </tr>
            `;
        }).join('');
        // Show the history section
        const section = document.getElementById('seo-update-history-section');
        if (section) section.style.display = 'block';
    } catch (error) {
        console.error('Failed to load SEO update history:', error);
        showToast('업데이트 이력 로드에 실패했습니다.', 'error');
    }
}

function closeSeoHistory() {
    const section = document.getElementById('seo-update-history-section');
    if (section) section.style.display = 'none';
}

async function rollbackSeoVersion(version) {
    if (!confirm(`버전 ${version}으로 롤백하시겠습니까?`)) return;
    try {
        const result = await apiCall(`/api/v1/admin/seo-guidelines/rollback/${version}`, { method: 'POST' });
        showToast('롤백이 완료되었습니다.', 'success');
        // Reload guidelines info
        await loadSEOGuidelines();
        // Refresh history
        await loadSeoUpdateHistory();
    } catch (error) {
        console.error('Rollback error:', error);
        showToast('롤백에 실패했습니다.', 'error');
    }
}


// ============================================================================
// Initialize
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {
    console.log('Admin Dashboard Initialized');

    // Load initial dashboard data
    loadDashboardStats();

    // Load SEO guidelines
    loadSEOGuidelines();

    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Add any global event listeners here
    console.log('Event listeners set up');
}
