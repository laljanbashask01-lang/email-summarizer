const API_BASE = "";
let ws = null;
let emails = [];
let currentFilter = "all";

// DOM elements
const btnLogin = document.getElementById("btn-login");
const btnFetch = document.getElementById("btn-fetch");
const emailList = document.getElementById("email-list");
const toast = document.getElementById("notification-toast");
const toastTitle = document.getElementById("toast-title");
const toastMessage = document.getElementById("toast-message");

// Check if authenticated
const params = new URLSearchParams(window.location.search);
if (params.get("authenticated") === "true") {
    btnLogin.textContent = "✓ Connected";
    btnLogin.disabled = true;
    btnFetch.disabled = false;
    window.history.replaceState({}, "", "/");
    connectWebSocket();
    loadEmails();
}

// Event listeners
btnLogin.addEventListener("click", () => {
    window.location.href = "/auth/login";
});

btnFetch.addEventListener("click", async () => {
    btnFetch.textContent = "Analyzing...";
    btnFetch.disabled = true;

    try {
        const res = await fetch("/api/fetch-emails", { method: "POST" });
        const data = await res.json();

        if (data.processed > 0) {
            showToast("New Emails", `Analyzed ${data.processed} new email(s)`);
        } else {
            showToast("No New Emails", "All emails are already processed");
        }
        await loadEmails();
    } catch (err) {
        showToast("Error", "Failed to fetch emails");
        console.error(err);
    } finally {
        btnFetch.textContent = "Fetch & Analyze";
        btnFetch.disabled = false;
    }
});

// Filter buttons
document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter = btn.dataset.filter;
        renderEmails();
    });
});

// Load emails from API
async function loadEmails() {
    try {
        const res = await fetch("/api/emails");
        emails = await res.json();
        renderEmails();
        updateStats();
    } catch (err) {
        console.error("Failed to load emails:", err);
    }
}

// Filter emails
function getFilteredEmails() {
    if (currentFilter === "all") return emails;
    if (currentFilter === "high") return emails.filter(e => e.importance === "high");
    if (currentFilter === "spam") return emails.filter(e => e.spam_classification === "spam" || e.spam_classification === "phishing");
    if (currentFilter === "positive") return emails.filter(e => e.sentiment === "positive");
    if (currentFilter === "negative") return emails.filter(e => e.sentiment === "negative");
    return emails;
}

// Render email cards
function renderEmails() {
    const filtered = getFilteredEmails();
    if (filtered.length === 0) {
        emailList.innerHTML = '<p class="placeholder">No emails match this filter.</p>';
        return;
    }

    emailList.innerHTML = filtered.map(email => `
        <div class="email-card importance-${email.importance} ${email.threat_level === 'high' ? 'threat-high' : ''}">
            <div class="email-header">
                <span class="email-subject">${escapeHtml(email.subject)}</span>
                <div class="email-badges">
                    <span class="email-badge badge-${email.importance}">${email.importance}</span>
                    <span class="badge-sentiment sentiment-${email.sentiment}">${email.sentiment}</span>
                    <span class="badge-spam spam-${email.spam_classification}">${email.spam_classification}</span>
                </div>
            </div>
            <div class="email-sender">From: ${escapeHtml(email.sender)}</div>
            
            <div class="email-summary">
                <strong>Summary:</strong> ${escapeHtml(email.summary)}
            </div>

            <div class="email-analysis-grid">
                <div class="analysis-item">
                    <span class="analysis-label">Tone</span>
                    <span class="analysis-value badge-tone">${email.tone || 'unknown'}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Threat</span>
                    <span class="analysis-value threat-${email.threat_level || 'none'}">${email.threat_level || 'none'}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Reply</span>
                    <span class="analysis-value reply-${email.reply_urgency || 'no_reply_needed'}">${(email.reply_urgency || 'none').replace(/_/g, ' ')}</span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Spam Score</span>
                    <span class="analysis-value">${Math.round((email.spam_confidence || 0) * 100)}%</span>
                </div>
            </div>

            ${email.suggested_reply ? `
            <div class="suggested-reply">
                <strong>💡 Suggested Reply:</strong> ${escapeHtml(email.suggested_reply)}
            </div>` : ''}

            ${email.red_flags && email.red_flags.length > 0 ? `
            <div class="red-flags">
                <strong>🚩 Red Flags:</strong>
                ${email.red_flags.map(f => `<span class="red-flag-tag">${escapeHtml(f)}</span>`).join('')}
            </div>` : ''}

            ${email.emotional_cues && email.emotional_cues.length > 0 ? `
            <div class="email-emotions">
                ${email.emotional_cues.map(e => `<span class="emotion-tag">${e}</span>`).join('')}
            </div>` : ''}

            <div class="email-meta">
                <span class="email-category">${email.category}</span>
                <span>${formatDate(email.received_at)}</span>
                ${email.action_required ? '<span class="action-required">⚡ Action Required</span>' : ''}
            </div>
        </div>
    `).join("");
}

// Update stats bar
function updateStats() {
    const total = emails.length;
    const high = emails.filter(e => e.importance === "high").length;
    const spam = emails.filter(e => e.spam_classification === "spam" || e.spam_classification === "phishing").length;
    const positive = emails.filter(e => e.sentiment === "positive").length;
    const negative = emails.filter(e => e.sentiment === "negative").length;

    document.querySelector("#stat-total .stat-value").textContent = total;
    document.querySelector("#stat-high .stat-value").textContent = high;
    document.querySelector("#stat-spam .stat-value").textContent = spam;
    document.querySelector("#stat-positive .stat-value").textContent = positive;
    document.querySelector("#stat-negative .stat-value").textContent = negative;
}

// WebSocket for real-time notifications
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "new_email") {
            showToast(`New: ${msg.data.subject}`, msg.data.summary);
            loadEmails();
            playNotificationSound();
        }
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 5000);
    };
}

// Toast notification
function showToast(title, message) {
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    toast.classList.remove("hidden");

    if (Notification.permission === "granted") {
        new Notification(title, { body: message });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission();
    }

    setTimeout(() => toast.classList.add("hidden"), 5000);
}

// Play notification sound
function playNotificationSound() {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 800;
    gain.gain.value = 0.1;
    osc.start();
    osc.stop(ctx.currentTime + 0.15);
}

// Utilities
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}
