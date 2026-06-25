const API_BASE = "";
let ws = null;
let emails = [];

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
    btnFetch.textContent = "Fetching...";
    btnFetch.disabled = true;

    try {
        const res = await fetch("/api/fetch-emails", { method: "POST" });
        const data = await res.json();

        if (data.processed > 0) {
            showToast("New Emails", `Processed ${data.processed} new email(s)`);
        } else {
            showToast("No New Emails", "All emails are already processed");
        }

        await loadEmails();
    } catch (err) {
        showToast("Error", "Failed to fetch emails");
        console.error(err);
    } finally {
        btnFetch.textContent = "Fetch Emails";
        btnFetch.disabled = false;
    }
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

// Render email cards
function renderEmails() {
    if (emails.length === 0) {
        emailList.innerHTML = '<p class="placeholder">No emails processed yet. Click "Fetch Emails" to get started.</p>';
        return;
    }

    emailList.innerHTML = emails.map(email => `
        <div class="email-card importance-${email.importance}">
            <div class="email-header">
                <span class="email-subject">${escapeHtml(email.subject)}</span>
                <span class="email-badge badge-${email.importance}">${email.importance}</span>
            </div>
            <div class="email-sender">From: ${escapeHtml(email.sender)}</div>
            <div class="email-summary">${escapeHtml(email.summary)}</div>
            <div class="email-meta">
                <span class="email-category">${email.category}</span>
                <span>${formatDate(email.received_at)}</span>
                ${email.action_required ? '<span style="color: #ef4444;">⚡ Action Required</span>' : ""}
            </div>
        </div>
    `).join("");
}

// Update stats bar
function updateStats() {
    const total = emails.length;
    const high = emails.filter(e => e.importance === "high").length;
    const medium = emails.filter(e => e.importance === "medium").length;
    const low = emails.filter(e => e.importance === "low").length;

    document.querySelector("#stat-total .stat-value").textContent = total;
    document.querySelector("#stat-high .stat-value").textContent = high;
    document.querySelector("#stat-medium .stat-value").textContent = medium;
    document.querySelector("#stat-low .stat-value").textContent = low;
}

// WebSocket for real-time notifications
function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "new_email") {
            showToast(
                `New: ${msg.data.subject}`,
                msg.data.summary
            );
            loadEmails(); // Refresh the list
            playNotificationSound();
        }
    };

    ws.onclose = () => {
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };
}

// Toast notification
function showToast(title, message) {
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    toast.classList.remove("hidden");

    // Request browser notification permission
    if (Notification.permission === "granted") {
        new Notification(title, { body: message, icon: "📧" });
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
