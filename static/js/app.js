/**
 * VidSpectre Frontend - Mobile-First Refactor
 * Uses Tailwind CSS + vanilla JavaScript
 */

// Helper to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper to show toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg z-50 ' +
        (type === 'error' ? 'bg-red-600 text-white' : 'bg-gray-700 text-white');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Global functions exposed on window
window.fetchSubscription = fetchSubscription;
window.saveSubscription = saveSubscription;
window.toggleEpisodes = toggleEpisodes;

function fetchSubscription(btn) {
    if (btn.disabled) return;  // Guard against double-click
    const subId = btn.dataset.subId;
    btn.disabled = true;
    btn.textContent = '...';

    saveSubscription(subId)
        .then(() => {
            return fetch(`/api/subscriptions/${subId}/fetch`, { method: 'POST' });
        })
        .then(response => response.json())
        .then(data => {
            const row = btn.closest('.subscription-card');
            const latestCell = row.querySelector('.latest-episode');
            if (data.latest_episode && latestCell) {
                latestCell.textContent = data.latest_episode;
            }
            const episodesContent = document.getElementById('episodes-content-' + subId);
            const episodesRow = document.getElementById('episodes-' + subId);
            if (episodesContent && episodesRow && episodesRow.style.display !== 'none') {
                episodesContent.innerHTML = '';
                fetch(`/api/subscriptions/${subId}/episodes`)
                    .then(r => r.json())
                    .then(episodes => renderEpisodes(episodes, subId));
            }
        })
        .then(() => {
            btn.textContent = '✓';
        })
        .catch(() => {
            btn.textContent = '✗';
        })
        .finally(() => {
            btn.disabled = false;
            setTimeout(() => btn.textContent = '🔄', 1500);
        });
}

function saveSubscription(subId) {
    const episodeInput = document.querySelector(`.episode-input[data-sub-id="${subId}"]`);
    const keywordsInput = document.querySelector(`.keywords-input[data-sub-id="${subId}"]`);
    const currentEpisode = episodeInput ? episodeInput.value.trim() : '';
    const searchKeywords = keywordsInput ? keywordsInput.value.trim() : '';

    return fetch(`/api/subscriptions/${subId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_episode: currentEpisode, search_keywords: searchKeywords })
    })
    .then(response => response.json())
    .then(data => {
        if (episodeInput) {
            episodeInput.classList.add('border-green-500');
            setTimeout(() => episodeInput.classList.remove('border-green-500'), 1000);
        }
        if (keywordsInput) {
            keywordsInput.classList.add('border-green-500');
            setTimeout(() => keywordsInput.classList.remove('border-green-500'), 1000);
        }
    })
    .catch(err => {
        console.error('Failed to save subscription:', err);
        if (episodeInput) episodeInput.classList.add('border-red-500');
        if (keywordsInput) keywordsInput.classList.add('border-red-500');
    });
}

function toggleEpisodes(btn) {
    const subId = btn.dataset.subId;
    const row = document.getElementById('episodes-' + subId);
    const content = document.getElementById('episodes-content-' + subId);
    const loading = row ? row.querySelector('.episodes-loading') : null;
    const mediaType = btn.dataset.mediaType || 'tv';  // NEW LINE

    if (row && row.style.display === 'none') {
        row.style.display = 'block';
        btn.textContent = '收起';

        // NEW: Movie type - get links directly
        if (mediaType === 'movie') {
            fetch(`/api/subscriptions/${subId}/movie-links`)
                .then(r => r.json())
                .then(links => {
                    if (loading) loading.style.display = 'none';
                    renderMovieLinks(links, subId);
                })
                .catch(err => {
                    if (loading) loading.textContent = '加载失败';
                });
            return;
        }

        // TV type - existing logic (fetch episodes)
        fetch(`/api/subscriptions/${subId}/episodes`)
            .then(r => r.json())
            .then(episodes => {
                if (loading) loading.style.display = 'none';
                renderEpisodes(episodes, subId);
            })
            .catch(err => {
                if (loading) loading.textContent = '加载失败';
            });
    } else if (row) {
        row.style.display = 'none';
        btn.textContent = '展开';
    }
}

function renderEpisodes(episodes, subId) {
    const content = document.getElementById('episodes-content-' + subId);
    if (Object.keys(episodes).length === 0) {
        content.innerHTML = '<p class="text-gray-400">暂无可用剧集</p>';
        return;
    }
    const sorted = Object.keys(episodes).sort((a, b) => b - a);
    let html = '<div class="space-y-2">';
    sorted.forEach(ep => {
        html += `
        <div class="episode-item border border-gray-700 rounded-lg overflow-hidden">
            <button class="episode-header w-full text-left px-4 py-3 bg-gray-700 hover:bg-gray-650 flex justify-between items-center"
                    data-episode="${escapeHtml(ep)}">
                <span class="font-medium">第${escapeHtml(ep)}集</span>
                <span class="text-gray-400 text-sm">${episodes[ep].length} 个资源 ▾</span>
            </button>
            <div class="episode-links hidden p-3 bg-gray-750 space-y-2"></div>
        </div>`;
    });
    html += '</div>';
    content.innerHTML = html;

    // Bind click events for episode headers
    content.querySelectorAll('.episode-header').forEach(header => {
        header.addEventListener('click', function() {
            const ep = this.dataset.episode;
            const linksContainer = this.nextElementSibling;

            if (linksContainer.classList.contains('hidden')) {
                // Expand this episode's links
                linksContainer.classList.remove('hidden');
                this.querySelector('span:last-child').textContent = '收起 △';

                // Only render links if not already rendered
                if (!linksContainer.dataset.rendered) {
                    linksContainer.innerHTML = episodes[ep].map(link => `
                        <button class="get-magnet-link w-full text-left px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-blue-400 hover:text-blue-300"
                                data-url="${escapeHtml(link.url)}"
                                data-title="${escapeHtml(link.title)}">
                            ${escapeHtml(link.title)}
                        </button>
                    `).join('');
                    linksContainer.dataset.rendered = 'true';

                    // Bind click events for links
                    linksContainer.querySelectorAll('.get-magnet-link').forEach(linkBtn => {
                        linkBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            const originalText = this.textContent;
                            this.textContent = '获取中...';

                            // Remove any existing magnet display
                            const existingDisplay = this.parentElement.querySelector('.magnet-display');
                            if (existingDisplay) existingDisplay.remove();

                            fetch('/api/download-link?url=' + encodeURIComponent(this.dataset.url))
                                .then(r => r.json())
                                .then(d => {
                                    if (d.magnet) {
                                        const display = document.createElement('div');
                                        display.className = 'magnet-display mt-2 p-2 bg-gray-700 rounded text-xs break-all';
                                        display.innerHTML = '磁力：<span class="text-green-400 select-all cursor-pointer">' + escapeHtml(d.magnet) + '</span>';
                                        this.parentElement.appendChild(display);
                                    } else {
                                        showToast('获取失败', 'error');
                                    }
                                    this.textContent = originalText;
                                })
                                .catch(() => {
                                    showToast('获取失败', 'error');
                                    this.textContent = originalText;
                                });
                        });
                    });
                }
            } else {
                // Collapse
                linksContainer.classList.add('hidden');
                this.querySelector('span:last-child').textContent = `${episodes[ep].length} 个资源 ▾`;
            }
        });
    });
}

function renderMovieLinks(links, subId) {
    const content = document.getElementById('episodes-content-' + subId);
    if (!links || links.length === 0) {
        content.innerHTML = '<p class="text-gray-400">暂无可用资源</p>';
        return;
    }
    let html = '<div class="space-y-2">';
    links.forEach(link => {
        html += `
        <button class="get-magnet-link w-full text-left px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-blue-400 hover:text-blue-300"
                data-url="${escapeHtml(link.url)}"
                data-title="${escapeHtml(link.title || link.name || '')}">
            ${escapeHtml(link.title || link.name || '下载链接')}
        </button>`;
    });
    html += '</div>';
    content.innerHTML = html;

    // Bind click events for links
    content.querySelectorAll('.get-magnet-link').forEach(linkBtn => {
        linkBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const originalText = this.textContent;
            this.textContent = '获取中...';
            const existingDisplay = this.parentElement.querySelector('.magnet-display');
            if (existingDisplay) existingDisplay.remove();
            const url = this.dataset.url;
            if (url.startsWith('magnet:')) {
                // Direct magnet link - show it
                const magnetHtml = `<div class="magnet-display mt-2 p-2 bg-gray-750 rounded break-all">
                    <a href="${escapeHtml(url)}" class="text-blue-400 hover:text-blue-300 text-sm break-all">${escapeHtml(url)}</a>
                </div>`;
                this.insertAdjacentHTML('afterend', magnetHtml);
                this.textContent = originalText;
            } else {
                // Non-magnet URL - fetch actual magnet from API (same as TV episodes)
                fetch('/api/download-link?url=' + encodeURIComponent(url))
                    .then(r => r.json())
                    .then(data => {
                        if (data.magnet) {
                            const magnetHtml = `<div class="magnet-display mt-2 p-2 bg-gray-750 rounded break-all">
                                <a href="${escapeHtml(data.magnet)}" class="text-blue-400 hover:text-blue-300 text-sm break-all">${escapeHtml(data.magnet)}</a>
                            </div>`;
                            this.insertAdjacentHTML('afterend', magnetHtml);
                        }
                        this.textContent = originalText;
                    })
                    .catch(err => {
                        this.textContent = originalText;
                    });
            }
        });
    });
}

function initSaveButtons() {
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const subId = this.dataset.subId;
            saveSubscription(subId);
        });
    });
}

function initFetchButtons() {
    document.querySelectorAll('.fetch-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            fetchSubscription(this);
        });
    });
}

function initEpisodeToggles() {
    document.querySelectorAll('.toggle-episodes').forEach(btn => {
        btn.addEventListener('click', function() {
            toggleEpisodes(this);
        });
    });
}

function initDeleteForms() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('确定删除？')) {
                e.preventDefault();
            }
        });
    });
}

function initMoreMenus() {
    document.querySelectorAll('.more-menu-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            document.querySelectorAll('.more-menu').forEach(m => {
                if (m !== menu) m.classList.add('hidden');
            });
            menu.classList.toggle('hidden');
        });
    });

    document.addEventListener('click', function() {
        document.querySelectorAll('.more-menu').forEach(m => m.classList.add('hidden'));
    });
}

function initSearchKeyword() {
    const input = document.getElementById('search-keyword');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchMedia();
            }
        });
    }
}

function searchMedia() {
    const keyword = document.getElementById('search-keyword').value.trim();
    if (!keyword) return;

    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="p-3 text-gray-400">搜索中...</div>';

    fetch('/api/search?q=' + encodeURIComponent(keyword))
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            if (data.length === 0) {
                resultsDiv.innerHTML = '<div class="p-3 text-gray-400">未找到结果</div>';
                return;
            }
            data.forEach(item => {
                const div = document.createElement('div');
                div.className = 'p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700 flex items-center gap-3';
                // Cover image (clickable to enlarge)
                const img = document.createElement('img');
                img.src = item.cover_url || '';
                img.className = 'w-12 h-12 object-cover rounded flex-shrink-0 bg-gray-600 cursor-zoom-in hover:opacity-80 transition-opacity';
                img.onerror = function() {
                    this.style.display = 'none';
                    this.nextElementSibling.style.display = 'flex';
                };
                img.onclick = function(e) {
                    e.stopPropagation();
                    if (item.cover_url) {
                        openImgModal(item.cover_url);
                    }
                };
                const placeholder = document.createElement('div');
                placeholder.className = 'w-12 h-12 rounded flex-shrink-0 bg-gray-600 hidden items-center justify-center text-gray-400 text-xs';
                placeholder.textContent = '无图';
                div.appendChild(img);
                div.appendChild(placeholder);
                // Name
                const nameSpan = document.createElement('span');
                nameSpan.className = 'font-medium flex-1 truncate';
                nameSpan.textContent = item.name;
                div.appendChild(nameSpan);
                div.addEventListener('click', function() {
                    document.querySelector('input[name="media_name"]').value = item.name;
                    document.querySelector('input[name="media_id"]').value = item.media_id;
                    resultsDiv.innerHTML = '';
                });
                resultsDiv.appendChild(div);
            });
        })
        .catch(err => {
            resultsDiv.innerHTML = '<div class="p-3 text-red-400">搜索失败</div>';
        });
}

window.searchMedia = searchMedia;
window.openImgModal = openImgModal;
window.closeImgModal = closeImgModal;

function openImgModal(src) {
    const modal = document.getElementById('img-modal');
    const modalImg = document.getElementById('img-modal-content');
    modalImg.src = src;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeImgModal() {
    const modal = document.getElementById('img-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

document.addEventListener('DOMContentLoaded', function() {
    initSaveButtons();
    initFetchButtons();
    initEpisodeToggles();
    initDeleteForms();
    initMoreMenus();
    initSearchKeyword();
});
