import os, time, PyPDF2, requests, tempfile
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, Response
from supabase import create_client

app = Flask(__name__)
app.secret_key = "JIIT_PRINTFLOW_FINAL_ULTIMATE_V2026_FIXED"

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://qsfwlyucognzoojijgul.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzZndseXVjb2duem9vamlqZ3VsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwNjUwNjgsImV4cCI6MjA5NjY0MTA2OH0.WeipU_k1_Rm6M97gC7LMsjbFspjVRDiPOnAHreeNATc")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- PDF PROCESSING ENGINE ---
def process_pdf_and_count(input_path, output_path, range_str):
    try:
        reader = PyPDF2.PdfReader(input_path)
        total_pages = len(reader.pages)
        if not range_str or range_str.lower() == 'all' or range_str.strip() == "":
            return total_pages, input_path
        writer = PyPDF2.PdfWriter()
        selected_indices = []
        parts = range_str.replace(" ", "").split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                selected_indices.extend(range(start - 1, end))
            else:
                selected_indices.append(int(part) - 1)
        for idx in sorted(list(set(selected_indices))):
            if 0 <= idx < total_pages: writer.add_page(reader.pages[idx])
        if len(writer.pages) == 0: return total_pages, input_path
        with open(output_path, "wb") as f: writer.write(f)
        return len(writer.pages), output_path
    except: return 0, input_path

# --- FULL UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrintFlow Pro | JIIT Portal</title>
    <link rel="icon" type="image/png" href="https://qsfwlyucognzoojijgul.supabase.co/storage/v1/object/public/assets/PF_Logo.png">
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg:        #080c14;
            --surface:   #0d1320;
            --surface2:  #111827;
            --border:    #1e2d45;
            --border2:   #2a3f5f;
            --primary:   #3b82f6;
            --primary2:  #60a5fa;
            --glow:      rgba(59,130,246,0.35);
            --accent:    #f59e0b;
            --accent2:   #fbbf24;
            --green:     #10b981;
            --red:       #ef4444;
            --text:      #e2e8f0;
            --muted:     #64748b;
            --sidebar-w: 270px;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Space Grotesk', sans-serif;
            background: var(--bg);
            color: var(--text);
            display: flex;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ── SCROLLBAR ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--surface); }
        ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

        /* ── ANIMATED BG GRID ── */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        /* ── SIDEBAR ── */
        .sidebar {
            width: var(--sidebar-w);
            background: var(--surface);
            height: 100vh;
            padding: 2rem 1.25rem;
            position: fixed;
            left: 0; top: 0;
            z-index: 100;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .sidebar::after {
            content: '';
            position: absolute;
            top: 0; right: -1px;
            width: 1px; height: 100%;
            background: linear-gradient(180deg, transparent, var(--primary), transparent);
            opacity: 0.5;
        }

        .logo {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 1.4rem;
            margin-bottom: 2rem;
            padding: 0 0.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: 2px;
        }
        .logo .bracket { color: var(--muted); }
        .logo .name { color: var(--text); }
        .logo .accent { color: var(--primary); }

        .nav-label {
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 2px;
            color: var(--muted);
            padding: 0.5rem 0.75rem;
            text-transform: uppercase;
            margin-top: 0.5rem;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 14px;
            color: var(--muted);
            text-decoration: none;
            border-radius: 10px;
            transition: all 0.2s;
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid transparent;
            position: relative;
            overflow: hidden;
        }
        .nav-item::before {
            content: '';
            position: absolute;
            left: 0; top: 0;
            width: 3px; height: 100%;
            background: var(--primary);
            border-radius: 0 2px 2px 0;
            transform: scaleY(0);
            transition: transform 0.2s;
        }
        .nav-item:hover { background: rgba(59,130,246,0.08); color: var(--text); border-color: var(--border); }
        .nav-item:hover::before { transform: scaleY(1); }
        .nav-item.active { background: rgba(59,130,246,0.12); color: var(--primary2); border-color: rgba(59,130,246,0.25); }
        .nav-item.active::before { transform: scaleY(1); }

        .nav-logout {
            margin-top: auto;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 14px;
            color: var(--muted);
            text-decoration: none;
            border-radius: 10px;
            border: 1px solid transparent;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .nav-logout:hover { background: rgba(239,68,68,0.1); color: var(--red); border-color: rgba(239,68,68,0.2); }

        /* ── MAIN CONTENT ── */
        .main {
            margin-left: var(--sidebar-w);
            padding: 2.5rem 3rem;
            width: calc(100% - var(--sidebar-w));
            min-height: 100vh;
            position: relative;
            z-index: 1;
        }

        /* ── PAGE HEADER ── */
        .page-header {
            margin-bottom: 2.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }
        .page-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--text) 0%, var(--primary2) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.35rem;
        }
        .page-header p { color: var(--muted); font-size: 0.875rem; }
        .page-header strong { color: var(--primary2); }

        /* ── CARDS ── */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .card:hover { border-color: var(--border2); box-shadow: 0 0 30px rgba(59,130,246,0.05); }
        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
            opacity: 0;
            transition: opacity 0.3s;
        }
        .card:hover::before { opacity: 0.4; }

        .card-title {
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-title i { color: var(--primary); width: 16px; height: 16px; }

        /* ── STATS GRID ── */
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }
        .stat-card:hover { border-color: var(--primary); box-shadow: 0 0 25px var(--glow); transform: translateY(-2px); }
        .stat-card::after {
            content: '';
            position: absolute;
            bottom: 0; right: 0;
            width: 80px; height: 80px;
            background: radial-gradient(circle, var(--glow) 0%, transparent 70%);
            pointer-events: none;
        }
        .stat-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 0.6rem; }
        .stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: var(--text); }
        .stat-value.accent { color: var(--accent2); }

        /* ── FORM ELEMENTS ── */
        .form-group { margin-bottom: 1rem; }
        .form-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); margin-bottom: 0.5rem; display: block; }

        input[type="file"],
        input[type="email"],
        input[type="password"],
        select {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s;
            -webkit-appearance: none;
        }
        input:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
        input[type="file"] { cursor: pointer; color: var(--muted); }
        input[type="file"]::-webkit-file-upload-button {
            background: var(--surface2);
            color: var(--primary2);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px 12px;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            margin-right: 10px;
            transition: all 0.2s;
        }
        input[type="file"]::-webkit-file-upload-button:hover { border-color: var(--primary); color: var(--text); }
        select option { background: var(--surface2); }

        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

        /* ── BUTTONS ── */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 10px;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            outline: none;
            transition: all 0.2s;
            text-decoration: none;
            width: 100%;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
            box-shadow: 0 0 20px rgba(59,130,246,0.3);
        }
        .btn-primary:hover { background: var(--primary2); box-shadow: 0 0 30px rgba(59,130,246,0.5); transform: translateY(-1px); }
        .btn-primary:active { transform: translateY(0); }

        .btn-ghost {
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
        }
        .btn-ghost:hover { border-color: var(--border2); color: var(--text); }

        /* ── BADGES ── */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
        .badge.Queued { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
        .badge.Queued::before { background: #94a3b8; }
        .badge.Printing { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); animation: pulse-badge 1.5s infinite; }
        .badge.Printing::before { background: #fbbf24; }
        .badge.Ready { background: rgba(16,185,129,0.1); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
        .badge.Ready::before { background: #34d399; }

        @keyframes pulse-badge { 0%,100% { opacity:1; } 50% { opacity:0.6; } }

        /* ── TABLE ── */
        table { width: 100%; border-collapse: collapse; }
        thead tr { border-bottom: 1px solid var(--border); }
        th {
            padding: 12px 16px;
            text-align: left;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--muted);
        }
        tbody tr {
            border-bottom: 1px solid rgba(30,45,69,0.5);
            transition: background 0.15s;
        }
        tbody tr:hover { background: rgba(59,130,246,0.04); }
        tbody tr:last-child { border-bottom: none; }
        td { padding: 14px 16px; font-size: 0.875rem; color: var(--text); }
        td strong { color: var(--primary2); font-weight: 600; }

        /* ── ACTION BUTTONS IN TABLE ── */
        .view-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(59,130,246,0.1);
            color: var(--primary2);
            padding: 6px 14px;
            border-radius: 7px;
            font-weight: 700;
            font-size: 0.78rem;
            text-decoration: none;
            border: 1px solid rgba(59,130,246,0.2);
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }
        .view-btn:hover { background: rgba(59,130,246,0.2); border-color: var(--primary); box-shadow: 0 0 12px rgba(59,130,246,0.3); }

        .done-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(16,185,129,0.1);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 7px;
            font-weight: 700;
            font-size: 0.78rem;
            text-decoration: none;
            border: 1px solid rgba(16,185,129,0.2);
            margin-left: 8px;
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }
        .done-btn:hover { background: rgba(16,185,129,0.2); border-color: var(--green); box-shadow: 0 0 12px rgba(16,185,129,0.3); }

        .clear-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(239,68,68,0.08);
            color: #f87171;
            padding: 6px 14px;
            border-radius: 7px;
            font-weight: 700;
            font-size: 0.78rem;
            text-decoration: none;
            border: 1px solid rgba(239,68,68,0.2);
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }
        .clear-btn:hover { background: rgba(239,68,68,0.15); border-color: var(--red); box-shadow: 0 0 12px rgba(239,68,68,0.2); }

        /* ── SECTION HEADER ── */
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.25rem;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title i { color: var(--primary); width: 18px; height: 18px; }

        /* ── ORDER ITEM (student) ── */
        .order-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            border-radius: 10px;
            background: var(--surface2);
            border: 1px solid var(--border);
            margin-bottom: 10px;
            transition: all 0.2s;
        }
        .order-item:hover { border-color: var(--border2); transform: translateX(2px); }
        .order-name { font-weight: 600; font-size: 0.875rem; color: var(--text); margin-bottom: 3px; }
        .order-meta { font-size: 0.75rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

        /* ── PAYMENT MODAL ── */
        #pay-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(8px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .modal {
            background: var(--surface);
            border: 1px solid var(--border2);
            padding: 2.5rem;
            border-radius: 24px;
            width: 380px;
            text-align: center;
            box-shadow: 0 0 60px rgba(59,130,246,0.2);
            position: relative;
        }
        .modal::before {
            content: '';
            position: absolute;
            top: 0; left: 20%; right: 20%;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }
        .modal h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; }
        .modal-sub { color: var(--muted); font-size: 0.82rem; margin-bottom: 1.5rem; }
        .modal-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary2);
            margin: 1.25rem 0;
            text-shadow: 0 0 20px var(--glow);
        }
        .modal img { border-radius: 12px; border: 2px solid var(--border2); margin-bottom: 1.5rem; }
        .modal-actions { display: flex; flex-direction: column; gap: 10px; }
        .btn-cancel { background: transparent; color: var(--red); border: 1px solid rgba(239,68,68,0.2); border-radius: 10px; padding: 10px; cursor: pointer; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.875rem; transition: all 0.2s; width: 100%; }
        .btn-cancel:hover { background: rgba(239,68,68,0.1); }

        /* ── LOGIN PAGE ── */
        .login-page {
            width: 100%;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg);
            position: relative;
        }
        .login-page::before {
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 60% 50% at 30% 40%, rgba(59,130,246,0.08) 0%, transparent 70%),
                radial-gradient(ellipse 40% 40% at 70% 70%, rgba(245,158,11,0.05) 0%, transparent 70%);
            pointer-events: none;
        }
        .login-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 3rem 2.5rem;
            width: 420px;
            position: relative;
            box-shadow: 0 0 80px rgba(59,130,246,0.1);
        }
        .login-box::before {
            content: '';
            position: absolute;
            top: 0; left: 15%; right: 15%;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }
        .login-logo {
            text-align: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: 3px;
            margin-bottom: 0.5rem;
        }
        .login-sub {
            text-align: center;
            color: var(--muted);
            font-size: 0.82rem;
            margin-bottom: 2.5rem;
        }
        .login-divider {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 1.25rem 0;
        }
        .login-divider span { font-size: 0.75rem; color: var(--muted); white-space: nowrap; }
        .login-divider::before, .login-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
        .btn-signup {
            background: transparent;
            color: var(--primary2);
            border: 1px solid rgba(59,130,246,0.3);
            border-radius: 10px;
            padding: 12px;
            width: 100%;
            cursor: pointer;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .btn-signup:hover { background: rgba(59,130,246,0.08); border-color: var(--primary); }

        /* ── STAFF ACTIVE BADGE ── */
        .active-dot {
            display: inline-block;
            width: 8px; height: 8px;
            background: var(--green);
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 6px var(--green);
            animation: pulse-dot 2s infinite;
        }
        @keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(0.85)} }

        /* ── EMPTY STATE ── */
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--muted);
        }
        .empty-state i { width: 40px; height: 40px; margin-bottom: 1rem; opacity: 0.3; }
        .empty-state p { font-size: 0.875rem; }

        /* ── GLOW ACCENT ON STAFF CARD ── */
        .staff-active-card {
            border-left: 2px solid var(--primary);
            box-shadow: -4px 0 20px rgba(59,130,246,0.1);
        }

        /* ── TOOLTIP-LIKE MONO TAG ── */
        .mono-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: var(--muted);
            background: var(--surface2);
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid var(--border);
        }
    </style>
</head>
<body>

{% if not session.get('user_id') %}
<!-- ═══════════════ LOGIN PAGE ═══════════════ -->
<div class="login-page">
    <div class="login-box">
        <div class="login-logo"><span style="color:var(--text)">PRINT</span><span style="color:var(--primary)">FLOW</span></div>
        <p class="login-sub">JIIT Smart Printing Portal</p>
        <form action="/auth" method="POST">
            <div class="form-group">
                <label class="form-label">JIIT Email</label>
                <input type="email" name="email" placeholder="yourname@jiit.ac.in" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" placeholder="••••••••••" required>
            </div>
            <button type="submit" name="action" value="login" class="btn btn-primary" style="margin-top:0.5rem;">
                Sign In
            </button>
            <div class="login-divider"><span>or</span></div>
            <button type="submit" name="action" value="signup" class="btn-signup">
                Create Account
            </button>
        </form>
    </div>
</div>

{% else %}
<!-- ═══════════════ APP SHELL ═══════════════ -->

<nav class="sidebar">
    <div class="logo">
        <span class="bracket">[</span>
        <span class="name">PRINT</span><span class="accent">FLOW</span>
        <span class="bracket">]</span>
    </div>

    <span class="nav-label">Navigation</span>
    <a href="/" class="nav-item {{ 'active' if active_page == 'dashboard' else '' }}">
        <i data-lucide="layout-dashboard"></i> Dashboard
    </a>
    {% if session['role'] == 'student' %}
    <a href="/my-orders" class="nav-item {{ 'active' if active_page == 'orders' else '' }}">
        <i data-lucide="printer"></i> My Orders
    </a>
    {% endif %}

    <a href="/logout" class="nav-logout">
        <i data-lucide="log-out"></i> Sign Out
    </a>
</nav>

<main class="main">

    <div class="page-header">
        <h1>
            {% if session['role'] == 'staff' %}Staff Console{% elif active_page == 'orders' %}My Print Orders{% else %}Print Dashboard{% endif %}
        </h1>
        <p>Signed in as <strong>{{ session['email'] }}</strong>
        {% if session['role'] == 'staff' %}&nbsp;·&nbsp;<span style="color:var(--green);">Staff Access</span>{% endif %}
        </p>
    </div>

    <!-- ─── STUDENT VIEW ─── -->
    {% if session['role'] == 'student' %}

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label"><span class="active-dot"></span>Live Queue</div>
            <div class="stat-value" id="live-pages">0 Pages</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Est. Wait Time</div>
            <div class="stat-value accent" id="live-eta">-- mins</div>
        </div>
    </div>

    {% if active_page == 'dashboard' %}
    <div class="card">
        <div class="section-header">
            <div class="section-title">
                <i data-lucide="upload-cloud"></i> New Print Job
            </div>
        </div>
        <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label class="form-label">PDF Document</label>
                <input type="file" name="file" accept=".pdf" required id="fileInput">
            </div>
           <div class="form-grid">
                <div class="form-group">
                    <label class="form-label">Color Mode</label>
                    <select name="color_mode" id="colorMode">
                        <option value="B/W">B&W — ₹3 / page</option>
                        <option value="Color">Color — ₹11 / page</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Page Size</label>
                    <select name="page_size">
                        <option value="A4">A4</option>
                        <option value="A3">A3</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Page Range <span style="color:var(--muted); font-weight:400; text-transform:none; letter-spacing:0;">(optional — e.g. 1-3, 5, 7-9 · leave blank for all)</span></label>
                <input type="text" name="page_range" id="pageRange" placeholder="e.g. 1-3, 5, 7-9  or leave blank for all pages">
            </div>
            <button type="button" onclick="showPayment()" class="btn btn-primary" style="margin-top:0.5rem;">
                <i data-lucide="credit-card" style="width:16px;height:16px;"></i>
                Review & Pay
            </button>
        </form>
    </div>

    {% else %}
    <div class="card">
        <div class="section-header">
            <div class="section-title"><i data-lucide="clock"></i> Order History</div>
        </div>
        <div id="queue-list">
            <div class="empty-state">
                <i data-lucide="inbox"></i>
                <p>Loading your orders…</p>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- ─── STAFF VIEW ─── -->
    {% else %}

    <div class="card staff-active-card">
        <div class="section-header">
            <div class="section-title">
                <i data-lucide="zap"></i> Active Queue
            </div>
            <span class="mono-tag" id="queue-count">0 jobs</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Student</th>
                    <th>Config</th>
                    <th>Pages</th>
                    <th>Price</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% set active_jobs = jobs | selectattr('status', 'ne', 'Ready') | list %}
                {% if active_jobs %}
                    {% for j in active_jobs %}
                    <tr>
                        <td><strong>{{ j.student_email.split('@')[0] }}</strong></td>
                        <td><span class="mono-tag">{{ j.page_size }} · {{ j.color_mode }}</span></td>
                        <td><span class="mono-tag">{{ j.page_count }}pg</span></td>
                        <td style="color:var(--accent2); font-family:'JetBrains Mono',monospace; font-weight:700;">₹{{ j.price }}</td>
                        <td><span class="badge {{j.status}}">{{ j.status }}</span></td>
                        <td>
                            <a href="/view/{{ j.id }}" target="_blank" class="view-btn">
                                <i data-lucide="eye" style="width:12px;height:12px;"></i> View
                            </a>
                            <a href="/update/{{ j.id }}/Ready" class="done-btn">
                                <i data-lucide="check" style="width:12px;height:12px;"></i> Done
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="6">
                        <div class="empty-state">
                            <i data-lucide="check-circle-2"></i>
                            <p>Queue is clear — no pending jobs.</p>
                        </div>
                    </td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>

    <div class="card" style="opacity:0.85;">
        <div class="section-header">
            <div class="section-title">
                <i data-lucide="archive"></i> Completed Jobs
            </div>
            <a href="/clear-ready" onclick="return confirm('Permanently delete all completed jobs?')" class="clear-btn">
                <i data-lucide="trash-2" style="width:12px;height:12px;"></i> Clear All
            </a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Student</th>
                    <th>Config</th>
                    <th>Price</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% set done_jobs = jobs | selectattr('status', 'eq', 'Ready') | list %}
                {% if done_jobs %}
                    {% for j in done_jobs %}
                    <tr style="opacity:0.6;">
                        <td>{{ j.student_email.split('@')[0] }}</td>
                        <td><span class="mono-tag">{{ j.page_size }} · {{ j.color_mode }}</span></td>
                        <td style="font-family:'JetBrains Mono',monospace;">₹{{ j.price }}</td>
                        <td><span class="badge Ready">Ready</span></td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="4">
                        <div class="empty-state">
                            <i data-lucide="inbox"></i>
                            <p>No completed jobs yet.</p>
                        </div>
                    </td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>

    {% endif %}
</main>

<!-- ═══════════════ PAYMENT MODAL ═══════════════ -->
<div id="pay-overlay">
    <div class="modal">
        <h3>Confirm Payment</h3>
        <p class="modal-sub">Scan the QR below and complete payment before submitting.</p>
        <div class="modal-price" id="modalPrice">₹ —</div>
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=jiit@upi&color=60a5fa&bgcolor=0d1320" width="160" height="160">
        <div class="modal-actions">
            <button onclick="document.getElementById('uploadForm').submit()" class="btn btn-primary">
                <i data-lucide="check-circle" style="width:16px;height:16px;"></i> Payment Done — Submit Job
            </button>
            <button onclick="document.getElementById('pay-overlay').style.display='none'" class="btn-cancel">
                Cancel
            </button>
        </div>
    </div>
</div>

<script>
    lucide.createIcons();

    function showPayment() {
        if (!document.getElementById('fileInput').files[0]) return alert("Please select a PDF file first.");
        const rate = document.getElementById('colorMode').value === 'Color' ? 11 : 3;
        document.getElementById('modalPrice').innerText = "₹" + rate + " / page";
        document.getElementById('pay-overlay').style.display = 'flex';
    }

    async function sync() {
        try {
            const r = await fetch('/api/queue');
            const jobs = await r.json();
            let html = '';
            let activePages = 0;
            const email = "{{ session['email'] }}";

            jobs.forEach(j => {
                if (j.status !== 'Ready') activePages += j.page_count;
                if (j.student_email === email) {
                    const rawName = j.file_url.split('/').pop().split('_').slice(2).join('_');
                    const name = decodeURIComponent(rawName) || 'Document';
                    html += `
                    <div class="order-item">
                        <div>
                            <div class="order-name">${name}</div>
                            <div class="order-meta">₹${j.price} &nbsp;·&nbsp; ETA: ${j.eta} &nbsp;·&nbsp; ${j.color_mode} &nbsp;·&nbsp; ${j.page_size}</div>
                        </div>
                        <span class="badge ${j.status}">${j.status}</span>
                    </div>`;
                }
            });

            const livePages = document.getElementById('live-pages');
            const liveEta   = document.getElementById('live-eta');
            const queueList = document.getElementById('queue-list');
            const queueCount = document.getElementById('queue-count');

            if (livePages) livePages.innerText = activePages + " Pages";
            if (liveEta) liveEta.innerText = Math.max(2, Math.floor(activePages / 5) + 2) + " mins";
            if (queueList) queueList.innerHTML = html || `
                <div class="empty-state">
                    <i data-lucide="inbox"></i>
                    <p>No orders placed yet. Submit your first print job from the Dashboard.</p>
                </div>`;
            if (queueCount) {
                const active = jobs.filter(j => j.status !== 'Ready').length;
                queueCount.innerText = active + " job" + (active !== 1 ? 's' : '');
            }
            lucide.createIcons();
        } catch(e) {}
    }

    setInterval(sync, 4000);
    sync();
</script>

{% endif %}
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    jobs = []
    if session.get('role') == 'staff':
        jobs = supabase.table('print_jobs').select("*").order('created_at', desc=True).execute().data
    return render_template_string(HTML_TEMPLATE, jobs=jobs, active_page="dashboard")

@app.route('/my-orders')
def my_orders():
    return render_template_string(HTML_TEMPLATE, active_page="orders")

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form['email'].strip().lower()
    pwd = request.form['password']
    action = request.form['action']
    try:
        if action == "signup":
            res = supabase.auth.sign_up({"email": email, "password": pwd})
        else:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
        role = 'staff' if email == 'staff@jiit.ac.in' else 'student'
        print("\n--- LOGIN DEBUG INFO ---")
        print(f"Raw Email Typed: [{email}]")
        print(f"Role Assigned:   [{role}]")
        print("------------------------\n")
        session.update({'user_id': str(res.user.id), 'email': email, 'role': role})
        return redirect('/')
    except Exception as e:
        print(f"SUPABASE ERROR: {e}")
        return f"<h1>Detailed Auth Error:</h1><p>{e}</p><br><a href='/'>Go Back</a>"

@app.route('/view/<job_id>')
def view_file(job_id):
    try:
        job = supabase.table('print_jobs').select("file_url").eq("id", job_id).single().execute()
        if not job.data:
            return f"<h1>No job found for ID: {job_id}</h1>", 404
        return redirect(job.data['file_url'])
    except Exception as e:
        return f"<h1>Error for ID [{job_id}]:</h1><p>{e}</p><br><a href='/'>Go Back</a>", 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        color_mode = request.form.get('color_mode', 'B/W')
        t_stamp = int(time.time())
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, f"{t_stamp}.pdf")
        file.save(local_path)
        page_range = request.form.get('page_range', '').strip()
        count, final_path = process_pdf_and_count(local_path, local_path, page_range)
        total_price = count * (11 if color_mode == 'Color' else 3)
        active = supabase.table('print_jobs').select("page_count").neq("status", "Ready").execute()
        total_active_pages = sum(j['page_count'] for j in active.data)
        eta_val = max(2, (total_active_pages // 5) + 2)
        storage_name = f"pdf_{t_stamp}_{file.filename.replace(' ', '_')}"
        with open(final_path, 'rb') as f:
            supabase.storage.from_('print-files').upload(storage_name, f, {"content-type": "application/pdf"})
        url = supabase.storage.from_('print-files').get_public_url(storage_name)
        supabase.table('print_jobs').insert({
            "student_email": session['email'], "file_url": url, "page_count": count,
            "price": total_price, "color_mode": color_mode, "eta": f"{eta_val}m",
            "page_size": request.form.get('page_size', 'A4'), "status": "Queued"
        }).execute()
        return redirect('/my-orders')
    except Exception as e:
        print(f"\n--- UPLOAD ERROR --- \n{e}\n--------------------\n")
        return f"<h1>Upload Failed:</h1><p>{e}</p><br><a href='/'>Go Back</a>"

@app.route('/api/queue')
def get_queue():
    res = supabase.table('print_jobs').select("*").execute()
    return jsonify(res.data)

@app.route('/update/<int:job_id>/<status>')
def update_status(job_id, status):
    supabase.table('print_jobs').update({"status": status}).eq("id", job_id).execute()
    return redirect('/')

@app.route('/clear-ready')
def clear_ready():
    supabase.table('print_jobs').delete().eq("status", "Ready").execute()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001)
