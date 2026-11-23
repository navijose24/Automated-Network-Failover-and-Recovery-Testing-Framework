"""Generates high-resolution publication-quality architecture diagrams and experimental charts."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs("documentation/architecture", exist_ok=True)

# -------------------------------------------------------------
# 1. NETWORK TOPOLOGY DIAGRAM
# -------------------------------------------------------------
def create_network_topology_diagram():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_facecolor("#F8FAFC")
    fig.patch.set_facecolor("#F8FAFC")

    # Titles
    ax.text(6.5, 7.5, "Dual-Path Virtual Network Topology Architecture", fontsize=17, fontweight="bold",
            color="#101828", ha="center")
    ax.text(6.5, 7.15, "Isolated Linux Network Namespaces (iproute2) with Asymmetric Multi-Path Metric Routing",
            fontsize=11, color="#475467", ha="center")

    # Box styling helper
    def draw_node(x, y, w, h, title, subtitle, ip_text, bg_color, border_color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                      facecolor=bg_color, edgecolor=border_color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.35, title, fontsize=12, fontweight="bold", color="#101828", ha="center")
        ax.text(x + w/2, y + h - 0.7, subtitle, fontsize=9.5, fontweight="semibold", color="#0F766E", ha="center")
        for idx, line in enumerate(ip_text):
            ax.text(x + w/2, y + h - 1.1 - idx*0.32, line, fontsize=8.5, color="#344054", ha="center", fontfamily="monospace")

    # Client Node
    draw_node(4.75, 4.8, 3.5, 1.8, "Client Host", "Namespace: ns_client",
              ["veth_c_p: 10.0.1.2/24", "veth_c_b: 10.0.2.2/24", "Target: 10.50.0.1 (via metric 100/200)"],
              "#E0F2FE", "#0284C7")

    # Primary Router
    draw_node(1.2, 2.3, 3.8, 1.8, "Primary Router (Active)", "Namespace: ns_primary",
              ["Ingress: veth_p_c (10.0.1.1/24)", "Egress:  veth_p_s (10.0.3.1/24)", "Kernel Forwarding: enabled", "Metric: 100 (High Preference)"],
              "#DCFCE7", "#16A34A")

    # Backup Router
    draw_node(8.0, 2.3, 3.8, 1.8, "Backup Router (Standby)", "Namespace: ns_backup",
              ["Ingress: veth_b_c (10.0.2.1/24)", "Egress:  veth_b_s (10.0.4.1/24)", "Kernel Forwarding: enabled", "Metric: 200 (Failover: 50)"],
              "#FEF3C7", "#D97706")

    # Server Node
    draw_node(4.75, 0.2, 3.5, 1.6, "Destination Server", "Namespace: ns_server",
              ["veth_s_p: 10.0.3.2/24", "veth_s_b: 10.0.4.2/24", "Service Loopback: 10.50.0.1/32"],
              "#EDE9FE", "#7C3AED")

    # Arrows - Primary Path (Solid Teal / Green)
    ax.annotate("", xy=(3.1, 4.1), xytext=(5.3, 4.8),
                arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=2.5, mutation_scale=15))
    ax.text(3.7, 4.55, "Primary Link A (veth_c_p <-> veth_p_c)", fontsize=8.5, color="#15803D", fontweight="bold")

    ax.annotate("", xy=(5.3, 1.8), xytext=(3.1, 2.3),
                arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=2.5, mutation_scale=15))
    ax.text(3.7, 1.95, "Primary Link B (veth_p_s <-> veth_s_p)", fontsize=8.5, color="#15803D", fontweight="bold")

    # Arrows - Backup Path (Dashed Orange)
    ax.annotate("", xy=(9.9, 4.1), xytext=(7.7, 4.8),
                arrowprops=dict(arrowstyle="<->", color="#D97706", lw=2.2, linestyle="--", mutation_scale=15))
    ax.text(9.3, 4.55, "Backup Link A (veth_c_b <-> veth_b_c)", fontsize=8.5, color="#B45309", fontweight="bold")

    ax.annotate("", xy=(7.7, 1.8), xytext=(9.9, 2.3),
                arrowprops=dict(arrowstyle="<->", color="#D97706", lw=2.2, linestyle="--", mutation_scale=15))
    ax.text(9.3, 1.95, "Backup Link B (veth_b_s <-> veth_s_b)", fontsize=8.5, color="#B45309", fontweight="bold")

    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("documentation/architecture/network_topology.png", dpi=300)
    plt.close()
    print("Created network_topology.png")

# -------------------------------------------------------------
# 2. SYSTEM ARCHITECTURE DIAGRAM
# -------------------------------------------------------------
def create_system_architecture_diagram():
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)
    ax.set_facecolor("#F8FAFC")
    fig.patch.set_facecolor("#F8FAFC")

    ax.text(6.5, 8.0, "Automated Network Failover Testing Framework - System Architecture",
            fontsize=16, fontweight="bold", color="#101828", ha="center")
    ax.text(6.5, 7.65, "Multi-Tiered Architectural Interaction Model", fontsize=11, color="#475467", ha="center")

    tiers = [
        ("Layer 1: Presentation Tier", 6.2, 1.1, "#EFF6FF", "#2563EB", [
            "Web Dashboard (Bootstrap 5, Chart.js 4)",
            "Topology Visualizer & Interface Inspector",
            "Real-Time Telemetry & Live Loss/Latency Charts",
            "CSV Reporting & Pandas Aggregates Downloader"
        ]),
        ("Layer 2: Application / Controller Tier (Flask 3.0)", 4.7, 1.2, "#F0FDF4", "#16A34A", [
            "REST API Endpoints (/api/status, /api/failure, /api/session)",
            "Testing Session Lifecycle Controller",
            "Asynchronous Event Dispatcher & Callback Hub",
            "Report Generation & Master Dataset Exporter"
        ]),
        ("Layer 3: Core Network Engine Tier", 2.9, 1.5, "#FEF3C7", "#D97706", [
            "Network Topology Manager (Namespaces, Veth Pairs, IP Routing)",
            "High-Frequency ICMP Packet Monitor (0.2s-0.5s Resolution)",
            "Failure Simulation Engine (5 Disruption Profiles via iproute2)",
            "Automatic Failover Controller (Threshold Detection, Metric 50 Override)",
            "Failback Controller (Stability Verification & Metric Restoration)",
            "Recovery Analyzer (Monotonic Millisecond Precision Metric Engine)"
        ]),
        ("Layer 4: Virtualization & Persistence Tier", 0.9, 1.6, "#F5F3FF", "#7C3AED", [
            "Linux Network Subsystem (Kernel iproute2, NetNS, Sysctl IP Forwarding)",
            "SQLite High-Concurrency WAL Database (sessions, probe_records, network_events, session_metrics)",
            "Pandas Telemetry & Cross-Scenario Analytical Aggregation Engine"
        ])
    ]

    for title, y, h, bg, border, items in tiers:
        rect = patches.FancyBboxPatch((0.8, y), 11.4, h, boxstyle="round,pad=0.1",
                                      facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(1.2, y + h - 0.3, title, fontsize=12, fontweight="bold", color="#101828")
        
        # Draw items as badge pills
        x_cursor = 1.2
        y_cursor = y + h - 0.7
        for idx, itm in enumerate(items):
            itm_w = len(itm) * 0.105 + 0.3
            if x_cursor + itm_w > 11.8:
                x_cursor = 1.2
                y_cursor -= 0.38
            pill = patches.FancyBboxPatch((x_cursor, y_cursor - 0.12), itm_w, 0.3,
                                          boxstyle="round,pad=0.05", facecolor="#FFFFFF",
                                          edgecolor="#CBD5E1", linewidth=1)
            ax.add_patch(pill)
            ax.text(x_cursor + itm_w/2, y_cursor + 0.02, itm, fontsize=8.5, color="#334155", ha="center")
            x_cursor += itm_w + 0.25

    # Connect tiers with vertical arrows
    for y_arrow in [6.1, 4.6, 2.8]:
        ax.annotate("", xy=(6.5, y_arrow), xytext=(6.5, y_arrow + 0.2),
                    arrowprops=dict(arrowstyle="->", color="#64748B", lw=2.5, mutation_scale=15))

    ax.set_xlim(0, 13)
    ax.set_ylim(0.5, 8.5)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("documentation/architecture/system_architecture.png", dpi=300)
    plt.close()
    print("Created system_architecture.png")

# -------------------------------------------------------------
# 3. MODULE ARCHITECTURE & COMPONENT INTERACTION
# -------------------------------------------------------------
def create_module_architecture_diagram():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_facecolor("#F8FAFC")
    fig.patch.set_facecolor("#F8FAFC")

    ax.text(6.5, 7.6, "Module Architecture and Inter-Component Telemetry Flow",
            fontsize=16, fontweight="bold", color="#101828", ha="center")
    ax.text(6.5, 7.25, "Synchronous & Asynchronous Callback Communication Pipelines", fontsize=11, color="#475467", ha="center")

    modules = [
        ("PacketMonitor", 0.8, 4.5, 3.2, 2.2, "#EFF6FF", "#2563EB", [
            "Probing loop (0.2s ICMP)",
            "send_probe() via iproute2",
            "LatencyTracker (RTT, jitter)",
            "Callback Dispatcher"
        ]),
        ("FailoverController", 4.9, 4.5, 3.2, 2.2, "#FEF3C7", "#D97706", [
            "Threshold detection (N=3)",
            "Monotonic T0 registration",
            "replace_route() metric=50",
            "Active verification probe"
        ]),
        ("FailbackController", 9.0, 4.5, 3.2, 2.2, "#F0FDF4", "#16A34A", [
            "Stability probe (N=3)",
            "Health tick processor",
            "Primary metric=100 restore",
            "Standby metric=200 reset"
        ]),
        ("FailureEngine", 0.8, 1.2, 3.2, 2.2, "#FEE2E2", "#DC2626", [
            "5 Disruption scenarios",
            "ip link / sysctl execution",
            "Timer-based recovery",
            "Ground-truth start timing"
        ]),
        ("RecoveryAnalyzer", 4.9, 1.2, 3.2, 2.2, "#F3E8FF", "#9333EA", [
            "Detection time computation",
            "Recovery duration analysis",
            "Packet loss calculation",
            "Availability % derivation"
        ]),
        ("Database Models", 9.0, 1.2, 3.2, 2.2, "#F1F5F9", "#475467", [
            "create_session()",
            "log_probe() [62 records]",
            "log_event() [28 records]",
            "save_metrics() [100%]"
        ])
    ]

    for name, x, y, w, h, bg, border, items in modules:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                      facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.35, name, fontsize=12, fontweight="bold", color="#101828", ha="center")
        for idx, itm in enumerate(items):
            ax.text(x + 0.3, y + h - 0.75 - idx*0.35, f"• {itm}", fontsize=9, color="#334155")

    # Arrows
    # PacketMonitor -> FailoverController
    ax.annotate("Probe Stream", xy=(4.8, 5.6), xytext=(4.1, 5.6),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2, mutation_scale=14),
                fontsize=8.5, color="#1D4ED8", fontweight="bold", ha="center")
    # FailoverController -> FailbackController
    ax.annotate("Failover Event", xy=(8.9, 5.6), xytext=(8.2, 5.6),
                arrowprops=dict(arrowstyle="->", color="#D97706", lw=2, mutation_scale=14),
                fontsize=8.5, color="#B45309", fontweight="bold", ha="center")
    # FailureEngine -> FailoverController
    ax.annotate("T0 Failure Triggered", xy=(5.2, 4.4), xytext=(3.5, 3.4),
                arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2, mutation_scale=14),
                fontsize=8.5, color="#B91C1C", fontweight="bold", ha="center")
    # Failback -> Database
    ax.annotate("Events", xy=(10.6, 3.5), xytext=(10.6, 4.4),
                arrowprops=dict(arrowstyle="->", color="#16A34A", lw=2, mutation_scale=14))
    # Failover -> RecoveryAnalyzer
    ax.annotate("Recovery Timestamps", xy=(6.5, 3.5), xytext=(6.5, 4.4),
                arrowprops=dict(arrowstyle="->", color="#9333EA", lw=2, mutation_scale=14))
    # RecoveryAnalyzer -> Database
    ax.annotate("Calculated Metrics", xy=(8.9, 2.3), xytext=(8.2, 2.3),
                arrowprops=dict(arrowstyle="->", color="#475467", lw=2, mutation_scale=14),
                fontsize=8.5, color="#334155", fontweight="bold", ha="center")

    ax.set_xlim(0, 13)
    ax.set_ylim(0.5, 8.0)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("documentation/architecture/module_architecture.png", dpi=300)
    plt.close()
    print("Created module_architecture.png")

# -------------------------------------------------------------
# 4. DATA FLOW & FAILOVER TIMELINE SEQUENCE
# -------------------------------------------------------------
def create_data_flow_diagram():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_facecolor("#F8FAFC")
    fig.patch.set_facecolor("#F8FAFC")

    ax.text(6.5, 7.6, "Data Flow and Sequence: Failure Injection, Detection & Failover",
            fontsize=16, fontweight="bold", color="#101828", ha="center")
    ax.text(6.5, 7.25, "Closed-Loop Telemetry & Control Cycle in Monotonic Milliseconds",
            fontsize=11, color="#475467", ha="center")

    steps = [
        ("Step 1: Baseline Health", "ns_client routes via PRIMARY (metric 100)\nProbes succeed; 0% loss; RTT ~0.03ms", 1.2, "#DCFCE7", "#16A34A"),
        ("Step 2: Failure Injection (T0)", "FailureEngine drops link or gateway\nT0 monotonic timestamp logged to Controller", 3.0, "#FEE2E2", "#DC2626"),
        ("Step 3: Threshold Detection", "PacketMonitor logs 3 missed probes\nThreshold N=3 reached; declare failure", 4.8, "#FEF3C7", "#D97706"),
        ("Step 4: Backup Route Activation", "Kernel route replaced (metric 50)\nRoute cache flushed; backup ping verified", 6.6, "#E0F2FE", "#0284C7"),
        ("Step 5: Primary Restoration", "Link/gateway restored; N=3 stability verified\nFailbackController restores metric 100", 8.4, "#F3E8FF", "#7C3AED"),
        ("Step 6: Metrics Commitment", "RecoveryAnalyzer computes metrics\nProbe trace & stats committed to SQLite", 10.2, "#F1F5F9", "#475467")
    ]

    for title, desc, x, bg, border in steps:
        box = patches.FancyBboxPatch((x - 0.75, 2.5), 1.5, 3.6, boxstyle="round,pad=0.1",
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 5.8, title.split(":")[0], fontsize=10, fontweight="bold", color="#101828", ha="center")
        ax.text(x, 5.4, title.split(":")[1].strip(), fontsize=9, fontweight="semibold", color=border, ha="center")
        ax.text(x, 4.0, desc, fontsize=8.2, color="#334155", ha="center", wrap=True)

    # Sequence arrows
    for idx in range(len(steps) - 1):
        x1 = steps[idx][2] + 0.8
        x2 = steps[idx+1][2] - 0.8
        ax.annotate("", xy=(x2, 4.3), xytext=(x1, 4.3),
                    arrowprops=dict(arrowstyle="->", color="#475467", lw=2, mutation_scale=14))

    ax.set_xlim(0, 13)
    ax.set_ylim(1.5, 8.0)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("documentation/architecture/data_flow.png", dpi=300)
    plt.close()
    print("Created data_flow.png")

# -------------------------------------------------------------
# 5. EXPERIMENTAL CHARTS (BASED ON ACTUAL VERIFIED RESULTS)
# -------------------------------------------------------------
def create_experimental_charts():
    # Chart 1: Detection Time vs Recovery Time across failure scenarios
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")

    scenarios = [
        "Primary Link\nDisconnection",
        "Gateway\nUnavailability",
        "Primary Interface\nShutdown",
        "Repeated Failure\n(Gateway Avg)"
    ]
    # Actual verified experimental measurements from the runs
    detection_times = [4132.61, 3821.02, 1795.45, 4216.29]
    recovery_times = [4861.34, 4597.90, 2202.46, 4760.35]

    x = np.arange(len(scenarios))
    width = 0.35

    rects1 = ax.bar(x - width/2, detection_times, width, label="Failure Detection Time (ms)", color="#0284C7", edgecolor="#0369A1")
    rects2 = ax.bar(x + width/2, recovery_times, width, label="Total Failover Recovery Time (ms)", color="#0D9488", edgecolor="#0F766E")

    ax.set_ylabel("Duration in Milliseconds (ms)", fontsize=11, fontweight="bold", color="#101828")
    ax.set_title("Experimental Evaluation: Failure Detection vs. Total Recovery Duration", fontsize=13, fontweight="bold", color="#101828", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=10, fontweight="semibold")
    ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Add data labels
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f"{height:.1f} ms", xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f"{height:.1f} ms", xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    plt.savefig("documentation/architecture/experiment_recovery_chart.png", dpi=300)
    plt.close()
    print("Created experiment_recovery_chart.png")

    # Chart 2: Repeated Cycles Stability (Exp 6)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")

    cycles = ["Cycle 1", "Cycle 2", "Cycle 3"]
    det = [3977.90, 4276.74, 4394.24]
    rec = [4659.95, 4843.54, 4777.56]
    fb = [25.44, 23.81, 21.26]

    x = np.arange(len(cycles))
    ax.plot(cycles, det, marker="o", lw=2.5, color="#0284C7", label="Detection Time (ms)")
    ax.plot(cycles, rec, marker="s", lw=2.5, color="#0D9488", label="Recovery Time (ms)")
    ax.plot(cycles, fb, marker="^", lw=2.5, color="#D97706", label="Failback Duration (ms)")

    ax.set_ylabel("Duration (ms)", fontsize=11, fontweight="bold", color="#101828")
    ax.set_title("Repeated Failure & Recovery Testing: 3 Consecutive Cycles Consistency", fontsize=13, fontweight="bold", color="#101828", pad=15)
    ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)

    for i, txt in enumerate(rec):
        ax.annotate(f"{txt:.1f} ms", (cycles[i], rec[i]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5, fontweight="bold")
    for i, txt in enumerate(fb):
        ax.annotate(f"{txt:.1f} ms", (cycles[i], fb[i]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    plt.savefig("documentation/architecture/repeated_cycles_chart.png", dpi=300)
    plt.close()
    print("Created repeated_cycles_chart.png")

if __name__ == "__main__":
    create_network_topology_diagram()
    create_system_architecture_diagram()
    create_module_architecture_diagram()
    create_data_flow_diagram()
    create_experimental_charts()
    print("All architecture and experimental graphics generated successfully!")
