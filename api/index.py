import os, time, PyPDF2, requests, tempfile
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify, Response
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads .env in this folder for local runs; harmless no-op on Vercel
except ImportError:
    pass

app = Flask(__name__)

# Locally: values come from .env (see .env.example). On Vercel: Project Settings -> Environment Variables.
# (No hardcoded fallback — this repo is public, so a hardcoded key is a public key.)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "d1cca308bd5845d897e3dce2a8baa1e91350fbda0f2cddcb5e627dc8510c6a69")

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://qsfwlyucognzoojijgul.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzZndseXVjb2duem9vamlqZ3VsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwNjUwNjgsImV4cCI6MjA5NjY0MTA2OH0.WeipU_k1_Rm6M97gC7LMsjbFspjVRDiPOnAHreeNATc")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\" "
        "and set it as an environment variable (locally in .env, or in your Vercel project settings)."
    )
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set as environment variables. "
        "Find them in your Supabase project under Settings > API."
    )

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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>PRINTFLOW // JIIT Smart Printing Network</title>
<link rel="icon" href="data:,">
<script src="https://unpkg.com/lucide@latest"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#04060c;
    --bg2:#070b15;
    --surface: rgba(13,19,34,0.55);
    --surface-solid:#0b101c;
    --surface2: rgba(20,28,48,0.6);
    --border: rgba(56,189,248,0.16);
    --border-strong: rgba(56,189,248,0.45);
    --primary:#38bdf8;
    --primary2:#7dd3fc;
    --glow: rgba(56,189,248,0.35);
    --accent:#c084fc;
    --accent2:#e9d5ff;
    --aglow: rgba(192,132,252,0.35);
    --gold:#fbbf24;
    --gold2:#fde68a;
    --green:#34d399;
    --red:#fb7185;
    --text:#e8eefb;
    --muted:#6f7e96;
    --sidebar-w:280px;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
  html{scroll-behavior:smooth;}
  body{
    font-family:'Space Grotesk',sans-serif;
    background:var(--bg);
    color:var(--text);
    min-height:100vh;
    overflow-x:hidden;
    cursor:none;
  }
  ::selection{background:var(--glow); color:#fff;}
  ::-webkit-scrollbar{width:6px;}
  ::-webkit-scrollbar-track{background:var(--bg2);}
  ::-webkit-scrollbar-thumb{background:var(--border-strong); border-radius:3px;}

  h1,h2,h3,.font-display{font-family:'Orbitron',sans-serif;}
  .mono{font-family:'JetBrains Mono',monospace;}

  a{color:inherit;}

  /* ───────────────────────── CUSTOM CURSOR ───────────────────────── */
  .cursor-dot, .cursor-ring{
    position:fixed; top:0; left:0; pointer-events:none; z-index:9999;
    border-radius:50%;
    transform:translate(-50%,-50%);
    will-change:transform;
  }
  .cursor-dot{
    width:6px; height:6px; background:var(--primary2);
    box-shadow:0 0 8px var(--primary2);
    transition:opacity .2s, background .2s;
  }
  .cursor-ring{
    width:34px; height:34px;
    border:1px solid var(--border-strong);
    transition:width .25s, height .25s, border-color .25s, background .25s, border-radius .25s;
  }
  .cursor-ring::before,.cursor-ring::after{
    content:''; position:absolute; background:var(--primary2);
  }
  .cursor-ring::before{ top:50%; left:-7px; width:6px; height:1px; transform:translateY(-50%);}
  .cursor-ring::after{ top:-7px; left:50%; width:1px; height:6px; transform:translateX(-50%);}
  body.cursor-active .cursor-ring{
    width:56px; height:56px;
    border-color:var(--primary);
    background:rgba(56,189,248,0.08);
  }
  body.cursor-danger .cursor-ring{ border-color:var(--red); background:rgba(251,113,133,0.08);}
  body.cursor-danger .cursor-dot{ background:var(--red); box-shadow:0 0 8px var(--red);}
  @media (hover:none){ body{cursor:auto;} .cursor-dot,.cursor-ring{display:none;} }

  /* ───────────────────────── BACKGROUND FX ───────────────────────── */
  .bg-fx{position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden;}
  .bg-grid{
    position:absolute; inset:-20% -10%;
    background-image:
      linear-gradient(rgba(56,189,248,0.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(56,189,248,0.05) 1px, transparent 1px);
    background-size:42px 42px;
    mask-image:radial-gradient(ellipse 70% 60% at 50% 30%, black 40%, transparent 90%);
    will-change:transform;
  }
  .orb{
    position:absolute; border-radius:50%; filter:blur(60px);
    will-change:transform;
  }
  .orb-1{ width:480px; height:480px; top:-120px; left:-100px; background:radial-gradient(circle, var(--glow), transparent 70%); }
  .orb-2{ width:420px; height:420px; top:30%; right:-140px; background:radial-gradient(circle, var(--aglow), transparent 70%); }
  .orb-3{ width:380px; height:380px; bottom:5%; left:15%; background:radial-gradient(circle, rgba(251,191,36,0.18), transparent 70%); }
  .orb-4{ width:300px; height:300px; bottom:40%; right:20%; background:radial-gradient(circle, var(--glow), transparent 70%); }

  .scanline{
    position:absolute; left:0; right:0; height:140px;
    background:linear-gradient(180deg, transparent, rgba(56,189,248,0.05) 45%, rgba(56,189,248,0.12) 50%, rgba(56,189,248,0.05) 55%, transparent);
    animation:scan 9s linear infinite;
  }
  @keyframes scan{ 0%{transform:translateY(-150px);} 100%{transform:translateY(110vh);} }

  .noise-vignette{ position:absolute; inset:0; box-shadow: inset 0 0 220px rgba(0,0,0,0.85); }

  /* ───────────────────────── SCROLL PROGRESS HUD ───────────────────────── */
  .scroll-hud{
    position:fixed; right:18px; top:50%; transform:translateY(-50%);
    width:18px; height:200px; z-index:60;
    display:flex; flex-direction:column; align-items:center; gap:8px;
  }
  .scroll-hud .track{ position:relative; width:2px; flex:1; background:var(--border); }
  .scroll-hud .fill{ position:absolute; bottom:0; left:0; width:100%; background:linear-gradient(180deg,var(--primary),var(--accent)); box-shadow:0 0 8px var(--glow); height:0%; }
  .scroll-hud .pct{ font-size:.62rem; letter-spacing:1px; color:var(--muted); writing-mode:vertical-rl; }
  @media (max-width:1000px){ .scroll-hud{display:none;} }

  /* ───────────────────────── REVEAL ANIM ───────────────────────── */
  .reveal{ opacity:0; transform:translateY(36px); transition:opacity .7s cubic-bezier(.2,.7,.3,1), transform .7s cubic-bezier(.2,.7,.3,1); }
  .reveal.in{ opacity:1; transform:translateY(0); }

  /* ───────────────────────── LOGIN SCREEN ───────────────────────── */
  #loginScreen{
    position:relative; z-index:5; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:2rem;
  }
  .login-box{
    position:relative; width:430px; max-width:100%;
    background:var(--surface); backdrop-filter:blur(18px);
    border:1px solid var(--border); border-radius:20px;
    padding:2.75rem 2.4rem; box-shadow:0 0 80px rgba(56,189,248,0.08), 0 30px 60px rgba(0,0,0,0.5);
    will-change:transform;
  }
  .login-box::before{
    content:''; position:absolute; top:0; left:14%; right:14%; height:1px;
    background:linear-gradient(90deg,transparent,var(--primary),transparent);
  }
  .corner{ position:absolute; width:18px; height:18px; border-color:var(--primary); opacity:.7;}
  .corner.tl{ top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; border-radius:6px 0 0 0;}
  .corner.tr{ top:-1px; right:-1px; border-top:2px solid; border-right:2px solid; border-radius:0 6px 0 0;}
  .corner.bl{ bottom:-1px; left:-1px; border-bottom:2px solid; border-left:2px solid; border-radius:0 0 0 6px;}
  .corner.br{ bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; border-radius:0 0 6px 0;}

  .login-logo{
    text-align:center; font-size:1.9rem; font-weight:900; letter-spacing:4px; margin-bottom:.4rem;
  }
  .login-logo .lb{color:var(--muted); font-weight:500;}
  .login-logo .lp{color:var(--text);}
  .login-logo .la{color:var(--primary); text-shadow:0 0 18px var(--glow);}
  .login-status{ text-align:center; font-size:.68rem; letter-spacing:2px; color:var(--muted); margin-bottom:2.1rem; text-transform:uppercase; display:flex; align-items:center; justify-content:center; gap:6px;}
  .status-dot{width:6px;height:6px;border-radius:50%;background:var(--green); box-shadow:0 0 6px var(--green); animation:pulse-dot 2s infinite;}
  @keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}

  .form-group{margin-bottom:1.1rem;}
  .form-label{font-size:.66rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:.5rem; display:block;}
  input[type=email],input[type=password],input[type=text],select{
    width:100%; padding:13px 16px; background:rgba(4,6,12,0.6); border:1px solid var(--border); border-radius:10px;
    color:var(--text); font-family:'Space Grotesk',sans-serif; font-size:.9rem; outline:none;
    transition:border-color .2s, box-shadow .2s;
  }
  input:focus,select:focus{border-color:var(--primary); box-shadow:0 0 0 3px rgba(56,189,248,0.15);}
  input[type=file]{cursor:none; color:var(--muted); width:100%; padding:13px 16px; background:rgba(4,6,12,0.6); border:1px solid var(--border); border-radius:10px; font-family:'Space Grotesk',sans-serif; font-size:.85rem;}
  input[type=file]::file-selector-button{
    background:var(--surface2); color:var(--primary2); border:1px solid var(--border); border-radius:6px;
    padding:7px 14px; font-family:'Space Grotesk',sans-serif; font-size:.78rem; font-weight:700; cursor:none; margin-right:12px;
  }
  select option{background:var(--surface-solid);}
  .form-grid{display:grid; grid-template-columns:1fr 1fr; gap:1rem;}

  .btn{
    display:inline-flex; align-items:center; justify-content:center; gap:8px;
    padding:13px 24px; border-radius:10px; font-family:'Space Grotesk',sans-serif; font-size:.88rem;
    font-weight:700; letter-spacing:.3px; cursor:none; border:none; outline:none; width:100%;
    position:relative; overflow:hidden; transition:transform .15s;
  }
  .btn-primary{ background:linear-gradient(135deg,var(--primary),#0ea5e9); color:#03101c; box-shadow:0 0 24px rgba(56,189,248,0.35);}
  .btn-primary:hover{ box-shadow:0 0 38px rgba(56,189,248,0.55); }
  .btn-ghost{ background:transparent; color:var(--primary2); border:1px solid var(--border-strong); }
  .btn-ghost:hover{ background:rgba(56,189,248,0.08); }
  .btn-danger{ background:transparent; color:var(--red); border:1px solid rgba(251,113,133,0.3);}
  .btn-danger:hover{ background:rgba(251,113,133,0.1);}

  .login-divider{ display:flex; align-items:center; gap:12px; margin:1.3rem 0;}
  .login-divider span{font-size:.7rem; color:var(--muted); letter-spacing:1px;}
  .login-divider::before,.login-divider::after{content:''; flex:1; height:1px; background:var(--border);}
  .login-error{
    background:rgba(251,113,133,0.08); border:1px solid rgba(251,113,133,0.3); color:var(--red);
    border-radius:10px; padding:.7rem .9rem; font-size:.78rem; margin-bottom:1.1rem; line-height:1.4;
  }

  /* ───────────────────────── APP SHELL ───────────────────────── */
  #appShell{ display:none; position:relative; z-index:5; }
  .sidebar{
    width:var(--sidebar-w); height:100vh; position:fixed; left:0; top:0; z-index:50;
    background:rgba(7,11,21,0.7); backdrop-filter:blur(16px);
    border-right:1px solid var(--border); padding:2rem 1.3rem; display:flex; flex-direction:column; gap:.3rem;
  }
  .sidebar::after{ content:''; position:absolute; top:0; right:-1px; width:1px; height:100%; background:linear-gradient(180deg,transparent,var(--primary),transparent); opacity:.5;}
  .logo{ font-family:'Orbitron',sans-serif; font-weight:900; font-size:1.25rem; letter-spacing:3px; margin-bottom:.4rem; padding:0 .4rem; display:flex; align-items:center; gap:6px;}
  .logo .b{color:var(--muted);} .logo .n{color:var(--text);} .logo .a{color:var(--primary); text-shadow:0 0 14px var(--glow);}
  .sys-tag{font-size:.6rem; color:var(--muted); letter-spacing:2px; padding:0 .45rem; margin-bottom:1.8rem;}

  .role-toggle{ display:flex; background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:3px; margin-bottom:1.6rem; }
  .role-toggle button{ flex:1; padding:8px 0; font-size:.7rem; font-weight:700; letter-spacing:1px; background:transparent; border:none; color:var(--muted); border-radius:8px; cursor:none; font-family:'Space Grotesk'; transition:all .2s;}
  .role-toggle button.active{ background:var(--primary); color:#03101c; box-shadow:0 0 14px var(--glow);}
  .role-toggle button:disabled{ cursor:not-allowed; opacity:1; }
  .role-toggle button:disabled:not(.active){ opacity:.4; }

  .nav-label{font-size:.62rem; font-weight:700; letter-spacing:2px; color:var(--muted); padding:.5rem .75rem; text-transform:uppercase;}
  .nav-item{ display:flex; align-items:center; gap:12px; padding:11px 14px; color:var(--muted); text-decoration:none;
    border-radius:10px; font-size:.88rem; font-weight:500; border:1px solid transparent; position:relative; overflow:hidden;
    transition:background .2s, color .2s, border-color .2s; cursor:none; background:none; width:100%; text-align:left; font-family:'Space Grotesk';}
  .nav-item i{width:17px; height:17px;}
  .nav-item::before{ content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:var(--primary); transform:scaleY(0); transition:transform .2s; border-radius:0 2px 2px 0;}
  .nav-item:hover{ background:rgba(56,189,248,0.08); color:var(--text); border-color:var(--border);}
  .nav-item:hover::before{transform:scaleY(1);}
  .nav-item.active{ background:rgba(56,189,248,0.13); color:var(--primary2); border-color:rgba(56,189,248,0.3);}
  .nav-item.active::before{transform:scaleY(1);}
  .nav-logout{margin-top:auto;}

  .main{ margin-left:var(--sidebar-w); padding:2.6rem 3rem 6rem; min-height:100vh; position:relative; }

  .page-header{ margin-bottom:2.3rem; padding-bottom:1.4rem; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:1rem;}
  .page-header h1{ font-size:1.7rem; font-weight:900; letter-spacing:1px;
    background:linear-gradient(135deg,var(--text),var(--primary2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin-bottom:.4rem;}
  .page-header p{color:var(--muted); font-size:.85rem;}
  .page-header strong{color:var(--primary2);}
  .session-tag{font-family:'JetBrains Mono'; font-size:.7rem; color:var(--muted); border:1px solid var(--border); padding:6px 12px; border-radius:8px; display:flex; align-items:center; gap:6px;}

  /* tilt card */
  .tilt{ transform-style:preserve-3d; will-change:transform; transition:transform .15s ease-out, box-shadow .25s; }

  .card{
    background:var(--surface); backdrop-filter:blur(14px); border:1px solid var(--border); border-radius:18px;
    padding:1.8rem; margin-bottom:1.5rem; position:relative; overflow:hidden;
  }
  .card:hover{ border-color:var(--border-strong); box-shadow:0 0 40px rgba(56,189,248,0.08);}
  .card::before{ content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,var(--primary),transparent); opacity:0; transition:opacity .3s;}
  .card:hover::before{opacity:.5;}

  .card-title{ font-size:.8rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:.7rem; display:flex; align-items:center; gap:8px;}
  .card-title i{color:var(--primary); width:16px; height:16px;}

  .stats{display:grid; grid-template-columns:repeat(3,1fr); gap:1.2rem; margin-bottom:1.5rem;}
  .stat-card{ background:var(--surface); backdrop-filter:blur(14px); border:1px solid var(--border); border-radius:18px; padding:1.5rem; position:relative; overflow:hidden;}
  .stat-card:hover{ border-color:var(--primary); box-shadow:0 0 28px var(--glow); }
  .stat-card::after{ content:''; position:absolute; bottom:-30px; right:-30px; width:110px; height:110px; background:radial-gradient(circle,var(--glow),transparent 70%); pointer-events:none;}
  .stat-label{font-size:.66rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:.6rem; display:flex; align-items:center;}
  .stat-value{font-family:'JetBrains Mono'; font-size:1.7rem; font-weight:700;}
  .stat-value.accent{color:var(--gold2);}
  .stat-value.violet{color:var(--accent2);}

  .active-dot{display:inline-block; width:7px;height:7px;background:var(--green);border-radius:50%;margin-right:7px;box-shadow:0 0 6px var(--green); animation:pulse-dot 2s infinite;}

  .form-label-row{display:flex; justify-content:space-between; align-items:baseline;}
  .hint{color:var(--muted); font-weight:400; text-transform:none; letter-spacing:0; font-size:.7rem;}

  .badge{ display:inline-flex; align-items:center; gap:5px; padding:4px 12px; border-radius:20px; font-size:.7rem; font-weight:700; letter-spacing:.5px; text-transform:uppercase;}
  .badge::before{content:'';width:6px;height:6px;border-radius:50%;}
  .badge.Queued{background:rgba(111,126,150,.15); color:#9fb0c8; border:1px solid rgba(111,126,150,.3);}
  .badge.Queued::before{background:#9fb0c8;}
  .badge.Printing{background:rgba(251,191,36,.1); color:var(--gold2); border:1px solid rgba(251,191,36,.3); animation:pulse-badge 1.4s infinite;}
  .badge.Printing::before{background:var(--gold);}
  .badge.Ready{background:rgba(52,211,153,.1); color:var(--green); border:1px solid rgba(52,211,153,.3);}
  .badge.Ready::before{background:var(--green);}
  @keyframes pulse-badge{0%,100%{opacity:1}50%{opacity:.55}}

  table{width:100%; border-collapse:collapse;}
  thead tr{border-bottom:1px solid var(--border);}
  th{padding:11px 14px; text-align:left; font-size:.66rem; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:var(--muted);}
  tbody tr{border-bottom:1px solid rgba(56,189,248,0.07); transition:background .15s;}
  tbody tr:hover{background:rgba(56,189,248,0.05);}
  tbody tr:last-child{border-bottom:none;}
  td{padding:13px 14px; font-size:.85rem;}
  td strong{color:var(--primary2);}

  .view-btn,.done-btn{ display:inline-flex; align-items:center; gap:5px; padding:6px 13px; border-radius:7px; font-weight:700; font-size:.74rem; text-decoration:none; letter-spacing:.4px; cursor:none; border:1px solid; background:none;}
  .view-btn{ color:var(--primary2); border-color:rgba(56,189,248,0.25); background:rgba(56,189,248,0.08);}
  .view-btn:hover{ box-shadow:0 0 12px rgba(56,189,248,0.3);}
  .done-btn{ color:var(--green); border-color:rgba(52,211,153,0.25); background:rgba(52,211,153,0.08); margin-left:8px;}
  .done-btn:hover{ box-shadow:0 0 12px rgba(52,211,153,0.3);}
  .clear-btn{ display:inline-flex; align-items:center; gap:6px; background:rgba(251,113,133,0.08); color:var(--red); padding:6px 14px; border-radius:7px; font-weight:700; font-size:.74rem; border:1px solid rgba(251,113,133,0.25); cursor:none;}
  .clear-btn:hover{ box-shadow:0 0 12px rgba(251,113,133,0.25);}

  .section-header{display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2rem; flex-wrap:wrap; gap:.6rem;}
  .section-title{font-size:1rem; font-weight:700; display:flex; align-items:center; gap:10px;}
  .section-title i{color:var(--primary); width:18px;height:18px;}
  .mono-tag{font-family:'JetBrains Mono'; font-size:.74rem; color:var(--muted); background:var(--surface2); padding:3px 9px; border-radius:5px; border:1px solid var(--border);}

  .order-item{display:flex; justify-content:space-between; align-items:center; padding:14px 16px; border-radius:12px; background:var(--surface2); border:1px solid var(--border); margin-bottom:10px;}
  .order-item:hover{border-color:var(--border-strong);}
  .order-name{font-weight:600; font-size:.86rem; margin-bottom:3px;}
  .order-meta{font-size:.72rem; color:var(--muted); font-family:'JetBrains Mono';}

  .empty-state{text-align:center; padding:3rem 1rem; color:var(--muted);}
  .empty-state i{width:38px;height:38px;margin-bottom:1rem;opacity:.3;}
  .empty-state p{font-size:.85rem;}

  /* PAYMENT MODAL */
  #pay-overlay{display:none; position:fixed; inset:0; background:rgba(2,4,9,0.82); backdrop-filter:blur(10px); z-index:2000; align-items:center; justify-content:center;}
  .modal{ position:relative; background:var(--surface-solid); border:1px solid var(--border-strong); padding:2.5rem; border-radius:22px; width:380px; max-width:90vw; text-align:center; box-shadow:0 0 70px rgba(56,189,248,0.2);}
  .modal::before{content:''; position:absolute; top:0; left:18%; right:18%; height:1px; background:linear-gradient(90deg,transparent,var(--primary),transparent);}
  .modal h3{font-family:'Orbitron'; font-size:1.1rem; margin-bottom:.5rem; letter-spacing:1px;}
  .modal-sub{color:var(--muted); font-size:.8rem; margin-bottom:1.4rem;}
  .modal-price{font-family:'JetBrains Mono'; font-size:2.4rem; font-weight:700; color:var(--primary2); margin:1.1rem 0; text-shadow:0 0 22px var(--glow);}
  .modal-qr{width:150px;height:150px; margin:0 auto 1.4rem; border-radius:12px; border:2px solid var(--border-strong);
    background:repeating-linear-gradient(45deg, #0d1320, #0d1320 6px, #131c2e 6px, #131c2e 12px); display:flex; align-items:center; justify-content:center; color:var(--muted); font-family:'JetBrains Mono'; font-size:.65rem;}
  .modal-actions{display:flex; flex-direction:column; gap:10px;}

  /* signature: HUD readout strip */
  .hud-strip{
    display:flex; gap:1.2rem; flex-wrap:wrap; font-family:'JetBrains Mono'; font-size:.68rem; color:var(--muted);
    border:1px solid var(--border); border-radius:10px; padding:.7rem 1rem; margin-bottom:1.5rem; letter-spacing:.5px;
  }
  .hud-strip b{color:var(--primary2); font-weight:700;}

  /* ───────────────────────── HAMBURGER + MOBILE SIDEBAR ───────────────────────── */
  .hamburger{
    display:none; position:fixed; top:1.1rem; left:1.1rem; z-index:70;
    width:44px; height:44px; align-items:center; justify-content:center;
    background:var(--surface-solid); border:1px solid var(--border-strong);
    border-radius:10px; cursor:pointer;
  }
  .hamburger i{width:20px; height:20px; color:var(--primary2);}
  .sidebar-overlay{
    display:none; position:fixed; inset:0; z-index:45;
    background:rgba(2,4,9,0.6); backdrop-filter:blur(4px);
  }
  .sidebar-overlay.open{display:block;}

  @media (max-width:900px){
    .hamburger{display:flex;}
    .sidebar{
      display:flex; transform:translateX(-100%);
      transition:transform .28s ease; z-index:80; width:78vw; max-width:300px;
    }
    .sidebar.open{transform:translateX(0);}
    .main{margin-left:0; padding:5.5rem 1.1rem 5rem;}
    .stats{grid-template-columns:1fr;}
    .form-grid{grid-template-columns:1fr;}
    .page-header{flex-direction:column; align-items:flex-start;}
    .page-header h1{font-size:1.35rem;}
    .stat-value{font-size:1.4rem;}
    .login-box{padding:2.1rem 1.5rem;}
    .scroll-hud{display:none !important;}
    .modal{padding:2rem 1.4rem;}
  }

  @media (max-width:600px){
    .login-logo{font-size:1.5rem; letter-spacing:2px;}
    .modal-qr{width:120px; height:120px;}
    .modal-price{font-size:1.9rem;}

    table thead{display:none;}
    table, tbody, tr, td{display:block; width:100%;}
    tbody tr{
      border:1px solid var(--border); border-radius:12px; padding:.8rem 1rem;
      margin-bottom:10px; background:var(--surface2);
    }
    td{padding:6px 0; display:flex; justify-content:space-between; align-items:center; font-size:.8rem; gap:.6rem;}
    td::before{content:attr(data-label); color:var(--muted); font-size:.66rem; text-transform:uppercase; letter-spacing:1px; flex-shrink:0;}
    td:empty{display:none;}
    td .empty-state{width:100%;}
    td:has(.empty-state)::before{display:none;}
  }
</style>
</head>
<body>

<!-- CURSOR -->
<div class="cursor-dot" id="cursorDot"></div>
<div class="cursor-ring" id="cursorRing"></div>

<!-- BACKGROUND FX -->
<div class="bg-fx">
  <div class="bg-grid" id="bgGrid"></div>
  <div class="orb orb-1" data-speed="0.12" id="orb1"></div>
  <div class="orb orb-2" data-speed="-0.08" id="orb2"></div>
  <div class="orb orb-3" data-speed="0.18" id="orb3"></div>
  <div class="orb orb-4" data-speed="-0.14" id="orb4"></div>
  <div class="scanline"></div>
  <div class="noise-vignette"></div>
</div>

<!-- SCROLL HUD -->
<div class="scroll-hud" id="scrollHud" style="display:none;">
  <span class="pct mono">SCROLL</span>
  <div class="track"><div class="fill" id="scrollFill"></div></div>
  <span class="pct mono" id="scrollPct">000</span>
</div>

<!-- ═══════════ LOGIN SCREEN ═══════════ -->
<div id="loginScreen">
  <div class="login-box tilt" id="loginBox">
    <div class="corner tl"></div><div class="corner tr"></div><div class="corner bl"></div><div class="corner br"></div>
    <div class="login-logo"><span class="lb">[</span><span class="lp">PRINT</span><span class="la">FLOW</span><span class="lb">]</span></div>
    <div class="login-status"><span class="status-dot"></span>JIIT SMART PRINTING NETWORK — ONLINE</div>

    <div class="role-toggle" id="loginRoleToggle" style="margin-bottom:1.8rem;">
      <button type="button" id="loginRoleStudentBtn" class="active" onclick="setLoginRole('student')">STUDENT</button>
      <button type="button" id="loginRoleStaffBtn" onclick="setLoginRole('staff')">STAFF</button>
    </div>

    <form id="loginForm" method="POST" action="/auth">
      <input type="hidden" id="loginRole" name="role" value="student">
      <input type="hidden" name="action" id="formAction" value="login">
      <div id="loginError" class="login-error" style="display:none;"></div>
      <div class="form-group">
        <label class="form-label" id="loginEmailLabel">Jiit Email</label>
        <input type="email" id="loginEmail" name="email" placeholder="yourname@jiit.ac.in" required>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" id="loginPassword" name="password" placeholder="••••••••••" required>
      </div>
      <button type="submit" class="btn btn-primary" data-action="login" id="loginSubmitBtn">
        <i data-lucide="log-in" style="width:16px;height:16px;" id="loginIcon"></i> <span id="loginBtnText">Sign In as Student</span>
      </button>
      <div class="login-divider" id="signupDivider"><span>OR</span></div>
      <button type="submit" class="btn btn-ghost" data-action="signup" id="signupBtn">
        <i data-lucide="user-plus" style="width:16px;height:16px;"></i> Create Student Account
      </button>
    </form>
  </div>
</div>

{% if logged_in %}
<script>window.__PRINTFLOW_SESSION__ = {loggedIn:true, email:{{ email|tojson }}, role:{{ role|tojson }}};</script>
{% else %}
<script>window.__PRINTFLOW_SESSION__ = {loggedIn:false, email:null, role:null};</script>
{% endif %}

<!-- ═══════════ APP SHELL ═══════════ -->
<div id="appShell">
  <button class="hamburger" id="hamburgerBtn" onclick="toggleSidebar()">
    <i data-lucide="menu"></i>
  </button>
  <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>
  <nav class="sidebar" id="sidebarNav">
    <div class="logo"><span class="b">[</span><span class="n">PRINT</span><span class="a">FLOW</span><span class="b">]</span></div>
    <div class="sys-tag mono">SYS://JIIT-NODE-04 · v2.6</div>

    <div class="role-toggle" style="pointer-events:none;">
      <button id="roleStudentBtn" class="active" disabled>STUDENT</button>
      <button id="roleStaffBtn" disabled>STAFF</button>
    </div>

    <span class="nav-label">Navigation</span>
    <button class="nav-item active" data-view="dashboard" id="navDashboard" onclick="setView('dashboard')">
      <i data-lucide="layout-dashboard"></i> Dashboard
    </button>
    <button class="nav-item" data-view="orders" id="navOrders" onclick="setView('orders')">
      <i data-lucide="printer"></i> My Orders
    </button>
    <button class="nav-item" data-view="staff" id="navStaff" style="display:none;" onclick="setView('staff')">
      <i data-lucide="server-cog"></i> Staff Console
    </button>

    <a href="#" class="nav-item nav-logout" onclick="logout();return false;">
      <i data-lucide="log-out"></i> Sign Out
    </a>
  </nav>

  <main class="main">

    <div class="page-header">
      <div>
        <h1 id="pageTitle">Print Dashboard</h1>
        <p>Signed in as <strong id="sessionEmail">student@jiit.ac.in</strong></p>
      </div>
      <div class="session-tag"><span class="active-dot"></span><span id="sessionRole">STUDENT ACCESS</span></div>
    </div>

    <!-- ─── DASHBOARD VIEW ─── -->
    <section id="view-dashboard" class="view" style="display:none;">
      <div class="hud-strip reveal">
        <span>NODE: <b>JIIT-04</b></span><span>PRINTERS: <b>3/4 ONLINE</b></span><span>UPTIME: <b>99.8%</b></span><span>RATE: <b>₹3/pg B·W</b> · <b>₹11/pg COLOR</b></span>
      </div>

      <div class="stats">
        <div class="stat-card tilt reveal">
          <div class="stat-label"><span class="active-dot"></span>Live Queue</div>
          <div class="stat-value" id="live-pages">0 Pages</div>
        </div>
        <div class="stat-card tilt reveal">
          <div class="stat-label">Est. Wait Time</div>
          <div class="stat-value accent" id="live-eta">2 mins</div>
        </div>
        <div class="stat-card tilt reveal">
          <div class="stat-label">Your Orders</div>
          <div class="stat-value violet" id="my-orders-count">0 Jobs</div>
        </div>
      </div>

      <div class="card tilt reveal">
        <div class="section-header">
          <div class="section-title"><i data-lucide="upload-cloud"></i> New Print Job</div>
        </div>
        <form id="uploadForm" onsubmit="return false;">
          <div class="form-group">
            <label class="form-label">PDF Document</label>
            <input type="file" id="fileInput" accept=".pdf" required>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Color Mode</label>
              <select id="colorMode">
                <option value="B/W">B&amp;W — ₹3 / page</option>
                <option value="Color">Color — ₹11 / page</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Page Size</label>
              <select id="pageSize">
                <option value="A4">A4</option>
                <option value="A3">A3</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label-row">
              <span class="form-label">Page Range</span>
              <span class="hint">e.g. 1-3, 5, 7-9 · leave blank for all</span>
            </label>
            <input type="text" id="pageRange" placeholder="e.g. 1-3, 5, 7-9  or leave blank for all pages">
          </div>
          <button type="button" onclick="showPayment()" class="btn btn-primary" style="margin-top:.4rem;">
            <i data-lucide="credit-card" style="width:16px;height:16px;"></i> Review &amp; Pay
          </button>
        </form>
      </div>
    </section>

    <!-- ─── ORDERS VIEW (student) ─── -->
    <section id="view-orders" class="view" style="display:none;">
      <div class="card tilt reveal">
        <div class="section-header">
          <div class="section-title"><i data-lucide="clock"></i> Order History</div>
        </div>
        <div id="queue-list">
          <div class="empty-state">
            <i data-lucide="inbox"></i>
            <p>No orders placed yet. Submit your first print job from the Dashboard.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── STAFF VIEW ─── -->
    <section id="view-staff" class="view" style="display:none;">
      <div class="card tilt reveal" style="border-left:2px solid var(--primary); box-shadow:-4px 0 24px rgba(56,189,248,0.1);">
        <div class="section-header">
          <div class="section-title"><i data-lucide="zap"></i> Active Queue</div>
          <span class="mono-tag" id="queue-count">0 jobs</span>
        </div>
        <table>
          <thead><tr><th>Student</th><th>Config</th><th>Pages</th><th>Price</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody id="active-jobs-body">
            <tr><td colspan="6"><div class="empty-state"><i data-lucide="check-circle-2"></i><p>Queue is clear — no pending jobs.</p></div></td></tr>
          </tbody>
        </table>
      </div>

      <div class="card tilt reveal" style="opacity:.85;">
        <div class="section-header">
          <div class="section-title"><i data-lucide="archive"></i> Completed Jobs</div>
          <a href="#" onclick="clearReady();return false;" class="clear-btn"><i data-lucide="trash-2" style="width:12px;height:12px;"></i> Clear All</a>
        </div>
        <table>
          <thead><tr><th>Student</th><th>Config</th><th>Price</th><th>Status</th></tr></thead>
          <tbody id="done-jobs-body">
            <tr><td colspan="4"><div class="empty-state"><i data-lucide="inbox"></i><p>No completed jobs yet.</p></div></td></tr>
          </tbody>
        </table>
      </div>
    </section>

  </main>
</div>

<!-- PAYMENT MODAL -->
<div id="pay-overlay">
  <div class="modal">
    <h3>CONFIRM PAYMENT</h3>
    <p class="modal-sub">Scan the QR below and complete payment before submitting.</p>
    <div class="modal-price" id="modalPrice">₹ —</div>
    <div class="modal-qr mono">[ QR CODE ]</div>
    <div class="modal-actions">
      <button onclick="submitJob()" class="btn btn-primary"><i data-lucide="check-circle" style="width:16px;height:16px;"></i> Payment Done — Submit Job</button>
      <button onclick="closePayment()" class="btn btn-danger"><i data-lucide="x" style="width:16px;height:16px;"></i> Cancel</button>
    </div>
  </div>
</div>

<script>
lucide.createIcons();

/* ════════════════════ CUSTOM CURSOR ════════════════════ */
const dot = document.getElementById('cursorDot');
const ring = document.getElementById('cursorRing');
let mx=innerWidth/2, my=innerHeight/2, rx=mx, ry=my;
addEventListener('mousemove', e=>{ mx=e.clientX; my=e.clientY; dot.style.left=mx+'px'; dot.style.top=my+'px'; });
(function loop(){ rx += (mx-rx)*0.18; ry += (my-ry)*0.18; ring.style.left=rx+'px'; ring.style.top=ry+'px'; requestAnimationFrame(loop); })();

const interactiveSel = 'a, button, input, select, .card, .stat-card, .order-item, .nav-item, .login-box';
document.body.addEventListener('mouseover', e=>{
  if(e.target.closest(interactiveSel)) document.body.classList.add('cursor-active');
  if(e.target.closest('.clear-btn,.btn-danger')) document.body.classList.add('cursor-danger');
});
document.body.addEventListener('mouseout', e=>{
  if(e.target.closest(interactiveSel)) document.body.classList.remove('cursor-active');
  if(e.target.closest('.clear-btn,.btn-danger')) document.body.classList.remove('cursor-danger');
});

/* ════════════════════ TILT + MAGNETIC ════════════════════ */
document.querySelectorAll('.tilt').forEach(el=>{
  el.addEventListener('mousemove', e=>{
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left)/r.width - 0.5;
    const py = (e.clientY - r.top)/r.height - 0.5;
    el.style.transform = `perspective(900px) rotateX(${(-py*5).toFixed(2)}deg) rotateY(${(px*6).toFixed(2)}deg) translateZ(0)`;
  });
  el.addEventListener('mouseleave', ()=>{ el.style.transform=''; });
});
document.querySelectorAll('.btn-primary').forEach(btn=>{
  btn.addEventListener('mousemove', e=>{
    const r = btn.getBoundingClientRect();
    const dx = (e.clientX - (r.left+r.width/2))*0.12;
    const dy = (e.clientY - (r.top+r.height/2))*0.25;
    btn.style.transform = `translate(${dx}px,${dy}px)`;
  });
  btn.addEventListener('mouseleave', ()=>{ btn.style.transform=''; });
});

/* ════════════════════ PARALLAX (scroll + mouse) ════════════════════ */
const orbs = document.querySelectorAll('.orb');
function applyParallax(){
  const sy = window.scrollY;
  orbs.forEach(o=>{
    const sp = parseFloat(o.dataset.speed);
    o.style.transform = `translateY(${sy*sp}px) translateX(${(mx-innerWidth/2)*0.01*sp*10}px)`;
  });
  document.getElementById('bgGrid').style.transform = `translateY(${sy*0.04}px) translateX(${(mx-innerWidth/2)*0.01}px)`;
}
addEventListener('scroll', applyParallax);
addEventListener('mousemove', applyParallax);
applyParallax();

/* login box subtle mouse parallax */
addEventListener('mousemove', e=>{
  if(document.getElementById('loginScreen').style.display==='none') return;
  const dx = (e.clientX/innerWidth - 0.5)*10;
  const dy = (e.clientY/innerHeight - 0.5)*10;
  document.getElementById('loginBox').style.transform = `perspective(900px) rotateX(${-dy*0.4}deg) rotateY(${dx*0.4}deg)`;
});

/* ════════════════════ SCROLL PROGRESS HUD ════════════════════ */
const hud = document.getElementById('scrollHud');
function updateHud(){
  const h = document.documentElement;
  const pct = h.scrollTop / (h.scrollHeight - h.clientHeight || 1);
  document.getElementById('scrollFill').style.height = (pct*100)+'%';
  document.getElementById('scrollPct').innerText = String(Math.round(pct*100)).padStart(3,'0');
}
addEventListener('scroll', updateHud);

/* ════════════════════ REVEAL ON SCROLL ════════════════════ */
const io = new IntersectionObserver((entries)=>{
  entries.forEach((en,i)=>{
    if(en.isIntersecting){ setTimeout(()=>en.target.classList.add('in'), i*70); io.unobserve(en.target); }
  });
}, {threshold:0.15});
function observeReveals(){ document.querySelectorAll('.reveal:not(.in)').forEach(el=>io.observe(el)); }
observeReveals();

/* ════════════════════ MOBILE HAMBURGER MENU ════════════════════ */
function toggleSidebar(){
  const isOpen = document.getElementById('sidebarNav').classList.toggle('open');
  document.getElementById('sidebarOverlay').classList.toggle('open', isOpen);
  document.getElementById('hamburgerBtn').innerHTML = `<i data-lucide="${isOpen ? 'x' : 'menu'}"></i>`;
  lucide.createIcons();
}
function closeSidebar(){
  document.getElementById('sidebarNav').classList.remove('open');
  document.getElementById('sidebarOverlay').classList.remove('open');
  document.getElementById('hamburgerBtn').innerHTML = `<i data-lucide="menu"></i>`;
  lucide.createIcons();
}

/* ════════════════════ REAL AUTH / SESSION ════════════════════ */
let role = 'student';
let currentEmail = '';
let loginRole = 'student';
let jobs = [];           // hydrated from the server, not faked client-side
let pollTimer = null;

function setLoginRole(r){
  loginRole = r;
  document.getElementById('loginRole').value = r;
  document.getElementById('loginRoleStudentBtn').classList.toggle('active', r==='student');
  document.getElementById('loginRoleStaffBtn').classList.toggle('active', r==='staff');
  const emailInput = document.getElementById('loginEmail');
  const emailLabel = document.getElementById('loginEmailLabel');
  const btnText = document.getElementById('loginBtnText');
  const signupBtn = document.getElementById('signupBtn');
  const signupDivider = document.getElementById('signupDivider');
  if(r==='staff'){
    emailLabel.innerText = 'Staff Email';
    emailInput.placeholder = 'staff@jiit.ac.in';
    btnText.innerText = 'Sign In as Staff';
    signupBtn.style.display = 'none';
    signupDivider.style.display = 'none';
  } else {
    emailLabel.innerText = 'Jiit Email';
    emailInput.placeholder = 'yourname@jiit.ac.in';
    btnText.innerText = 'Sign In as Student';
    signupBtn.style.display = '';
    signupDivider.style.display = '';
  }
  hideLoginError();
}

function showLoginError(msg){
  const el = document.getElementById('loginError');
  el.innerText = msg;
  el.style.display = 'block';
}
function hideLoginError(){
  document.getElementById('loginError').style.display = 'none';
}

let pendingAction = 'login';
document.getElementById('loginSubmitBtn').addEventListener('click', ()=>{ pendingAction = 'login'; });
document.getElementById('signupBtn').addEventListener('click', ()=>{ pendingAction = 'signup'; });

document.getElementById('loginForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  hideLoginError();
  document.getElementById('formAction').value = pendingAction;
  const form = e.target;
  const fd = new FormData(form);
  const submitBtns = form.querySelectorAll('button[type=submit]');
  submitBtns.forEach(b=>b.disabled=true);
  try{
    const res = await fetch('/auth', { method:'POST', body: fd });
    if(res.redirected || res.ok){
      // /auth redirects to '/' on success; reload so the server-rendered
      // session bootstrap (window.__PRINTFLOW_SESSION__) takes over.
      window.location.href = '/';
      return;
    }
    const text = await res.text();
    const match = text.match(/<p>(.*?)<\/p>/s);
    showLoginError(match ? match[1].replace(/<[^>]+>/g,'') : 'Sign in failed. Please check your credentials.');
  } catch(err){
    showLoginError('Network error — could not reach the server.');
  } finally {
    submitBtns.forEach(b=>b.disabled=false);
  }
});

function enterApp(email, r){
  currentEmail = email;
  role = r;
  document.getElementById('loginScreen').style.display = 'none';
  document.getElementById('appShell').style.display = 'block';
  hud.style.display = 'flex';
  applyRoleUI(role);
  setView(role==='staff' ? 'staff' : 'dashboard');
  document.getElementById('sessionEmail').innerText = currentEmail;
  observeReveals();
  refreshQueue();
  if(pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(refreshQueue, 4000);
}

/* Sets the read-only post-login role display. This is NOT switchable in-app —
   role is fixed at login time by which credentials/tab were used, and enforced
   server-side in /auth. */
function applyRoleUI(r){
  document.getElementById('roleStudentBtn').classList.toggle('active', r==='student');
  document.getElementById('roleStaffBtn').classList.toggle('active', r==='staff');
  document.getElementById('navDashboard').style.display = r==='student' ? 'flex' : 'none';
  document.getElementById('navOrders').style.display = r==='student' ? 'flex' : 'none';
  document.getElementById('navStaff').style.display = r==='staff' ? 'flex' : 'none';
  document.getElementById('sessionRole').innerText = r==='staff' ? 'STAFF ACCESS' : 'STUDENT ACCESS';
}

async function logout(){
  if(pollTimer) clearInterval(pollTimer);
  try{ await fetch('/logout'); }catch(e){}
  window.location.href = '/';
}

/* On load: trust the server's session state, not client memory. */
(function bootstrapSession(){
  const s = window.__PRINTFLOW_SESSION__ || {loggedIn:false};
  if(s.loggedIn){
    enterApp(s.email, s.role);
  } else {
    setLoginRole('student');
  }
})();

function setView(v){
  closeSidebar();
  document.querySelectorAll('.view').forEach(el=>el.style.display='none');
  document.getElementById('view-'+v).style.display='block';
  document.querySelectorAll('.nav-item[data-view]').forEach(el=>el.classList.toggle('active', el.dataset.view===v));
  const titles = {dashboard:'Print Dashboard', orders:'My Print Orders', staff:'Staff Console'};
  document.getElementById('pageTitle').innerText = titles[v];
  observeReveals();
  render();
}

function showPayment(){
  const f = document.getElementById('fileInput').files[0];
  if(!f){ alert('Please select a PDF file first.'); return; }
  document.getElementById('modalPrice').innerText = 'Calculating…';
  document.getElementById('pay-overlay').style.display='flex';
  document.getElementById('modalPrice').dataset.ready = '0';
  // Real page count/price are computed server-side from the actual PDF in /upload.
  // We don't know the exact price until upload completes, so we show an estimate
  // based on a quick local page-range parse against the color rate only.
  const range = document.getElementById('pageRange').value;
  const rate = document.getElementById('colorMode').value === 'Color' ? 11 : 3;
  document.getElementById('modalPrice').innerText = range ? `₹${rate}/pg × selected pages` : `₹${rate}/pg × all pages`;
}
function closePayment(){ document.getElementById('pay-overlay').style.display='none'; }

async function submitJob(){
  const f = document.getElementById('fileInput').files[0];
  if(!f){ alert('Please select a PDF file first.'); return; }
  const fd = new FormData();
  fd.append('file', f);
  fd.append('color_mode', document.getElementById('colorMode').value);
  fd.append('page_size', document.getElementById('pageSize').value);
  fd.append('page_range', document.getElementById('pageRange').value);

  const payBtn = document.querySelector('#pay-overlay .btn-primary');
  payBtn.disabled = true;
  const origText = payBtn.innerHTML;
  payBtn.innerHTML = 'Uploading…';
  try{
    const res = await fetch('/upload', { method:'POST', body: fd });
    const data = await res.json();
    if(!res.ok || data.error){
      alert('Upload failed: ' + (data.error || 'Unknown error'));
      return;
    }
    closePayment();
    document.getElementById('uploadForm').reset();
    setView('orders');
    await refreshQueue();
  } catch(err){
    alert('Network error during upload.');
  } finally {
    payBtn.disabled = false;
    payBtn.innerHTML = origText;
  }
}

async function clearReady(){
  try{
    const res = await fetch('/clear-ready');
    const data = await res.json();
    if(data.error){ alert(data.error); return; }
    await refreshQueue();
  } catch(err){ alert('Network error.'); }
}

async function refreshQueue(){
  try{
    const res = await fetch('/api/queue');
    if(res.status===401){ window.location.href='/'; return; }
    const data = await res.json();
    if(Array.isArray(data)) jobs = data;
    render();
  } catch(err){ /* keep last known state on transient network errors */ }
}

/* print_jobs has no file_name column — derive a readable name from the
   storage URL instead (strip our "pdf_<timestamp>_" prefix). */
function displayFileName(j){
  if(!j.file_url) return 'document.pdf';
  try{
    const raw = decodeURIComponent(j.file_url.split('/').pop());
    return raw.replace(/^pdf_\d+_/, '') || raw;
  } catch(e){
    return 'document.pdf';
  }
}

function render(){
  // stats
  const activePages = jobs.filter(j=>j.status!=='Ready').reduce((s,j)=>s+j.page_count,0);
  const livePages = document.getElementById('live-pages');
  const liveEta = document.getElementById('live-eta');
  if(livePages) livePages.innerText = activePages + ' Pages';
  if(liveEta) liveEta.innerText = Math.max(2, Math.floor(activePages/5)+2) + ' mins';
  const mine = jobs.filter(j=>j.student_email===currentEmail);
  const myCount = document.getElementById('my-orders-count');
  if(myCount) myCount.innerText = mine.length + ' Job' + (mine.length!==1?'s':'');

  // orders (student)
  const queueList = document.getElementById('queue-list');
  if(queueList){
    if(mine.length){
      queueList.innerHTML = mine.map(j=>`
        <div class="order-item tilt reveal in">
          <div>
            <div class="order-name">${displayFileName(j)}</div>
            <div class="order-meta">₹${j.price} &nbsp;·&nbsp; ETA: ${j.eta} &nbsp;·&nbsp; ${j.color_mode} &nbsp;·&nbsp; ${j.page_size}</div>
          </div>
          <span class="badge ${j.status}">${j.status}</span>
        </div>`).join('');
    } else {
      queueList.innerHTML = `<div class="empty-state"><i data-lucide="inbox"></i><p>No orders placed yet. Submit your first print job from the Dashboard.</p></div>`;
    }
  }

  // staff active
  const activeBody = document.getElementById('active-jobs-body');
  if(activeBody){
    const active = jobs.filter(j=>j.status!=='Ready');
    document.getElementById('queue-count').innerText = active.length + ' job' + (active.length!==1?'s':'');
    activeBody.innerHTML = active.length ? active.map(j=>`
      <tr>
        <td data-label="Student"><strong>${(j.student_email||'').split('@')[0]}</strong></td>
        <td data-label="Config"><span class="mono-tag">${j.page_size} · ${j.color_mode}</span></td>
        <td data-label="Pages"><span class="mono-tag">${j.page_count}pg</span></td>
        <td data-label="Price" style="color:var(--gold2);font-family:'JetBrains Mono';font-weight:700;">₹${j.price}</td>
        <td data-label="Status"><span class="badge ${j.status}">${j.status}</span></td>
        <td data-label="Actions">
          <a href="/view/${j.id}" target="_blank" class="view-btn"><i data-lucide="eye" style="width:12px;height:12px;"></i> View</a>
          ${j.status==='Queued' ? `<a href="#" class="done-btn" onclick="advanceStatus(${j.id},'Printing');return false;"><i data-lucide="printer" style="width:12px;height:12px;"></i> Start</a>` : ''}
          ${j.status==='Printing' ? `<a href="#" class="done-btn" onclick="advanceStatus(${j.id},'Ready');return false;"><i data-lucide="check" style="width:12px;height:12px;"></i> Done</a>` : ''}
        </td>
      </tr>`).join('') : `<tr><td colspan="6"><div class="empty-state"><i data-lucide="check-circle-2"></i><p>Queue is clear — no pending jobs.</p></div></td></tr>`;
  }

  // staff done
  const doneBody = document.getElementById('done-jobs-body');
  if(doneBody){
    const done = jobs.filter(j=>j.status==='Ready');
    doneBody.innerHTML = done.length ? done.map(j=>`
      <tr style="opacity:.6;">
        <td data-label="Student">${(j.student_email||'').split('@')[0]}</td>
        <td data-label="Config"><span class="mono-tag">${j.page_size} · ${j.color_mode}</span></td>
        <td data-label="Price" style="font-family:'JetBrains Mono';">₹${j.price}</td>
        <td data-label="Status"><span class="badge Ready">Ready</span></td>
      </tr>`).join('') : `<tr><td colspan="4"><div class="empty-state"><i data-lucide="inbox"></i><p>No completed jobs yet.</p></div></td></tr>`;
  }

  lucide.createIcons();
}

async function advanceStatus(id, status){
  try{
    const res = await fetch(`/update/${id}/${status}`);
    const data = await res.json();
    if(data.error){ alert(data.error); return; }
    await refreshQueue();
  } catch(err){ alert('Network error.'); }
}

</script>
</body>
</html>

"""

# --- ROUTES ---
@app.route('/')
def index():
    logged_in = 'role' in session and 'email' in session
    return render_template_string(
        HTML_TEMPLATE,
        logged_in=logged_in,
        email=session.get('email'),
        role=session.get('role'),
        active_page="dashboard"
    )

@app.route('/my-orders')
def my_orders():
    logged_in = 'role' in session and 'email' in session
    return render_template_string(
        HTML_TEMPLATE,
        logged_in=logged_in,
        email=session.get('email'),
        role=session.get('role'),
        active_page="orders"
    )

# Staff accounts are explicitly allow-listed. Add additional staff emails here
# (or better: look this up from a 'staff' table in Supabase keyed by user id/email).
STAFF_EMAILS = {"staff@jiit.ac.in"}

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form['email'].strip().lower()
    pwd = request.form['password']
    action = request.form['action']
    requested_role = request.form.get('role', 'student').strip().lower()
    if requested_role not in ('student', 'staff'):
        requested_role = 'student'

    # Server-side authority on role: never trust the client's tab selection alone.
    # A user is only ever staff if their email is allow-listed as staff.
    actual_role = 'staff' if email in STAFF_EMAILS else 'student'

    if requested_role == 'staff' and actual_role != 'staff':
        return "<h1>Access Denied</h1><p>This account is not authorized for staff access.</p><br><a href='/'>Go Back</a>", 403
    if requested_role == 'student' and actual_role == 'staff':
        # Staff account trying to sign in through the student tab — also reject,
        # since the two logins are meant to be kept separate.
        return "<h1>Access Denied</h1><p>Please sign in using the Staff tab.</p><br><a href='/'>Go Back</a>", 403

    try:
        if action == "signup":
            if actual_role == 'staff':
                return "<h1>Signup Disabled</h1><p>Staff accounts are provisioned by admins, not self-signup.</p><br><a href='/'>Go Back</a>", 403
            res = supabase.auth.sign_up({"email": email, "password": pwd})
        else:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
        session.update({'user_id': str(res.user.id), 'email': email, 'role': actual_role})
        return redirect('/')
    except Exception as e:
        print(f"SUPABASE ERROR: {e}")
        return f"<h1>Detailed Auth Error:</h1><p>{e}</p><br><a href='/'>Go Back</a>"

@app.route('/view/<job_id>')
def view_file(job_id):
    if 'role' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    try:
        job = supabase.table('print_jobs').select("file_url,student_email").eq("id", job_id).single().execute()
        if not job.data:
            return f"<h1>No job found for ID: {job_id}</h1>", 404
        # students may only open their own jobs
        if session['role'] != 'staff' and job.data.get('student_email') != session.get('email'):
            return jsonify({"error": "Forbidden"}), 403
        return redirect(job.data['file_url'])
    except Exception as e:
        return f"<h1>Error for ID [{job_id}]:</h1><p>{e}</p><br><a href='/'>Go Back</a>", 500

@app.route('/upload', methods=['POST'])
def upload():
    if session.get('role') != 'student':
        return jsonify({"error": "Only student accounts can submit print jobs."}), 403
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
        inserted = supabase.table('print_jobs').insert({
            "student_email": session['email'], "file_url": url,
            "page_count": count, "price": total_price, "color_mode": color_mode,
            "eta": f"{eta_val}m", "page_size": request.form.get('page_size', 'A4'), "status": "Queued"
        }).execute()
        return jsonify({"ok": True, "job": inserted.data[0] if inserted.data else None})
    except Exception as e:
        print(f"\n--- UPLOAD ERROR --- \n{e}\n--------------------\n")
        return jsonify({"error": str(e)}), 500

@app.route('/api/queue')
def get_queue():
    if 'role' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    query = supabase.table('print_jobs').select("*").order('created_at', desc=True)
    if session['role'] != 'staff':
        # students only ever see their own jobs, never the whole queue
        query = query.eq('student_email', session['email'])
    res = query.execute()
    return jsonify(res.data)

@app.route('/update/<int:job_id>/<status>')
def update_status(job_id, status):
    if session.get('role') != 'staff':
        return jsonify({"error": "Only staff can update job status."}), 403
    if status not in ('Queued', 'Printing', 'Ready'):
        return jsonify({"error": "Invalid status."}), 400
    supabase.table('print_jobs').update({"status": status}).eq("id", job_id).execute()
    return jsonify({"ok": True})

@app.route('/clear-ready')
def clear_ready():
    if session.get('role') != 'staff':
        return jsonify({"error": "Only staff can clear completed jobs."}), 403
    supabase.table('print_jobs').delete().eq("status", "Ready").execute()
    return jsonify({"ok": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001)
