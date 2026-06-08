
//              BlazingSugarCookies — profileManagement.js

document.addEventListener('DOMContentLoaded', () => {

    const PM_I18N_SAFE = (typeof PM_I18N !== 'undefined' && PM_I18N) ? PM_I18N : {};
    const t = (key, replacements = {}) => {
        let text = PM_I18N_SAFE[key] || key;
        Object.entries(replacements).forEach(([name, value]) => {
            text = text.replace(`{${name}}`, String(value));
        });
        return text;
    };

    // ═════════════════════════════════════════════════════════════════════════
    //  THEME  — apply immediately so there is no flash of wrong theme
    // ═════════════════════════════════════════════════════════════════════════

    // PM_USER_THEME is injected by the template; fall back to localStorage then 'forest'
    const savedTheme = (typeof PM_USER_THEME !== 'undefined' && PM_USER_THEME)
        ? PM_USER_THEME
        : (localStorage.getItem('pm-color-theme') || 'forest');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme === 'forest' ? '' : theme);
        localStorage.setItem('pm-color-theme', theme);
        // Sync active state on swatches
        document.querySelectorAll('.pm-theme-swatch').forEach(btn => {
            btn.classList.toggle('pm-theme-swatch--active', btn.dataset.theme === theme);
        });
    }

    applyTheme(savedTheme);


    // ═════════════════════════════════════════════════════════════════════════
    //  TIMEZONE  — shared state used by clock + chat timestamps
    // ═════════════════════════════════════════════════════════════════════════

    const savedTz = (typeof PM_USER_TIMEZONE !== 'undefined' && PM_USER_TIMEZONE)
        ? PM_USER_TIMEZONE
        : (localStorage.getItem('pm-timezone') || 'local');

    let chatTimezone = savedTz;

    // Time format: '24h' or '12h'
    const savedFmt = (typeof PM_USER_TIME_FORMAT !== 'undefined' && PM_USER_TIME_FORMAT)
        ? PM_USER_TIME_FORMAT
        : (localStorage.getItem('pm-time-format') || '24h');

    let timeFormat = savedFmt;

    // Keep JS date/time formatting aligned with Django's active language.
    const activeLocale = (() => {
        const pageLang = (typeof PM_USER_LANGUAGE !== 'undefined' && PM_USER_LANGUAGE)
            ? PM_USER_LANGUAGE
            : document.documentElement.lang;
        const lang = (pageLang || 'en').toLowerCase();
        if (lang === 'zh-hans') return 'zh-CN';
        return lang;
    })();

    function tzLabel(tz) {
        if (!tz || tz === 'local') return t('local');
        // Extract city part: 'America/New_York' → 'New York'
        const parts = tz.split('/');
        return parts[parts.length - 1].replace(/_/g, ' ');
    }

    // Sync both tz selects (options tab + chat header) to the saved value
    function syncTzSelects(tz) {
        ['pm-options-tz', 'pm-chat-tz'].forEach(id => {
            const sel = document.getElementById(id);
            if (sel) { sel.value = tz; if (!sel.value) sel.value = 'local'; }
        });
        const label = document.getElementById('pm-clock-tz');
        if (label) label.textContent = tzLabel(tz);
    }

    syncTzSelects(savedTz);


    // ═════════════════════════════════════════════════════════════════════════
    //  LIVE CLOCK
    // ═════════════════════════════════════════════════════════════════════════

    const clockDisplay = document.getElementById('pm-clock-display');
    const clockDate    = document.getElementById('pm-clock-date');

    function tickClock() {
        if (!clockDisplay) return;
        const tz = (chatTimezone && chatTimezone !== 'local') ? chatTimezone : undefined;
        const hour12 = (timeFormat === '12h');
        const opts = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12 };
        if (tz) opts.timeZone = tz;
        clockDisplay.textContent = new Date().toLocaleTimeString(activeLocale, opts);
        if (clockDate) {
            const dateOpts = { month: 'long', day: 'numeric', ...(tz ? { timeZone: tz } : {}) };
            clockDate.textContent = new Date().toLocaleDateString(activeLocale, dateOpts);
        }
    }

    tickClock();
    setInterval(tickClock, 1000);


    // ── Order row expand / collapse ──────────────────────────────────────────
    document.querySelectorAll('.pm-order-row').forEach(row => {
        row.addEventListener('click', () => {
            const detail = document.getElementById(row.getAttribute('data-target'));
            if (detail) detail.classList.toggle('pm-detail-open');
        });
    });


    // ── Tab switcher ─────────────────────────────────────────────────────────
    const tabs   = document.querySelectorAll('.pm-tab');
    const panels = document.querySelectorAll('.pm-tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            tabs.forEach(t => { t.classList.toggle('pm-tab--active', t.dataset.tab === target); t.setAttribute('aria-selected', t.dataset.tab === target); });
            panels.forEach(p => p.classList.toggle('pm-tab-panel--active', p.id === `tab-${target}`));
            tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
        });
    });


    // ── Helpers ──────────────────────────────────────────────────────────────
    function csrfFetch(url, opts = {}) {
        return fetch(url, {
            ...opts,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN, ...(opts.headers || {}) },
            credentials: 'same-origin',
        });
    }

    function avatarLetter(name) {
        return (name || '?')[0].toUpperCase();
    }

    function showToast(msg, isError = false) {
        const t = document.createElement('div');
        t.style.cssText = `
            position:fixed;bottom:28px;left:50%;transform:translateX(-50%);
            background:${isError ? '#c0392b' : 'var(--bsc-green)'};color:#fff;
            padding:10px 24px;border-radius:8px;font-size:.93rem;font-weight:600;
            z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.25);pointer-events:none;
            transition:opacity .4s;
        `;
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 400); }, 2600);
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  FRIEND SEARCH  (live as-you-type)
    // ═════════════════════════════════════════════════════════════════════════

    const searchInput   = document.getElementById('pm-friend-search');
    const searchResults = document.getElementById('pm-search-results');

    let searchTimer = null;

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimer);
            const q = searchInput.value.trim();
            if (q.length < 2) {
                renderSearchHint(t('minCharsHint'));
                return;
            }
            renderSearchHint(t('searching'));
            searchTimer = setTimeout(() => runSearch(q), 300);
        });
    }

    async function runSearch(q) {
        try {
            const res  = await fetch(`${PM_URLS.searchUsers}?q=${encodeURIComponent(q)}`, { credentials: 'same-origin' });
            const data = await res.json();
            renderSearchResults(data.results || []);
        } catch {
            renderSearchHint(t('searchFailed'));
        }
    }

    function renderSearchHint(text) {
        searchResults.innerHTML = '';
        const div = document.createElement('div');
        div.className = 'pm-search-hint';
        div.textContent = text;
        searchResults.appendChild(div);
    }

    function renderSearchResults(results) {
        searchResults.innerHTML = '';
        if (!results.length) {
            renderSearchHint(t('noUsersFound'));
            return;
        }
        results.forEach(u => {
            const item = document.createElement('div');
            item.className = 'pm-search-result-item';

            const av = document.createElement('span');
            av.className = 'pm-friend-avatar';
            av.textContent = avatarLetter(u.username);

            const name = document.createElement('span');
            name.className = 'pm-friend-name';
            name.textContent = u.username;

            const btn = document.createElement('button');
            btn.className = 'pm-btn-sm';
            if (u.relationship === 'friend') {
                btn.className += ' pm-btn-pending';
                btn.textContent = t('friendsLabel');
                btn.disabled = true;
            } else if (u.relationship === 'pending') {
                btn.className += ' pm-btn-pending';
                btn.textContent = t('pendingLabel');
                btn.disabled = true;
            } else {
                btn.className += ' pm-btn-add';
                btn.textContent = t('addFriend');
                btn.addEventListener('click', () => sendFriendRequest(u.id, u.username, btn));
            }

            item.append(av, name, btn);
            searchResults.appendChild(item);
        });
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  SEND FRIEND REQUEST
    // ═════════════════════════════════════════════════════════════════════════

    async function sendFriendRequest(receiverId, username, btn) {
        btn.disabled = true;
        btn.textContent = t('sending');
        try {
            const res  = await csrfFetch(PM_URLS.sendRequest, { method: 'POST', body: JSON.stringify({ receiver_id: receiverId }) });
            const data = await res.json();
            if (data.success) {
                btn.textContent = t('pendingLabel');
                btn.className = 'pm-btn-sm pm-btn-pending';
                showToast(t('friendRequestSent', { username }));
            } else {
                btn.disabled = false;
                btn.textContent = t('addFriend');
                showToast(data.error || t('couldNotSendRequest'), true);
            }
        } catch {
            btn.disabled = false;
            btn.textContent = t('addFriend');
            showToast(t('networkErrorRetry'), true);
        }
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  RESPOND TO FRIEND REQUEST  (accept / decline)
    // ═════════════════════════════════════════════════════════════════════════

    const requestsList = document.getElementById('pm-requests-list');
    const reqBadge     = document.getElementById('pm-req-badge');
    const tabBadge     = document.querySelector('.pm-tab-badge');

    function updateRequestBadge(count) {
        if (reqBadge) {
            reqBadge.textContent = count;
            reqBadge.classList.toggle('pm-req-badge--hidden', count === 0);
        }
        if (tabBadge) {
            tabBadge.textContent = count;
            tabBadge.style.display = count ? '' : 'none';
        }
    }

    if (requestsList) {
        requestsList.addEventListener('click', async e => {
            const acceptBtn  = e.target.closest('.pm-btn-accept');
            const declineBtn = e.target.closest('.pm-btn-decline');
            const btn = acceptBtn || declineBtn;
            if (!btn) return;

            const action    = acceptBtn ? 'accept' : 'decline';
            const requestId = btn.dataset.requestId;
            const li        = btn.closest('.pm-friend-item');

            btn.disabled = true;
            try {
                const url  = `/friends/request/${requestId}/respond/`;
                const res  = await csrfFetch(url, { method: 'POST', body: JSON.stringify({ action }) });
                const data = await res.json();
                if (data.success) {
                    li.remove();
                    const remaining = requestsList.querySelectorAll('.pm-friend-item').length;
                    updateRequestBadge(remaining);
                    if (remaining === 0) {
                        const empty = document.createElement('li');
                        empty.className = 'pm-empty-note';
                        empty.id = 'pm-no-requests';
                        empty.textContent = t('noPendingRequests');
                        requestsList.appendChild(empty);
                    }
                    if (action === 'accept' && data.friend) {
                        addFriendToList(data.friend);
                        showToast(t('nowFriends', { username: data.friend.username }));
                    } else {
                        showToast(t('requestDeclined'));
                    }
                } else {
                    btn.disabled = false;
                    showToast(data.error || t('actionFailed'), true);
                }
            } catch {
                btn.disabled = false;
                showToast(t('networkError'), true);
            }
        });
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  ADD / REMOVE FRIENDS  (friends list DOM helpers)
    // ═════════════════════════════════════════════════════════════════════════

    const friendsList  = document.getElementById('pm-friends-list');
    const friendCount  = document.getElementById('pm-friend-count');

    function updateFriendCount() {
        if (!friendCount || !friendsList) return;
        const n = friendsList.querySelectorAll('.pm-friend-item').length;
        friendCount.textContent = n;
    }

    function addFriendToList(friend) {
        if (!friendsList) return;
        document.getElementById('pm-no-friends')?.remove();
        const li = buildFriendLi(friend.id, friend.username);
        friendsList.appendChild(li);
        updateFriendCount();
    }

    function buildFriendLi(id, username) {
        const li = document.createElement('li');
        li.className = 'pm-friend-item';
        li.dataset.friendId = id;
        li.dataset.friendUsername = username;

        const av = document.createElement('span');
        av.className = 'pm-friend-avatar';
        av.textContent = avatarLetter(username);

        const nm = document.createElement('span');
        nm.className = 'pm-friend-name';
        nm.textContent = username;

        const actions = document.createElement('div');
        actions.className = 'pm-friend-actions';

        const msgBtn = document.createElement('button');
        msgBtn.className = 'pm-btn-sm pm-btn-message';
        msgBtn.dataset.friendId = id;
        msgBtn.dataset.friendUsername = username;
        msgBtn.textContent = t('message');

        const rmBtn = document.createElement('button');
        rmBtn.className = 'pm-btn-sm pm-btn-remove';
        rmBtn.dataset.friendId = id;
        rmBtn.dataset.friendUsername = username;
        rmBtn.textContent = t('remove');

        const unreadDot = document.createElement('span');
        unreadDot.className = 'pm-unread-dot pm-unread-dot--hidden';
        unreadDot.id = `pm-unread-${id}`;

        actions.append(msgBtn, rmBtn);
        li.append(av, nm, unreadDot, actions);
        return li;
    }

    // Remove friend
    if (friendsList) {
        friendsList.addEventListener('click', async e => {
            const removeBtn = e.target.closest('.pm-btn-remove');
            const messageBtn = e.target.closest('.pm-btn-message');

            if (removeBtn) {
                const friendId = removeBtn.dataset.friendId;
                const friendName = removeBtn.dataset.friendUsername;
                if (!confirm(t('confirmRemoveFriend', { username: friendName }))) return;
                removeBtn.disabled = true;
                try {
                    const res  = await csrfFetch(`/friends/remove/${friendId}/`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) {
                        removeBtn.closest('.pm-friend-item').remove();
                        updateFriendCount();
                        if (!friendsList.querySelector('.pm-friend-item')) {
                            const empty = document.createElement('li');
                            empty.className = 'pm-empty-note';
                            empty.id = 'pm-no-friends';
                            empty.textContent = t('noFriendsYet');
                            friendsList.appendChild(empty);
                        }
                        showToast(t('friendRemoved', { username: friendName }));
                        if (currentChatUserId === parseInt(friendId)) closeChat();
                    } else {
                        removeBtn.disabled = false;
                        showToast(data.error || t('couldNotRemoveFriend'), true);
                    }
                } catch {
                    removeBtn.disabled = false;
                    showToast(t('networkError'), true);
                }
            }

            if (messageBtn) {
                openChat(parseInt(messageBtn.dataset.friendId), messageBtn.dataset.friendUsername);
            }
        });
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  CHAT PANEL
    // ═════════════════════════════════════════════════════════════════════════

    const chatPanel    = document.getElementById('pm-chat-panel');
    const chatOverlay  = document.getElementById('pm-chat-overlay');
    const chatTitle    = document.getElementById('pm-chat-title');
    const chatMessages = document.getElementById('pm-chat-messages');
    const chatForm     = document.getElementById('pm-chat-form');
    const chatInput    = document.getElementById('pm-chat-input');
    const chatClose    = document.getElementById('pm-chat-close');
    const tzSelect     = document.getElementById('pm-chat-tz');

    // Sync chat tz select and re-render metas when it changes
    tzSelect?.addEventListener('change', () => {
        chatTimezone = tzSelect.value;
        syncTzSelects(chatTimezone);
        rerenderMetas();
        saveOptions({ timezone: chatTimezone });
    });

    let currentChatUserId = null;
    let pollTimer = null;
    let lastMessageId = 0;

    function openChat(userId, username) {
        currentChatUserId = userId;
        lastMessageId = 0;
        chatTitle.textContent = t('chatWith', { username });
        chatMessages.innerHTML = '';
        chatPanel.classList.add('pm-chat-panel--open');
        chatPanel.setAttribute('aria-hidden', 'false');
        chatOverlay.classList.add('pm-chat-overlay--open');
        chatInput.focus();
        // Clear this friend's unread dot immediately (server marks read on fetch)
        clearUnreadDot(userId);
        loadMessages(userId);
        startPolling(userId);
    }

    function closeChat() {
        stopPolling();
        chatPanel.classList.remove('pm-chat-panel--open');
        chatPanel.setAttribute('aria-hidden', 'true');
        chatOverlay.classList.remove('pm-chat-overlay--open');
        currentChatUserId = null;
    }

    chatClose?.addEventListener('click', closeChat);
    chatOverlay?.addEventListener('click', closeChat);

    async function loadMessages(userId) {
        try {
            const res  = await fetch(`/messages/${userId}/`, { credentials: 'same-origin' });
            const data = await res.json();
            if (data.error) { showToast(data.error, true); return; }
            chatMessages.innerHTML = '';
            if (!data.messages.length) {
                const em = document.createElement('div');
                em.className = 'pm-chat-empty';
                em.textContent = t('noMessagesYet');
                chatMessages.appendChild(em);
            } else {
                data.messages.forEach(appendBubble);
                lastMessageId = data.messages.at(-1).id;
            }
            scrollChatToBottom();
        } catch {
            // silently ignore poll errors
        }
    }

    async function pollMessages(userId) {
        if (currentChatUserId !== userId) return;
        try {
            const res  = await fetch(`/messages/${userId}/`, { credentials: 'same-origin' });
            const data = await res.json();
            if (!data.messages) return;
            const newOnes = data.messages.filter(m => m.id > lastMessageId);
            if (newOnes.length) {
                // Remove the "no messages" placeholder if present
                chatMessages.querySelector('.pm-chat-empty')?.remove();
                const wasAtBottom = chatMessages.scrollHeight - chatMessages.scrollTop <= chatMessages.clientHeight + 40;
                newOnes.forEach(appendBubble);
                lastMessageId = newOnes.at(-1).id;
                if (wasAtBottom) scrollChatToBottom();
            }
        } catch { /* ignore */ }
    }

    function startPolling(userId) {
        stopPolling();
        pollTimer = setInterval(() => pollMessages(userId), 3000);
    }

    function stopPolling() {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }


    // ═════════════════════════════════════════════════════════════════════════
    //  UNREAD MESSAGE NOTIFICATIONS
    // ═════════════════════════════════════════════════════════════════════════

    const tabMsgBadge = document.getElementById('pm-tab-msg-badge');
    let unreadPollTimer = null;

    function clearUnreadDot(userId) {
        const dot = document.getElementById(`pm-unread-${userId}`);
        if (dot) {
            dot.textContent = '';
            dot.classList.add('pm-unread-dot--hidden');
        }
    }

    function updateUnreadBadges(total, bySender) {
        if (tabMsgBadge) {
            tabMsgBadge.textContent = total;
            tabMsgBadge.classList.toggle('pm-tab-badge--hidden', total === 0);
        }
        document.querySelectorAll('.pm-unread-dot').forEach(dot => {
            const friendId = dot.id.replace('pm-unread-', '');
            const count = bySender[friendId] || 0;
            // Don't show dot for whoever we currently have open (messages are being read)
            const isActive = currentChatUserId && currentChatUserId.toString() === friendId;
            dot.textContent = count > 0 ? count : '';
            dot.classList.toggle('pm-unread-dot--hidden', count === 0 || isActive);
        });
    }

    async function pollUnread() {
        if (!PM_URLS.getUnreadCount) return;
        try {
            const res  = await fetch(PM_URLS.getUnreadCount, { credentials: 'same-origin' });
            const data = await res.json();
            updateUnreadBadges(data.total || 0, data.by_sender || {});
        } catch { /* silently ignore */ }
    }

    function startUnreadPoll() {
        pollUnread();
        unreadPollTimer = setInterval(pollUnread, 5000);
    }

    startUnreadPoll();

    // ─── Timestamp formatting ──────────────────────────────────────────────
    function formatMsgTime(isoString) {
        const d = new Date(isoString);
        const tz = (chatTimezone && chatTimezone !== 'local') ? chatTimezone : undefined;
        const opts = tz ? { timeZone: tz } : {};
        const hour12 = (timeFormat === '12h');
        const dDay  = d.toLocaleDateString(activeLocale, { ...opts, year: 'numeric', month: '2-digit', day: '2-digit' });
        const today = new Date().toLocaleDateString(activeLocale, { ...opts, year: 'numeric', month: '2-digit', day: '2-digit' });
        const time  = d.toLocaleTimeString(activeLocale, { ...opts, hour: '2-digit', minute: '2-digit', hour12 });
        if (dDay === today) return time;
        const date  = d.toLocaleDateString(activeLocale, { ...opts, month: 'short', day: 'numeric' });
        return `${date}, ${time}`;
    }

    function rerenderMetas() {
        chatMessages?.querySelectorAll('[data-created-at]').forEach(meta => {
            meta.textContent = formatMsgTime(meta.dataset.createdAt);
        });
    }

    function appendBubble(msg) {
        const wrap = document.createElement('div');
        wrap.style.display = 'flex';
        wrap.style.flexDirection = 'column';
        wrap.style.alignItems = msg.is_mine ? 'flex-end' : 'flex-start';

        const bubble = document.createElement('div');
        bubble.className = `pm-chat-bubble ${msg.is_mine ? 'pm-chat-bubble--mine' : 'pm-chat-bubble--theirs'}`;
        bubble.textContent = msg.content;   // textContent prevents XSS

        const meta = document.createElement('div');
        meta.className = 'pm-chat-bubble-meta';
        meta.dataset.createdAt = msg.created_at || msg.timestamp || '';
        meta.textContent = msg.created_at ? formatMsgTime(msg.created_at) : (msg.timestamp || '');

        wrap.append(bubble, meta);
        chatMessages.appendChild(wrap);
    }

    function scrollChatToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Send message
    chatForm?.addEventListener('submit', async e => {
        e.preventDefault();
        const content = chatInput.value.trim();
        if (!content || !currentChatUserId) return;
        chatInput.value = '';

        try {
            const res  = await csrfFetch(PM_URLS.sendMessage, {
                method: 'POST',
                body: JSON.stringify({ receiver_id: currentChatUserId, content }),
            });
            const data = await res.json();
            if (data.success) {
                chatMessages.querySelector('.pm-chat-empty')?.remove();
                appendBubble(data.message);
                lastMessageId = data.message.id;
                scrollChatToBottom();
            } else {
                showToast(data.error || t('couldNotSendMessage'), true);
                chatInput.value = content;
            }
        } catch {
            showToast(t('networkError'), true);
            chatInput.value = content;
        }
    });

    // Close chat on Escape
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && currentChatUserId) closeChat();
    });


    // ═════════════════════════════════════════════════════════════════════════
    //  OPTIONS TAB  — timezone + color theme
    // ═════════════════════════════════════════════════════════════════════════

    async function saveOptions(payload) {
        if (!PM_URLS.saveOptions) return;
        try {
            await csrfFetch(PM_URLS.saveOptions, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
        } catch { /* silently ignore — preference is already applied locally */ }
    }

    // Options tab timezone select
    const optsTzSelect = document.getElementById('pm-options-tz');
    if (optsTzSelect) {
        optsTzSelect.value = chatTimezone;
        if (!optsTzSelect.value) optsTzSelect.value = 'local';

        optsTzSelect.addEventListener('change', () => {
            chatTimezone = optsTzSelect.value;
            syncTzSelects(chatTimezone);
            localStorage.setItem('pm-timezone', chatTimezone);
            rerenderMetas();
            saveOptions({ timezone: chatTimezone });
        });
    }

    // Color theme swatches
    document.querySelectorAll('.pm-theme-swatch').forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            applyTheme(theme);
            saveOptions({ color_theme: theme });
        });
    });

    // Mark the active swatch on load
    const initTheme = localStorage.getItem('pm-color-theme') || savedTheme;
    document.querySelectorAll('.pm-theme-swatch').forEach(btn => {
        btn.classList.toggle('pm-theme-swatch--active', btn.dataset.theme === initTheme);
    });

    // Time format buttons
    function applyTimeFormat(fmt) {
        timeFormat = fmt;
        localStorage.setItem('pm-time-format', fmt);
        document.querySelectorAll('.pm-time-format-btn').forEach(btn => {
            btn.classList.toggle('pm-time-format-btn--active', btn.dataset.fmt === fmt);
        });
        rerenderMetas();
        tickClock();
    }

    document.querySelectorAll('.pm-time-format-btn').forEach(btn => {
        btn.classList.toggle('pm-time-format-btn--active', btn.dataset.fmt === timeFormat);
        btn.addEventListener('click', () => {
            applyTimeFormat(btn.dataset.fmt);
            saveOptions({ time_format: btn.dataset.fmt });
        });
    });


    // ═════════════════════════════════════════════════════════════════════════
    //  OPTIONS TAB  — language
    // ═════════════════════════════════════════════════════════════════════════

    const savedLang = (typeof PM_USER_LANGUAGE !== 'undefined' && PM_USER_LANGUAGE)
        ? PM_USER_LANGUAGE
        : 'en';

    function applyLangActive(lang) {
        document.querySelectorAll('.pm-lang-btn').forEach(btn => {
            btn.classList.toggle('pm-lang-btn--active', btn.dataset.lang === lang);
        });
    }

    applyLangActive(savedLang);

    document.querySelectorAll('.pm-lang-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const lang = btn.dataset.lang;
            if (lang === savedLang) return;
            applyLangActive(lang);
            try {
                await csrfFetch(PM_URLS.saveOptions, {
                    method: 'POST',
                    body: JSON.stringify({ language: lang }),
                });
            } catch { /* best-effort */ }
            // Reload so the server renders the page in the new language
            window.location.reload();
        });
    });

});
