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

    if (row && row.style.display === 'none') {
        row.style.display = 'block';
        btn.textContent = '收起';

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
    let html = '<div class="space-y-3">';
    sorted.forEach(ep => {
        const links = episodes[ep];
        html += `
        <div class="border-b border-gray-700 pb-2">
            <div class="flex justify-between items-center">
                <span class="font-medium">第${escapeHtml(ep)}集</span>
                <button class="get-magnet-link text-blue-400 hover:text-blue-300 text-sm"
                        data-url="${escapeHtml(links[0].url)}"
                        data-title="${escapeHtml(links[0].title.substring(0, 30))}">
                    获取
                </button>
            </div>
        </div>`;
    });
    html += '</div>';
    content.innerHTML = html;

    content.querySelectorAll('.get-magnet-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            this.textContent = '获取中...';
            fetch('/api/download-link?url=' + encodeURIComponent(this.dataset.url))
                .then(r => r.json())
                .then(d => {
                    if (d.magnet) {
                        prompt('磁力链接:', d.magnet);
                        this.textContent = '获取';
                    } else {
                        alert('获取失败');
                        this.textContent = this.dataset.title;
                    }
                })
                .catch(() => {
                    alert('获取失败');
                    this.textContent = '获取';
                });
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

function initIntervalSelectors() {
    document.querySelectorAll('.interval-select').forEach(select => {
        select.addEventListener('change', function() {
            const subId = this.dataset.subId;
            const customInput = document.querySelector(`.custom-cron[data-sub-id="${subId}"]`);
            const wrapper = customInput ? customInput.parentElement : null;

            if (this.value === 'custom') {
                wrapper && wrapper.classList.remove('hidden');
                customInput && customInput.focus();
            } else {
                wrapper && wrapper.classList.add('hidden');
                saveInterval(subId, this.value);
            }
        });
    });

    document.querySelectorAll('.custom-cron').forEach(input => {
        input.addEventListener('blur', function() {
            const subId = this.dataset.subId;
            if (this.value.trim()) {
                saveInterval(subId, this.value.trim());
            }
        });
    });
}

function saveInterval(subId, cron) {
    fetch(`/api/subscriptions/${subId}/interval`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_cron: cron })
    }).catch(err => console.error('Failed to save interval:', err));
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
                const badge = item.media_type === 'movie' ? '电影' : '电视剧';
                const div = document.createElement('div');
                div.className = 'p-3 border-b border-gray-700 cursor-pointer hover:bg-gray-700';
                const nameSpan = document.createElement('span');
                nameSpan.className = 'font-medium';
                nameSpan.textContent = item.name;
                const badgeSpan = document.createElement('span');
                badgeSpan.className = 'text-xs bg-gray-600 px-2 py-1 rounded';
                badgeSpan.textContent = badge;
                div.appendChild(nameSpan);
                div.appendChild(badgeSpan);
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

document.addEventListener('DOMContentLoaded', function() {
    initSaveButtons();
    initFetchButtons();
    initEpisodeToggles();
    initDeleteForms();
    initIntervalSelectors();
    initMoreMenus();
    initSearchKeyword();
});
