/**
 * Global JavaScript helper utilities and state synchronization for Network Failover Framework.
 */

// Toast notification helper
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const bgClass = type === "success" ? "bg-success" : type === "danger" ? "bg-danger" : type === "warning" ? "bg-warning text-dark" : "bg-primary";
    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0 show mb-2`;
    toastEl.setAttribute("role", "alert");
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    container.appendChild(toastEl);
    setTimeout(() => {
        toastEl.classList.remove("show");
        setTimeout(() => toastEl.remove(), 300);
    }, 4000);
}

// Global live poller for navbar status badges
async function updateGlobalStatus() {
    try {
        const res = await fetch("/api/status");
        if (!res.ok) return;
        const data = await res.json();

        // 1. Path badge
        const pathBadge = document.getElementById("nav-active-path");
        if (pathBadge && data.monitor) {
            const p = data.monitor.active_path || "UNKNOWN";
            pathBadge.innerText = p;
            pathBadge.className = `status-pill ${p.toLowerCase()}`;
        }

        // 2. Network state badge
        const netBadge = document.getElementById("nav-net-status");
        if (netBadge && data.topology) {
            const isUp = data.topology.primary_path_status === "UP" || data.topology.backup_path_status === "UP";
            netBadge.innerText = isUp ? "ONLINE" : "OFFLINE";
            netBadge.className = `status-pill ${isUp ? "up" : "down"}`;
        }

        // 3. Active session badge
        const sessionBadge = document.getElementById("nav-session-status");
        if (sessionBadge) {
            if (data.is_session_active) {
                sessionBadge.innerText = `SESSION #${data.session_id}`;
                sessionBadge.className = "status-pill healthy";
            } else {
                sessionBadge.innerText = "IDLE";
                sessionBadge.className = "status-pill idle";
            }
        }
    } catch (e) {
        console.debug("Status poll error:", e);
    }
}

// Action Helpers
async function setupTopology() {
    try {
        showToast("Provisioning virtual network namespaces...", "info");
        const res = await fetch("/api/topology/setup", { method: "POST" });
        const json = await res.json();
        if (json.success) {
            showToast("Network topology provisioned successfully!", "success");
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(`Setup error: ${json.error}`, "danger");
        }
    } catch (e) {
        showToast(`Setup request failed: ${e}`, "danger");
    }
}

async function teardownTopology() {
    if (!confirm("Are you sure you want to clean up all virtual network namespaces?")) return;
    try {
        showToast("Tearing down virtual network namespaces...", "info");
        const res = await fetch("/api/topology/teardown", { method: "POST" });
        const json = await res.json();
        showToast(json.message || "Topology torn down.", "success");
        setTimeout(() => location.reload(), 1000);
    } catch (e) {
        showToast(`Teardown request failed: ${e}`, "danger");
    }
}

async function triggerManualFailover() {
    try {
        showToast("Triggering manual failover to BACKUP...", "warning");
        const res = await fetch("/api/failover/manual", { method: "POST" });
        const json = await res.json();
        if (json.success) {
            showToast(`Failover activated! Route switched to ${json.active_path}`, "success");
        } else {
            showToast(`Failover failed: ${json.error || "Unknown error"}`, "danger");
        }
    } catch (e) {
        showToast(`Failover error: ${e}`, "danger");
    }
}

async function triggerManualFailback() {
    try {
        showToast("Triggering manual failback to PRIMARY...", "info");
        const res = await fetch("/api/failback/manual", { method: "POST" });
        const json = await res.json();
        if (json.success) {
            showToast("Failback completed! Traffic restored to PRIMARY.", "success");
        } else {
            showToast(`Failback failed: ${json.error || "Primary check failed"}`, "danger");
        }
    } catch (e) {
        showToast(`Failback error: ${e}`, "danger");
    }
}

async function toggleAutoFailback(checkbox) {
    try {
        const enabled = checkbox.checked;
        const res = await fetch("/api/failback/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled })
        });
        const json = await res.json();
        showToast(`Auto-failback ${enabled ? "enabled" : "disabled"}.`, "info");
    } catch (e) {
        showToast("Failed to update auto-failback setting.", "danger");
    }
}

// Start polling on load
document.addEventListener("DOMContentLoaded", () => {
    updateGlobalStatus();
    setInterval(updateGlobalStatus, 1500);
});
