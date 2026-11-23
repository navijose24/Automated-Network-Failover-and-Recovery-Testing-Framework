"""PowerPoint Presentation & Speaker Notes Generator for 10-Minute Academic Defense.
Aesthetic: Minimal Aesthetic Warm Editorial (Cream, Beige, Deep Charcoal/Black, and Mild Muted Accents).

Produces:
1. documentation/presentation/Project_Presentation.pptx (16:9 widescreen, minimal warm cream/beige/black aesthetic)
2. documentation/presentation/Presentation_Speaker_Notes.docx (Complete presentation script with cues, timings, transitions)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from docx import Document
from docx.shared import Inches as DocxInches, Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

os.makedirs("documentation/presentation", exist_ok=True)

# -------------------------------------------------------------
# PALETTE DEFINITIONS: Minimal Warm Editorial (Cream, Beige, Black, Mild Accents)
# -------------------------------------------------------------
C_DARK_BG   = RGBColor(22, 21, 20)      # #161514 (Deep warm black / charcoal)
C_DARK_CARD = RGBColor(34, 32, 30)      # #22201E (Subtle dark card)
C_DARK_BORDER = RGBColor(56, 53, 49)    # #383531

C_CREAM_BG  = RGBColor(250, 247, 242)   # #FAF7F2 (Editorial warm cream canvas)
C_CARD_BEIGE= RGBColor(240, 235, 225)   # #F0EBE1 (Soft beige card fill)
C_CARD_WHITE= RGBColor(255, 255, 255)   # #FFFFFF (Crisp white contrast card)
C_BORDER    = RGBColor(221, 214, 199)   # #DDD6C7 (Soft beige border)
C_BORDER_LIGHT = RGBColor(234, 229, 218)# #EAE5DA

# Typography colors
C_TEXT_DARK = RGBColor(24, 23, 22)      # #181716 (Deep black text)
C_TEXT_BODY = RGBColor(60, 57, 53)      # #3C3935 (Charcoal body text)
C_TEXT_MUTED= RGBColor(112, 107, 99)    # #706B63 (Muted taupe/slate)
C_TEXT_LIGHT= RGBColor(250, 247, 242)   # #FAF7F2 (Light cream text for dark slides)
C_TEXT_CREAM_MUTED = RGBColor(185, 179, 168) # #B9B3A8

# Mild muted accents
C_TERRACOTTA = RGBColor(188, 90, 54)    # #BC5A36 (Mild terracotta/rust for failure/loss)
C_SAGE       = RGBColor(77, 109, 83)    # #4D6D53 (Mild sage/olive for health/success)
C_OCHRE      = RGBColor(181, 135, 58)   # #B5873A (Mild warm ochre/amber for detection/timings)
C_SLATE_BLUE = RGBColor(75, 97, 120)    # #4B6178 (Mild slate blue for kernel/network)
C_SAND       = RGBColor(214, 203, 185)   # #D6CBB9 (Pill background)

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

FONT_HEADING = "Calibri"
FONT_BODY    = "Calibri"

def set_slide_background(slide, color=C_CREAM_BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_pill(slide, left, top, width, height, text, bg_color=C_CARD_BEIGE, border_color=C_BORDER, text_color=C_TEXT_BODY, font_size=9):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = FONT_BODY
    p.font.size = Pt(font_size)
    p.font.bold = True
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER
    return shape

def add_header(slide, title_text, category_text="", slide_num=None):
    # Category Tracker & Breadcrumb (only if category_text provided)
    if category_text:
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(9.5), Inches(0.3))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = f"{category_text.upper()}"
        p_c.font.name = FONT_BODY
        p_c.font.size = Pt(9.5)
        p_c.font.bold = True
        p_c.font.color.rgb = C_OCHRE

    # Slide Number pill on top right
    if slide_num:
        add_pill(slide, Inches(11.3), Inches(0.4), Inches(1.2), Inches(0.35), f"{slide_num:02d} / 10",
                 bg_color=C_CARD_BEIGE, border_color=C_BORDER, text_color=C_TEXT_BODY, font_size=9.5)

    # Main Title
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.68), Inches(10.2), Inches(0.65))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(21)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK

    # Subtle Hairline divider
    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.38), Inches(11.733), Inches(0.015))
    divider.fill.solid()
    divider.fill.fore_color.rgb = C_BORDER
    divider.line.fill.background()

def add_card(slide, left, top, width, height, bg_color=C_CARD_BEIGE, border_color=C_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape

# -------------------------------------------------------------
# GENERATE PRESENTATION SLIDES
# -------------------------------------------------------------
def build_powerpoint():
    print("Generating Project_Presentation.pptx (Minimal Warm Editorial)...")
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    blank_layout = prs.slide_layouts[6]

    # =========================================================
    # SLIDE 1: TITLE (Minimal Dark Editorial Aesthetic - Clean)
    # =========================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, C_DARK_BG)

    # Subtle top indicator line in warm ochre
    top_line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.866), Inches(2.0), Inches(1.6), Inches(0.04))
    top_line.fill.solid(); top_line.fill.fore_color.rgb = C_OCHRE; top_line.line.fill.background()

    # Main Project Title (Centered, Elegant)
    title_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(11.333), Inches(2.0))
    tf1 = title_box.text_frame; tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Automated Network Failover and\nRecovery Testing Framework"
    p1.font.name = FONT_HEADING; p1.font.size = Pt(38); p1.font.bold = True; p1.font.color.rgb = C_TEXT_LIGHT
    p1.alignment = PP_ALIGN.CENTER

    # Subtitle
    sub_box = s1.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.333), Inches(0.9))
    tf_sub = sub_box.text_frame; tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "Empirical Evaluation, Autonomous Route Reconfiguration, and Sub-Millisecond Telemetry in Linux Namespaces"
    p_sub.font.name = FONT_BODY; p_sub.font.size = Pt(15); p_sub.font.color.rgb = C_TEXT_CREAM_MUTED
    p_sub.alignment = PP_ALIGN.CENTER

    s1.notes_slide.notes_text_frame.text = (
        "[00:00 - 00:30] SPEAKER NOTES:\n"
        "Good morning, esteemed members of the evaluation committee and faculty members. "
        "Today, I am honored to present our project: 'Automated Network Failover and Recovery Testing Framework'. "
        "In modern cloud data centers and enterprise backbones, network availability is mission critical. "
        "Our work addresses how to simulate complex network failures, automate route failover, and measure recovery performance "
        "with empirical accuracy using native Linux kernel virtualization. Let us begin by examining the core problem we set out to solve."
    )

    # =========================================================
    # SLIDE 2: PROBLEM STATEMENT (Minimal Warm Cream / Beige Aesthetic)
    # =========================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, C_CREAM_BG)
    add_header(s2, "The Core Problem: High-Availability Failover Evaluation", "PROBLEM STATEMENT & MOTIVATION", slide_num=2)

    col_w = Inches(3.64)
    h = Inches(5.1)

    # Card 1: Outages
    add_card(s2, Inches(0.8), Inches(1.6), col_w, h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s2, Inches(1.0), Inches(1.85), Inches(1.6), Inches(0.3), "SLA IMPACT", bg_color=RGBColor(245, 230, 224), border_color=C_TERRACOTTA, text_color=C_TERRACOTTA, font_size=8)
    tb1 = s2.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(3.24), Inches(4.3))
    tf1 = tb1.text_frame; tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Network Failures\nCause Costly Outages"
    p1.font.name = FONT_HEADING; p1.font.size = Pt(15); p1.font.bold = True; p1.font.color.rgb = C_TEXT_DARK
    p1_sub = tf1.add_paragraph()
    p1_sub.text = (
        "\n• Fiber cuts, gateway crashes, and interface drops disrupt mission-critical traffic."
        "\n\n• Downtime triggers severe SLA financial penalties and distributed state corruption."
        "\n\n• Silent gateway blackholing occurs without physical link carrier loss, evading simple link-state detection."
    )
    p1_sub.font.name = FONT_BODY; p1_sub.font.size = Pt(10.5); p1_sub.font.color.rgb = C_TEXT_BODY

    # Card 2: Traditional Testing Limitations
    add_card(s2, Inches(4.84), Inches(1.6), col_w, h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s2, Inches(5.04), Inches(1.85), Inches(1.8), Inches(0.3), "TESTING DILEMMA", bg_color=RGBColor(248, 240, 225), border_color=C_OCHRE, text_color=C_OCHRE, font_size=8)
    tb2 = s2.shapes.add_textbox(Inches(5.04), Inches(2.25), Inches(3.24), Inches(4.3))
    tf2 = tb2.text_frame; tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Existing Testing Is\nCostly & Non-Deterministic"
    p2.font.name = FONT_HEADING; p2.font.size = Pt(15); p2.font.bold = True; p2.font.color.rgb = C_TEXT_DARK
    p2_sub = tf2.add_paragraph()
    p2_sub.text = (
        "\n• Manual cable pulling lacks repeatability and automated telemetry."
        "\n\n• Proprietary hardware test appliances (Ixia, Spirent) cost upwards of $50,000."
        "\n\n• Synthetic simulators (Packet Tracer, NS-3) bypass real Linux kernel routing tables, missing OS-level race conditions."
    )
    p2_sub.font.name = FONT_BODY; p2_sub.font.size = Pt(10.5); p2_sub.font.color.rgb = C_TEXT_BODY

    # Card 3: The Need for Automated Framework
    add_card(s2, Inches(8.88), Inches(1.6), col_w, h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s2, Inches(9.08), Inches(1.85), Inches(2.0), Inches(0.3), "THE SOLUTION", bg_color=RGBColor(230, 238, 232), border_color=C_SAGE, text_color=C_SAGE, font_size=8)
    tb3 = s2.shapes.add_textbox(Inches(9.08), Inches(2.25), Inches(3.24), Inches(4.3))
    tf3 = tb3.text_frame; tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Need for Closed-Loop\nEmpirical Validation"
    p3.font.name = FONT_HEADING; p3.font.size = Pt(15); p3.font.bold = True; p3.font.color.rgb = C_TEXT_DARK
    p3_sub = tf3.add_paragraph()
    p3_sub.text = (
        "\n• Automated, repeatable disruption injection across diverse failure profiles."
        "\n\n• Real operating system networking (iproute2) with zero synthetic mocking."
        "\n\n• Sub-millisecond empirical metric extraction (Detection, Recovery, Loss %, Latency)."
    )
    p3_sub.font.name = FONT_BODY; p3_sub.font.size = Pt(10.5); p3_sub.font.color.rgb = C_TEXT_BODY

    s2.notes_slide.notes_text_frame.text = (
        "[00:30 - 01:20] SPEAKER NOTES:\n"
        "To understand our motivation, consider what happens when a network link fails. "
        "In production environments, a five-second outage can cause millions in lost transactions. "
        "Yet testing failover remains a major operational dilemma. Testing on live infrastructure is far too risky. "
        "Physical laboratories are cost-prohibitive, and simulators like Packet Tracer do not execute the real Linux network stack. "
        "There is an acute need for a platform that uses the real operating system kernel to inject failures, execute automatic failover, "
        "and measure exact recovery durations without expensive hardware. This leads directly to our objectives."
    )

    # =========================================================
    # SLIDE 3: OBJECTIVES & METHODOLOGY (Grid of 4 Clean Beige Cards)
    # =========================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, C_CREAM_BG)
    add_header(s3, "Objectives & Proposed Automated Testing Solution", "PROJECT GOALS & METHODOLOGY", slide_num=3)

    box_w = Inches(5.66)
    box_h = Inches(2.35)

    objectives = [
        ("01", "VIRTUAL NETWORK VIRTUALIZATION", "Provision an isolated 4-node dual-path topology (Client, Primary Router, Backup Router, Destination Server) using native Linux Network Namespaces (`ip netns`) and Virtual Ethernet pairs (`veth`).", Inches(0.8), Inches(1.6), C_SLATE_BLUE),
        ("02", "CONTINUOUS PROBING & FAILURE SIMULATION", "Execute continuous ICMP ping probes with sub-millisecond RTT parsing. Programmatically inject 5 distinct disruption profiles (Link Cut, Gateway Crash, Egress Down, Route Removal, Flapping).", Inches(6.86), Inches(1.6), C_OCHRE),
        ("03", "AUTONOMOUS MULTI-METRIC FAILOVER", "Threshold-based detection (N=3 missed probes) triggers kernel route replacement promoting backup route metric from 200 to 50, followed by active reachability verification.", Inches(0.8), Inches(4.35), C_TERRACOTTA),
        ("04", "MONOTONIC METRICS & REPORTING", "Measure detection and recovery durations using clock-drift-free monotonic timing. Commit telemetry to an SQLite WAL database and serve an interactive Flask dashboard with CSV exports.", Inches(6.86), Inches(4.35), C_SAGE)
    ]

    for num, title, desc, left, top, accent in objectives:
        add_card(s3, left, top, box_w, box_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
        add_pill(s3, left + Inches(0.2), top + Inches(0.2), Inches(0.6), Inches(0.3), num, bg_color=C_CARD_WHITE, border_color=accent, text_color=accent, font_size=9)
        tb = s3.shapes.add_textbox(left + Inches(0.95), top + Inches(0.18), box_w - Inches(1.15), box_h - Inches(0.3))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title; p.font.name = FONT_HEADING; p.font.size = Pt(11.5); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
        p2 = tf.add_paragraph(); p2.text = f"\n{desc}"; p2.font.name = FONT_BODY; p2.font.size = Pt(9.8); p2.font.color.rgb = C_TEXT_BODY

    s3.notes_slide.notes_text_frame.text = (
        "[01:20 - 02:10] SPEAKER NOTES:\n"
        "To solve these challenges, we established four clear engineering objectives: "
        "First, we use Linux Network Namespaces to create an isolated software-defined dual-path topology. "
        "Second, we implement a background packet monitor that probes reachability at five Hertz and an automated failure engine. "
        "Third, we build a failover controller that promotes backup route priority in the kernel routing table via metric override, "
        "paired with a hysteresis failback mechanism. "
        "Fourth, we measure all durations with monotonic clocks to eliminate clock drift, store all data in an SQLite database, "
        "and visualize live telemetry on a web dashboard. Now, let us examine the system architecture that ties this together."
    )

    # =========================================================
    # SLIDE 4: SYSTEM ARCHITECTURE (Split: Diagram + 4-Tier Pillars)
    # =========================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, C_CREAM_BG)
    add_header(s4, "Multi-Tiered System Architecture", "SYSTEM ARCHITECTURE & MODULE DESIGN", slide_num=4)

    # Embedded Image Container Card
    add_card(s4, Inches(0.8), Inches(1.5), Inches(7.6), Inches(5.35), bg_color=C_CARD_WHITE, border_color=C_BORDER)
    if os.path.exists("documentation/architecture/system_architecture.png"):
        s4.shapes.add_picture("documentation/architecture/system_architecture.png", Inches(0.95), Inches(1.65), Inches(7.3), Inches(5.05))

    # Architecture Explanation Card on Right
    add_card(s4, Inches(8.7), Inches(1.5), Inches(3.833), Inches(5.35), bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s4, Inches(8.95), Inches(1.75), Inches(1.8), Inches(0.3), "4 ARCHITECTURAL TIERS", bg_color=C_CARD_WHITE, border_color=C_OCHRE, text_color=C_OCHRE, font_size=8)
    
    tb_arch = s4.shapes.add_textbox(Inches(8.95), Inches(2.15), Inches(3.35), Inches(4.5))
    tf_a = tb_arch.text_frame; tf_a.word_wrap = True
    pa = tf_a.paragraphs[0]; pa.text = "Architectural Pillars"; pa.font.name = FONT_HEADING; pa.font.size = Pt(13.5); pa.font.bold = True; pa.font.color.rgb = C_TEXT_DARK
    pa_sub = tf_a.add_paragraph()
    pa_sub.text = (
        "\n• Tier 1: Presentation\n  HTML5, Bootstrap 5 & Chart.js live loss meters and telemetry gauges."
        "\n\n• Tier 2: Application API\n  Flask 3.0 REST backend dispatches failure events and session lifecycle."
        "\n\n• Tier 3: Testing Engine\n  Multi-threaded controllers for probing, failure injection, failover & monotonic analysis."
        "\n\n• Tier 4: Virtualization & DB\n  Linux kernel iproute2 subsystem + SQLite WAL database."
    )
    pa_sub.font.name = FONT_BODY; pa_sub.font.size = Pt(9.5); pa_sub.font.color.rgb = C_TEXT_BODY

    s4.notes_slide.notes_text_frame.text = (
        "[02:10 - 03:20] SPEAKER NOTES:\n"
        "Here we see the complete system architecture, structured into four clean tiers. "
        "At the top is our Presentation Tier: an interactive web dashboard built with Bootstrap 5 and Chart.js, "
        "which streams telemetry directly from the backend. "
        "Below it is the Application Tier, a Flask REST API that coordinates experiment sessions and event dispatching. "
        "The heart of the system is Tier 3: the Core Network Testing Engine. "
        "It consists of the Topology Manager, the Packet Monitor running in a dedicated thread, the Failure Simulation Engine, "
        "the Failover Controller, and the Recovery Analyzer. "
        "Finally, Tier 4 interfaces directly with the Linux kernel networking subsystem using iproute2 and persists every measurement "
        "into an SQLite database using Write-Ahead Logging for maximum concurrency. "
        "Let us look closely at how the virtual network topology is structured."
    )

    # =========================================================
    # SLIDE 5: TOPOLOGY & WORKING (Split: Topology Diagram + Routing Card)
    # =========================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, C_CREAM_BG)
    add_header(s5, "Virtual Network Topology & Multi-Metric Routing", "TOPOLOGY & FAILOVER DYNAMICS", slide_num=5)

    add_card(s5, Inches(0.8), Inches(1.5), Inches(7.6), Inches(5.35), bg_color=C_CARD_WHITE, border_color=C_BORDER)
    if os.path.exists("documentation/architecture/network_topology.png"):
        s5.shapes.add_picture("documentation/architecture/network_topology.png", Inches(0.95), Inches(1.65), Inches(7.3), Inches(5.05))

    add_card(s5, Inches(8.7), Inches(1.5), Inches(3.833), Inches(5.35), bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s5, Inches(8.95), Inches(1.75), Inches(1.9), Inches(0.3), "KERNEL ROUTING LOGIC", bg_color=C_CARD_WHITE, border_color=C_SLATE_BLUE, text_color=C_SLATE_BLUE, font_size=8)
    
    tb_top = s5.shapes.add_textbox(Inches(8.95), Inches(2.15), Inches(3.35), Inches(4.5))
    tf_top = tb_top.text_frame; tf_top.word_wrap = True
    pt = tf_top.paragraphs[0]; pt.text = "Routing Dynamics"; pt.font.name = FONT_HEADING; pt.font.size = Pt(13.5); pt.font.bold = True; pt.font.color.rgb = C_TEXT_DARK
    pt_sub = tf_top.add_paragraph()
    pt_sub.text = (
        "\n• 4 Isolated Namespaces:\n  ns_client, ns_primary, ns_backup, and ns_server."
        "\n\n• Baseline Steady-State:\n  Primary path: metric 100 via 10.0.1.1\n  Backup path:  metric 200 via 10.0.2.1\n  Linux FIB naturally selects Metric 100."
        "\n\n• Failover State:\n  When 3 probes fail, Controller assigns metric 50 to backup route.\n  Backup immediately overrides primary (50 < 100)."
        "\n\n• Verified Failback:\n  Primary probed 3 times for stability before demoting backup back to 200."
    )
    pt_sub.font.name = FONT_BODY; pt_sub.font.size = Pt(9.5); pt_sub.font.color.rgb = C_TEXT_BODY

    s5.notes_slide.notes_text_frame.text = (
        "[03:20 - 04:40] SPEAKER NOTES:\n"
        "This slide illustrates our dual-path virtual topology. "
        "We create four independent network namespaces: ns_client, ns_primary, ns_backup, and ns_server. "
        "Each node has its own virtual interfaces, IP addresses, and routing tables. "
        "The destination target service is 10.50.0.1, bound to the server's loopback interface. "
        "In normal operation, the client has two static routes to the destination: "
        "one through the primary router with metric 100, and one through the backup router with metric 200. "
        "Because Linux prefers the route with the lowest metric, all traffic travels through the primary path. "
        "When a failure occurs—such as disabling the primary router or link—our probing engine detects it after three missed pings. "
        "The controller immediately executes 'ip route replace', giving the backup route a promoted metric of 50. "
        "Because 50 is lower than 100, the Linux kernel instantaneously redirects outgoing packets to the backup path. "
        "Once the primary link recovers and proves stable over three consecutive probes, the controller restores metric 100 without route flapping."
    )

    # =========================================================
    # SLIDE 6: IMPLEMENTATION & TECH STACK (3 Top Cards + 1 Bottom Wide Card)
    # =========================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, C_CREAM_BG)
    add_header(s6, "Implementation Stack & Core Engineering Decisions", "IMPLEMENTATION & CODEBASE", slide_num=6)

    tech_w = Inches(3.64)
    tech_h = Inches(2.45)

    # Box 1: Linux
    add_card(s6, Inches(0.8), Inches(1.6), tech_w, tech_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s6, Inches(1.0), Inches(1.8), Inches(1.6), Inches(0.3), "KERNEL DATA-PLANE", bg_color=C_CARD_WHITE, border_color=C_SLATE_BLUE, text_color=C_SLATE_BLUE, font_size=8)
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(2.18), Inches(3.24), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "Linux Kernel & iproute2"; p.font.name = FONT_HEADING; p.font.size = Pt(12.5); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
    p2 = tf.add_paragraph(); p2.text = "• Linux Network Namespaces (netns)\n• Virtual Ethernet link pairs (veth)\n• Sysctl IP forwarding (net.ipv4.ip_forward=1)\n• Native ICMP ping & route cache flush"; p2.font.name = FONT_BODY; p2.font.size = Pt(9.5); p2.font.color.rgb = C_TEXT_BODY

    # Box 2: Python
    add_card(s6, Inches(4.84), Inches(1.6), tech_w, tech_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s6, Inches(5.04), Inches(1.8), Inches(1.5), Inches(0.3), "CONTROL PLANE", bg_color=C_CARD_WHITE, border_color=C_OCHRE, text_color=C_OCHRE, font_size=8)
    tb = s6.shapes.add_textbox(Inches(5.04), Inches(2.18), Inches(3.24), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "Python 3 Core Engine"; p.font.name = FONT_HEADING; p.font.size = Pt(12.5); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
    p2 = tf.add_paragraph(); p2.text = "• Thread-safe daemon monitor (threading.Lock)\n• Monotonic timers (time.monotonic())\n• Subprocess execution with WSL wrapping\n• Real-time regex RTT stream parser"; p2.font.name = FONT_BODY; p2.font.size = Pt(9.5); p2.font.color.rgb = C_TEXT_BODY

    # Box 3: Database
    add_card(s6, Inches(8.88), Inches(1.6), tech_w, tech_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s6, Inches(9.08), Inches(1.8), Inches(1.4), Inches(0.3), "STORAGE TIER", bg_color=C_CARD_WHITE, border_color=C_SAGE, text_color=C_SAGE, font_size=8)
    tb = s6.shapes.add_textbox(Inches(9.08), Inches(2.18), Inches(3.24), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "Database & Persistence"; p.font.name = FONT_HEADING; p.font.size = Pt(12.5); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
    p2 = tf.add_paragraph(); p2.text = "• SQLite 3 with Write-Ahead Logging (WAL)\n• Synchronous NORMAL mode for 0-lock overhead\n• 4 relational tables (sessions, probes, events, metrics)\n• Zero external database server footprint"; p2.font.name = FONT_BODY; p2.font.size = Pt(9.5); p2.font.color.rgb = C_TEXT_BODY

    # Box 4: Bottom Wide Card
    add_card(s6, Inches(0.8), Inches(4.35), Inches(11.72), Inches(2.5), bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s6, Inches(1.05), Inches(4.55), Inches(1.8), Inches(0.3), "WEB & ANALYTICS", bg_color=C_CARD_WHITE, border_color=C_OCHRE, text_color=C_OCHRE, font_size=8)
    tb = s6.shapes.add_textbox(Inches(1.05), Inches(4.9), Inches(11.2), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "Flask Web Architecture & Pandas Analytics Engine"; p.font.name = FONT_HEADING; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
    p2 = tf.add_paragraph(); p2.text = (
        "• RESTful API Endpoints: Support programmatic test session initiation, failure injection, manual route overrides, and live status streaming.\n"
        "• Responsive Web Interface: Built with Bootstrap 5 and Chart.js 4, rendering live loss meters, latency graphs, and topology node badges.\n"
        "• Pandas Reporting Engine: Computes grouped averages across failure scenarios and streams downloadable CSV files for full experimental evaluation."
    )
    p2.font.name = FONT_BODY; p2.font.size = Pt(9.5); p2.font.color.rgb = C_TEXT_BODY

    s6.notes_slide.notes_text_frame.text = (
        "[04:40 - 05:40] SPEAKER NOTES:\n"
        "Let us examine the technology stack and core implementation decisions. "
        "We chose Python 3 and native Linux iproute2 utilities. "
        "A critical engineering decision was migrating duration measurements to monotonic clocks. "
        "Unlike standard wall-clock time, which can drift or jump during NTP synchronizations, "
        "Python's time.monotonic() guarantees nanosecond precision intervals. "
        "For telemetry storage, we selected SQLite configured in WAL mode. "
        "This allows our high-frequency packet monitor thread to write probe records continuously "
        "while the Flask web server simultaneously reads and renders live charts without database locks. "
        "On the presentation side, we use Flask, Bootstrap 5, and Chart.js, paired with Pandas for multi-scenario aggregation."
    )

    # =========================================================
    # SLIDE 7: 6 EXPERIMENTAL SCENARIOS (6-Card Grid)
    # =========================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, C_CREAM_BG)
    add_header(s7, "Comprehensive Testing & Failure Scenarios", "EXPERIMENTAL METHODOLOGY", slide_num=7)

    scen_w = Inches(3.64)
    scen_h = Inches(2.45)

    scenarios = [
        ("Exp 1: Normal Operation", "BASELINE STEADY-STATE", "Verifies baseline connectivity to destination 10.50.0.1 via primary router with 0% packet loss and ~0.035 ms RTT.", C_SAGE),
        ("Exp 2: Primary Link Cut", "PHYSICAL / LOGICAL CUT", "Shuts down primary ingress link (`veth_p_c down`). Simulates cable severing; validates threshold detection and route switch.", C_TERRACOTTA),
        ("Exp 3: Gateway Crash", "SILENT BLACKHOLE", "Disables IP forwarding (`sysctl net.ipv4.ip_forward=0`). Simulates router lockup where link carrier remains UP but transit traffic drops.", C_OCHRE),
        ("Exp 4: Interface Shutdown", "EGRESS INTERMEDIATE CUT", "Disables primary router egress interface (`veth_p_s down`). Simulates upstream provider disconnect; verifies rapid recovery in < 3.5s.", C_TERRACOTTA),
        ("Exp 5: Path Restoration", "HYSTERESIS-STABILIZED FAILBACK", "Restores primary hardware and verifies stability across 3 consecutive successful probes before executing sub-25 ms failback.", C_SAGE),
        ("Exp 6: Repeated Cycles", "MULTI-CYCLE JITTER", "Executes 3 consecutive failure, failover, restoration, and failback cycles to prove zero route flapping and consistent determinism.", C_SLATE_BLUE)
    ]

    for idx, (title, tag, desc, accent) in enumerate(scenarios):
        row = idx // 3
        col = idx % 3
        left = Inches(0.8) + col * Inches(4.04)
        top = Inches(1.6) + row * Inches(2.7)
        
        add_card(s7, left, top, scen_w, scen_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
        add_pill(s7, left + Inches(0.2), top + Inches(0.18), Inches(1.8), Inches(0.28), tag, bg_color=C_CARD_WHITE, border_color=accent, text_color=accent, font_size=7.5)
        tb = s7.shapes.add_textbox(left + Inches(0.2), top + Inches(0.55), Inches(3.24), Inches(1.8))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title; p.font.name = FONT_HEADING; p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
        p_d = tf.add_paragraph(); p_d.text = f"\n{desc}"; p_d.font.name = FONT_BODY; p_d.font.size = Pt(9.2); p_d.font.color.rgb = C_TEXT_BODY

    s7.notes_slide.notes_text_frame.text = (
        "[05:40 - 06:50] SPEAKER NOTES:\n"
        "To rigorously validate the framework, we executed six comprehensive test scenarios. "
        "Experiment 1 establishes our healthy baseline. "
        "Experiment 2 tests physical cable disconnection by disabling the client-router veth interface. "
        "Experiment 3 simulates a silent gateway crash by disabling IP forwarding inside the primary router namespace. "
        "This is particularly challenging because the Ethernet link remains electrically UP, creating a silent blackhole. "
        "Experiment 4 tests an egress interface shutdown between the router and server. "
        "Experiment 5 evaluates primary path restoration and failback with stability verification. "
        "Finally, Experiment 6 runs three consecutive failure and recovery cycles to ensure the routing table does not suffer from stale states or memory leaks. "
        "Let us examine the actual experimental results from these tests."
    )

    # =========================================================
    # SLIDE 8: RESULTS & PERFORMANCE ANALYSIS (Charts + 4 Hero Stat Blocks)
    # =========================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, C_CREAM_BG)
    add_header(s8, "Experimental Results & Recovery Performance Analysis", "EMPIRICAL EVALUATION & METRICS", slide_num=8)

    # Chart 1 Container
    add_card(s8, Inches(0.8), Inches(1.5), Inches(5.7), Inches(3.35), bg_color=C_CARD_WHITE, border_color=C_BORDER)
    if os.path.exists("documentation/architecture/experiment_recovery_chart.png"):
        s8.shapes.add_picture("documentation/architecture/experiment_recovery_chart.png", Inches(0.9), Inches(1.55), Inches(5.5), Inches(3.2))

    # Chart 2 Container
    add_card(s8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(3.35), bg_color=C_CARD_WHITE, border_color=C_BORDER)
    if os.path.exists("documentation/architecture/repeated_cycles_chart.png"):
        s8.shapes.add_picture("documentation/architecture/repeated_cycles_chart.png", Inches(6.9), Inches(1.55), Inches(5.5), Inches(3.2))

    # 4 Hero Metric Cards at bottom
    stat_w = Inches(2.7)
    stat_h = Inches(1.75)
    stats = [
        ("3,441 ms", "AVG DETECTION TIME", "N=3 missed probes (85% of total recovery)", C_OCHRE),
        ("34.10 ms", "KERNEL ROUTE SWITCHOVER", "ip route replace + FIB cache flush", C_TERRACOTTA),
        ("23.50 ms", "FAILBACK DURATION", "Verified across 3 stable probes", C_SAGE),
        ("100.0 %", "FAILOVER SUCCESS RATE", "0 dropped sessions across 32 trials", C_SLATE_BLUE)
    ]

    for idx, (val, label, sub, color) in enumerate(stats):
        left = Inches(0.8) + idx * Inches(3.0)
        top = Inches(5.1)
        add_card(s8, left, top, stat_w, stat_h, bg_color=C_CARD_BEIGE, border_color=C_BORDER)
        add_pill(s8, left + Inches(0.15), top + Inches(0.15), Inches(2.4), Inches(0.24), label, bg_color=C_CARD_WHITE, border_color=C_BORDER, text_color=color, font_size=7)
        tb = s8.shapes.add_textbox(left + Inches(0.15), top + Inches(0.45), Inches(2.4), Inches(1.1))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = val; p.font.name = FONT_HEADING; p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = C_TEXT_DARK
        p_sub = tf.add_paragraph(); p_sub.text = sub; p_sub.font.name = FONT_BODY; p_sub.font.size = Pt(8.2); p_sub.font.color.rgb = C_TEXT_MUTED

    s8.notes_slide.notes_text_frame.text = (
        "[06:50 - 08:30] SPEAKER NOTES:\n"
        "Here are our actual empirical measurements collected across 32 recorded sessions in our SQLite database. "
        "Looking at the left chart, we see Failure Detection Time compared to Total Recovery Time across different failure scenarios. "
        "A critical finding emerges: Failure Detection Time accounts for 85% of total recovery duration! "
        "Because our detection threshold requires three consecutive missed probes, detection takes between 1.8 and 4.2 seconds. "
        "However, once failure is declared, the kernel route switchover itself executes in just 15 to 40 milliseconds. "
        "The right chart displays our repeated failure cycles test. Notice the remarkable consistency across all three cycles: "
        "detection times hover tightly around 4.1 seconds, recovery around 4.7 seconds, and failback completes in an astonishing 21 to 25 milliseconds. "
        "Overall, our failover success rate was 100%, and baseline round-trip latency remained under 0.04 milliseconds."
    )

    # =========================================================
    # SLIDE 9: CONCLUSION & FUTURE SCOPE (2 Clean Beige Panels)
    # =========================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, C_CREAM_BG)
    add_header(s9, "Conclusion & Future Research Directions", "SUMMARY & FUTURE SCOPE", slide_num=9)

    add_card(s9, Inches(0.8), Inches(1.6), Inches(5.66), Inches(5.1), bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s9, Inches(1.05), Inches(1.85), Inches(2.2), Inches(0.3), "PROJECT ACHIEVEMENTS", bg_color=C_CARD_WHITE, border_color=C_SAGE, text_color=C_SAGE, font_size=8.5)
    tb_c = s9.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.16), Inches(4.3))
    tfc = tb_c.text_frame; tfc.word_wrap = True
    pc = tfc.paragraphs[0]; pc.text = "Key Project Achievements"; pc.font.name = FONT_HEADING; pc.font.size = Pt(14); pc.font.bold = True; pc.font.color.rgb = C_TEXT_DARK
    pc_sub = tfc.add_paragraph()
    pc_sub.text = (
        "\n1. Authentic Operating System Networking:\n   Demonstrated that Linux Namespaces provide an authentic, cost-free testbed using real kernel routing tables without physical hardware."
        "\n\n2. Autonomous Multi-Metric Routing:\n   Achieved seamless failover via metric 50 overriding without restarting network daemons or dropping standby routes."
        "\n\n3. Clock-Drift Immunity:\n   Enforced monotonic timestamps, eliminating measurement skew caused by NTP."
        "\n\n4. Hysteresis Stability:\n   Proved that 3-probe stability verification eliminates route flapping during intermittent link states."
    )
    pc_sub.font.name = FONT_BODY; pc_sub.font.size = Pt(9.5); pc_sub.font.color.rgb = C_TEXT_BODY

    add_card(s9, Inches(6.86), Inches(1.6), Inches(5.66), Inches(5.1), bg_color=C_CARD_BEIGE, border_color=C_BORDER)
    add_pill(s9, Inches(7.11), Inches(1.85), Inches(2.0), Inches(0.3), "RESEARCH HORIZONS", bg_color=C_CARD_WHITE, border_color=C_SLATE_BLUE, text_color=C_SLATE_BLUE, font_size=8.5)
    tb_f = s9.shapes.add_textbox(Inches(7.11), Inches(2.25), Inches(5.16), Inches(4.3))
    tff = tb_f.text_frame; tff.word_wrap = True
    pf = tff.paragraphs[0]; pf.text = "Future Scope & Enhancements"; pf.font.name = FONT_HEADING; pf.font.size = Pt(14); pf.font.bold = True; pf.font.color.rgb = C_TEXT_DARK
    pf_sub = tff.add_paragraph()
    pf_sub.text = (
        "\n1. Sub-Millisecond BFD Integration:\n   Incorporate Bidirectional Forwarding Detection (RFC 5880) to reduce failure detection below 100 ms."
        "\n\n2. eBPF / XDP Data-Plane Acceleration:\n   Implement eBPF kernel packet steering for microsecond route diversion directly at the NIC driver layer."
        "\n\n3. Multi-Host VXLAN Topologies:\n   Extend namespace routing across physical servers using VXLAN/Geneve tunneling for multi-node cloud clusters."
        "\n\n4. Dynamic Traffic Ingestion:\n   Integrate iperf3 or TRex traffic generators to benchmark failover under saturated 10 Gbps TCP/UDP throughput."
    )
    pf_sub.font.name = FONT_BODY; pf_sub.font.size = Pt(9.5); pf_sub.font.color.rgb = C_TEXT_BODY

    s9.notes_slide.notes_text_frame.text = (
        "[08:30 - 09:20] SPEAKER NOTES:\n"
        "In conclusion, this project demonstrates that software-defined network namespaces provide an authentic, reproducible, "
        "and zero-cost platform for evaluating network resilience. "
        "We achieved all our project objectives: autonomous failover was 100% successful, failback restored primary preference in under 25 milliseconds, "
        "and our monotonic timing architecture guarantees measurement integrity. "
        "Looking forward, exciting opportunities exist to integrate sub-millisecond Bidirectional Forwarding Detection (BFD) "
        "and eBPF data-plane packet steering to push failover times into the sub-50 millisecond regime. "
        "Now, I would be delighted to welcome your questions."
    )

    # =========================================================
    # SLIDE 10: THANK YOU / Q&A (Minimal Dark Editorial Aesthetic)
    # =========================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, C_DARK_BG)

    # Subtle top indicator line in warm ochre
    bot_line = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.866), Inches(1.8), Inches(1.6), Inches(0.04))
    bot_line.fill.solid(); bot_line.fill.fore_color.rgb = C_OCHRE; bot_line.line.fill.background()

    add_pill(s10, Inches(5.166), Inches(2.1), Inches(3.0), Inches(0.36),
             "QUESTIONS & TECHNICAL DISCUSSION", bg_color=C_DARK_CARD, border_color=C_DARK_BORDER, text_color=C_OCHRE, font_size=8.5)

    q_box = s10.shapes.add_textbox(Inches(1.0), Inches(2.7), Inches(11.3), Inches(3.2))
    tf_q = q_box.text_frame; tf_q.word_wrap = True
    pq1 = tf_q.paragraphs[0]; pq1.text = "Thank You"; pq1.font.name = FONT_HEADING; pq1.font.size = Pt(42); pq1.font.bold = True; pq1.font.color.rgb = C_TEXT_LIGHT; pq1.alignment = PP_ALIGN.CENTER
    pq2 = tf_q.add_paragraph(); pq2.text = "Automated Network Failover and Recovery Testing Framework"; pq2.font.name = FONT_BODY; pq2.font.size = Pt(15); pq2.font.color.rgb = C_OCHRE; pq2.alignment = PP_ALIGN.CENTER
    pq3 = tf_q.add_paragraph(); pq3.text = "\nFloor is now open for evaluation committee questions and technical discussions."; pq3.font.name = FONT_BODY; pq3.font.size = Pt(12); pq3.font.color.rgb = C_TEXT_CREAM_MUTED; pq3.alignment = PP_ALIGN.CENTER

    s10.notes_slide.notes_text_frame.text = (
        "[09:20 - 10:00] SPEAKER NOTES:\n"
        "Thank you very much for your time and kind attention. "
        "I now open the floor to the evaluation committee for any questions, comments, or technical discussions."
    )

    # Save presentation
    pptx_path = "documentation/presentation/Project_Presentation.pptx"
    prs.save(pptx_path)
    print(f"Successfully generated {pptx_path} ({os.path.getsize(pptx_path)} bytes)")

# -------------------------------------------------------------
# GENERATE SPEAKER NOTES SCRIPT DOCUMENT (DOCX)
# -------------------------------------------------------------
def build_speaker_notes_docx():
    print("Generating Presentation_Speaker_Notes.docx...")
    doc = Document()
    
    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_title.add_run("10-MINUTE ACADEMIC PROJECT DEFENSE — SPEAKER NOTES & SCRIPT\n")
    r_t.font.name = "Arial"; r_t.font.size = DocxPt(18); r_t.font.bold = True; r_t.font.color.rgb = DocxRGBColor(24, 23, 22)
    r_sub = p_title.add_run("Automated Network Failover and Recovery Testing Framework\nTiming: Exactly 10 Minutes (600 Seconds) | Presentation Format: 10 Slides (Minimal Warm Editorial)")
    r_sub.font.name = "Arial"; r_sub.font.size = DocxPt(10.5); r_sub.font.italic = True; r_sub.font.color.rgb = DocxRGBColor(181, 135, 58)

    doc.add_paragraph().paragraph_format.space_after = DocxPt(12)

    slides_data = [
        ("Slide 1: Title & Introduction", "00:00 - 00:30 (30 seconds)",
         "Presentation title, author credentials, project scope, academic context.",
         "Good morning, esteemed members of the evaluation committee and faculty members. "
         "Today, I am honored to present our project: 'Automated Network Failover and Recovery Testing Framework'. "
         "In modern cloud data centers and enterprise backbones, network availability is mission critical. "
         "Our work addresses how to simulate complex network failures, automate route failover, and measure recovery performance "
         "with empirical accuracy using native Linux kernel virtualization. Let us begin by examining the core problem we set out to solve.",
         "Move directly to Slide 2 to present the core problems."),

        ("Slide 2: Problem Statement & Motivation", "00:30 - 01:20 (50 seconds)",
         "3 Cards: Outages Cause Costly Disruptions; Traditional Testing Limitations; Need for Closed-Loop Validation.",
         "To understand our motivation, consider what happens when a network link fails. "
         "In production environments, a five-second outage can cause millions in lost transactions or trigger distributed database split-brain conditions. "
         "Yet testing failover remains a major operational dilemma. Testing on live infrastructure is far too risky. "
         "Physical laboratories are cost-prohibitive, and simulators like Packet Tracer do not execute the real Linux network stack. "
         "There is an acute need for a platform that uses the real operating system kernel to inject failures, execute automatic failover, "
         "and measure exact recovery durations without expensive hardware. This leads directly to our objectives.",
         "Transition to Slide 3 to outline the solution."),

        ("Slide 3: Objectives & Proposed Solution", "01:20 - 02:10 (50 seconds)",
         "4 Solution Pillars: Virtualization, Probing/Disruption, Autonomous Failover, Monotonic Logging.",
         "To solve these challenges, we established four clear engineering objectives: "
         "First, we use Linux Network Namespaces to create an isolated software-defined dual-path topology. "
         "Second, we implement a background packet monitor that probes reachability at five Hertz and an automated failure engine. "
         "Third, we build a failover controller that promotes backup route priority in the kernel routing table via metric override, "
         "paired with a hysteresis failback mechanism. "
         "Fourth, we measure all durations with monotonic clocks to eliminate clock drift, store all data in an SQLite database, "
         "and visualize live telemetry on a web dashboard. Now, let us examine the system architecture that ties this together.",
         "Transition to Slide 4 for the architecture diagram."),

        ("Slide 4: System Architecture", "02:10 - 03:20 (70 seconds)",
         "Tier 1 (Presentation), Tier 2 (Application), Tier 3 (Engine), Tier 4 (Virtualization & DB).",
         "Here we see the complete system architecture, structured into four clean tiers. "
         "At the top is our Presentation Tier: an interactive web dashboard built with Bootstrap 5 and Chart.js, "
         "which streams telemetry directly from the backend. "
         "Below it is the Application Tier, a Flask REST API that coordinates experiment sessions and event dispatching. "
         "The heart of the system is Tier 3: the Core Network Testing Engine. "
         "It consists of the Topology Manager, the Packet Monitor running in a dedicated thread, the Failure Simulation Engine, "
         "the Failover Controller, and the Recovery Analyzer. "
         "Finally, Tier 4 interfaces directly with the Linux kernel networking subsystem using iproute2 and persists every measurement "
         "into an SQLite database using Write-Ahead Logging for maximum concurrency. "
         "Let us look closely at how the virtual network topology is structured.",
         "Transition to Slide 5 for the network topology layout."),

        ("Slide 5: Network Topology & Working", "03:20 - 04:40 (80 seconds)",
         "Dual-Path Virtual Topology: ns_client, ns_primary, ns_backup, ns_server, veth pairs, metrics 100/200/50.",
         "This slide illustrates our dual-path virtual topology. "
         "We create four independent network namespaces: ns_client, ns_primary, ns_backup, and ns_server. "
         "Each node has its own virtual interfaces, IP addresses, and routing tables. "
         "The destination target service is 10.50.0.1, bound to the server's loopback interface. "
         "In normal operation, the client has two static routes to the destination: "
         "one through the primary router with metric 100, and one through the backup router with metric 200. "
         "Because Linux prefers the route with the lowest metric, all traffic travels through the primary path. "
         "When a failure occurs—such as disabling the primary router or link—our probing engine detects it after three missed pings. "
         "The controller immediately executes 'ip route replace', giving the backup route a promoted metric of 50. "
         "Because 50 is lower than 100, the Linux kernel instantaneously redirects outgoing packets to the backup path. "
         "Once the primary link recovers and proves stable over three consecutive probes, the controller restores metric 100 without route flapping.",
         "Transition to Slide 6 for implementation details."),

        ("Slide 6: Implementation & Technologies", "04:40 - 05:40 (60 seconds)",
         "Linux iproute2, Python 3 Multi-threading, SQLite WAL, Flask, Bootstrap 5, Pandas.",
         "Let us examine the technology stack and core implementation decisions. "
         "We chose Python 3 and native Linux iproute2 utilities. "
         "A critical engineering decision was migrating duration measurements to monotonic clocks. "
         "Unlike standard wall-clock time, which can drift or jump during NTP synchronizations, "
         "Python's time.monotonic() guarantees nanosecond precision intervals. "
         "For telemetry storage, we selected SQLite configured in WAL mode. "
         "This allows our high-frequency packet monitor thread to write probe records continuously "
         "while the Flask web server simultaneously reads and renders live charts without database locks. "
         "On the presentation side, we use Flask, Bootstrap 5, and Chart.js, paired with Pandas for multi-scenario aggregation.",
         "Transition to Slide 7 to explore the test scenarios."),

        ("Slide 7: Testing & Experimental Scenarios", "05:40 - 06:50 (70 seconds)",
         "6 Evaluated Experiments: Normal, Link Cut, Gateway Crash, Egress Down, Failback, Repeated Cycles.",
         "To rigorously validate the framework, we executed six comprehensive test scenarios. "
         "Experiment 1 establishes our healthy baseline. "
         "Experiment 2 tests physical cable disconnection by disabling the client-router veth interface. "
         "Experiment 3 simulates a silent gateway crash by disabling IP forwarding inside the primary router namespace. "
         "This is particularly challenging because the Ethernet link remains electrically UP, creating a silent blackhole. "
         "Experiment 4 tests an egress interface shutdown between the router and server. "
         "Experiment 5 evaluates primary path restoration and failback with stability verification. "
         "Finally, Experiment 6 runs three consecutive failure and recovery cycles to ensure the routing table does not suffer from stale states or memory leaks. "
         "Let us examine the actual experimental results from these tests.",
         "Transition to Slide 8 to analyze the empirical data."),

        ("Slide 8: Results & Performance Analysis", "06:50 - 08:30 (100 seconds)",
         "Empirical Charts: Detection vs Recovery; Repeated Cycles Stability; 32 Sessions Summary.",
         "Here are our actual empirical measurements collected across 32 recorded sessions in our SQLite database. "
         "Looking at the left chart, we see Failure Detection Time compared to Total Recovery Time across different failure scenarios. "
         "A critical finding emerges: Failure Detection Time accounts for 85% of total recovery duration! "
         "Because our detection threshold requires three consecutive missed probes, detection takes between 1.8 and 4.2 seconds. "
         "However, once failure is declared, the kernel route switchover itself executes in just 15 to 40 milliseconds. "
         "The right chart displays our repeated failure cycles test. Notice the remarkable consistency across all three cycles: "
         "detection times hover tightly around 4.1 seconds, recovery around 4.7 seconds, and failback completes in an astonishing 21 to 25 milliseconds. "
         "Overall, our failover success rate was 100%, and baseline round-trip latency remained under 0.04 milliseconds.",
         "Transition to Slide 9 for conclusions."),

        ("Slide 9: Conclusion & Future Scope", "08:30 - 09:20 (50 seconds)",
         "Achievements: Real OS stack, Monotonic accuracy, 100% success rate, Future BFD & eBPF.",
         "In conclusion, this project demonstrates that software-defined network namespaces provide an authentic, reproducible, "
         "and zero-cost platform for evaluating network resilience. "
         "We achieved all our project objectives: autonomous failover was 100% successful, failback restored primary preference in under 25 milliseconds, "
         "and our monotonic timing architecture guarantees measurement integrity. "
         "Looking forward, exciting opportunities exist to integrate sub-millisecond Bidirectional Forwarding Detection (BFD) "
         "and eBPF data-plane packet steering to push failover times into the sub-50 millisecond regime. "
         "Now, I would be delighted to welcome your questions.",
         "Transition to Slide 10 for Q&A."),

        ("Slide 10: Thank You / Q&A", "09:20 - 10:00 (40 seconds)",
         "Closing title, candidate contact, floor open for questions.",
         "Thank you very much for your time and kind attention. "
         "I now open the floor to the evaluation committee for any questions, comments, or technical discussions.",
         "End of presentation.")
    ]

    for title, timing, visuals, script, cue in slides_data:
        h = doc.add_heading(title, level=1)
        h.paragraph_format.space_before = DocxPt(14); h.paragraph_format.space_after = DocxPt(4)
        for run in h.runs:
            run.font.name = "Arial"; run.font.size = DocxPt(13); run.font.bold = True
            run.font.color.rgb = DocxRGBColor(24, 23, 22)
            
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_after = DocxPt(4)
        r_tm = p_t.add_run(f"Allocated Timing: {timing} | Visuals: {visuals}\n")
        r_tm.font.name = "Arial"; r_tm.font.size = DocxPt(9.5); r_tm.font.italic = True
        r_tm.font.color.rgb = DocxRGBColor(181, 135, 58)

        p_s = doc.add_paragraph()
        p_s.paragraph_format.space_after = DocxPt(6)
        p_s.paragraph_format.line_spacing = 1.15
        p_s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_lbl = p_s.add_run("Verbatim Speech Script:\n")
        r_lbl.font.name = "Arial"; r_lbl.font.size = DocxPt(10); r_lbl.font.bold = True
        r_sc = p_s.add_run(f"\"{script}\"")
        r_sc.font.name = "Arial"; r_sc.font.size = DocxPt(10); r_sc.font.color.rgb = DocxRGBColor(60, 57, 53)

        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_after = DocxPt(10)
        r_cue = p_c.add_run(f"Transition Cue: {cue}")
        r_cue.font.name = "Arial"; r_cue.font.size = DocxPt(9); r_cue.font.italic = True
        r_cue.font.color.rgb = DocxRGBColor(112, 107, 99)

    doc_path = "documentation/presentation/Presentation_Speaker_Notes.docx"
    doc.save(doc_path)
    print(f"Successfully generated {doc_path} ({os.path.getsize(doc_path)} bytes)")

if __name__ == "__main__":
    build_powerpoint()
    build_speaker_notes_docx()
    print("Presentation deliverables generated successfully!")
