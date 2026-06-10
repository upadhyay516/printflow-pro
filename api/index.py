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
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --sidebar: #0f172a; --primary: #2563eb; --accent: #f59e0b; --bg: #f8fafc; --sidebar-width: 260px; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--bg); margin: 0; display: flex; min-height: 100vh; }
        .sidebar { width: var(--sidebar-width); background: var(--sidebar); height: 100vh; color: white; padding: 2rem 1.5rem; position: fixed; left: 0; top: 0; z-index: 1000; box-sizing: border-box; }
        .logo { font-weight: 800; font-size: 1.5rem; margin-bottom: 2.5rem; display: flex; align-items: center; gap: 10px; }
        .logo span { color: var(--primary); }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px; color: #94a3b8; text-decoration: none; border-radius: 8px; transition: 0.3s; margin-bottom: 10px; }
        .nav-item:hover, .nav-item.active { background: #1e293b; color: white; }
        .main { margin-left: var(--sidebar-width); padding: 2.5rem; width: calc(100% - var(--sidebar-width)); box-sizing: border-box; min-height: 100vh; }
        .card { background: white; border-radius: 16px; border: 1px solid #e2e8f0; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 1.5rem; }
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #e2e8f0; box-sizing: border-box; font-family: inherit; }
        .btn-primary { background: var(--primary); color: white; border: none; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
        .Queued { background: #f1f5f9; color: #475569; }
        .Printing { background: #fef3c7; color: #92400e; }
        .Ready { background: #dcfce7; color: #166534; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 12px 0; color: #64748b; font-size: 0.85rem; }
        td { padding: 12px 0; border-top: 1px solid #f1f5f9; }
        #pay-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 2000; align-items: center; justify-content: center; }
        .modal { background: white; padding: 2rem; border-radius: 24px; width: 350px; text-align: center; }
    </style>
</head>
<body>
    {% if not session.get('user') %}
    <div style="width:100%; height:100vh; display:flex; align-items:center; justify-content:center; background:var(--sidebar);">
        <div class="card" style="width:380px; text-align:center; padding: 3rem;">
            <div class="logo" style="justify-content:center; color:black;">PRINT<span>FLOW</span></div>
            <form action="/auth" method="POST">
                <input type="email" name="email" placeholder="JIIT Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit" name="action" value="login" class="btn-primary">Sign In</button>
                <button type="submit" name="action" value="signup" style="background:none; border:none; color:#2563eb; cursor:pointer; font-weight:600; margin-top:10px;">Create Account</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="logo">PRINT<span>FLOW</span></div>
        <a href="/" class="nav-item active"><i data-lucide="layout-dashboard"></i> Dashboard</a>
        {% if session.get('user') != 'staff@jiit.ac.in' %}
            <a href="/" class="nav-item"><i data-lucide="printer"></i> My Orders</a>
        {% endif %}
        <a href="/logout" class="nav-item" style="position:absolute; bottom:2rem; width:210px; color: #f87171;"><i data-lucide="log-out"></i> Logout</a>
    </div>

    <div class="main">
        <div style="margin-bottom:2.5rem;">
            <h1>JIIT Smart Printing</h1>
            <p>User: <strong>{{ session['user'] }}</strong></p>
        </div>

        {% if session.get('user') != 'staff@jiit.ac.in' %}
            <div class="stats">
                <div class="card"><small style="font-weight:700; color:gray;">LIVE ACTIVE QUEUE</small><div style="font-size:1.5rem; font-weight:800;" id="live-pages">0 Pages</div></div>
                <div class="card"><small style="font-weight:700; color:gray;">EST. WAIT TIME</small><div style="font-size:1.5rem; font-weight:800; color:var(--accent);" id="live-eta">-- mins</div></div>
            </div>

            <div class="card">
                <h3><i data-lucide="upload-cloud"></i> New Print Request</h3>
                <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".pdf" required id="fileInput">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:10px;">
                        <select name="color_mode" id="colorMode"><option value="B&W">B&W (₹3/pg)</option><option value="Color">Color (₹11/pg)</option></select>
                        <select name="page_size"><option value="A4">A4</option><option value="A3">A3</option></select>
                    </div>
                    <button type="button" onclick="showPayment()" class="btn-primary" style="margin-top:1rem; padding:15px;">Review & Pay</button>
                </form>
            </div>
            
            <div class="card"><h3>Order History</h3><div id="queue-list">Syncing...</div></div>
        {% else %}
        <div class="card" style="border-left: 5px solid var(--primary);">
            <h3>Active Queue</h3>
            <table>
                <thead><tr><th>STUDENT</th><th>CONFIG</th><th>PRICE</th><th>STATUS</th><th>ACTIONS</th></tr></thead>
                <tbody>
                    {% for j in jobs if j.status != 'Ready' %}
                    <tr>
                        <td><strong>{{ j.user_email.split('@')[0] }}</strong></td>
                        <td>A4 | {{ j.color_mode }}</td>
                        <td>₹{{ j.price }}</td>
                        <td><span class="badge {{j.status}}">{{ j.status }}</span></td>
                        <td>
                            <a href="{{ j.file_url }}" target="_blank" style="display:inline-block; background:#eff6ff; color:var(--primary); padding:8px 12px; border-radius:6px; font-weight:800; text-decoration:none; text-align:center;">VIEW</a>
                            <a href="/update/{{ j.id }}/Ready" style="color:green; margin-left:10px; font-weight:700; text-decoration:none;">DONE</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="card" style="opacity: 0.8; margin-top: 2rem;">
            <h3>Staff History (Read-Only)</h3>
            <table>
                {% for j in jobs if j.status == 'Ready' %}
                <tr style="color:gray;"><td>{{ j.user_email.split('@')[0] }}</td><td>₹{{ j.price }}</td><td><span class="badge Ready">Ready</span></td></tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>

    <div id="pay-overlay">
        <div class="modal">
            <h3>Confirm Payment</h3>
            <div style="font-size:2rem; font-weight:800; color:var(--primary); margin: 1rem 0;" id="modalPrice">₹0</div>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=jiit@upi" style="margin-bottom:1rem;">
            <button onclick="document.getElementById('uploadForm').submit()" class="btn-primary">Verify & Submit</button>
            <button onclick="document.getElementById('pay-overlay').style.display='none'" style="background:none; border:none; color:red; cursor:pointer; margin-top:10px;">Cancel</button>
        </div>
    </div>

    <script>
        lucide.createIcons();
        function showPayment() {
            if(!document.getElementById('fileInput').files[0]) return alert("Select a file.");
            const rate = document.getElementById('colorMode').value === 'Color' ? 11 : 3;
            document.getElementById('modalPrice').innerText = "Rate: ₹" + rate + "/pg";
            document.getElementById('pay-overlay').style.display = 'flex';
        }
        async function sync() {
            try {
                // The API route to get data wasn't in the Python script, so we parse the UI jobs for now!
                // Realtime syncing will rely on standard page refreshes unless we add the /api/queue python route.
                location.reload();
            } catch(e) {}
        }
        // Disabled the auto-sync interval so it doesn't crash the frontend since there is no /api/queue route
        // setInterval(sync, 4000); 
    </script>
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
        
        # --- NEW DEBUG LINES ---
        print("\n--- LOGIN DEBUG INFO ---")
        print(f"Raw Email Typed: [{email}]")
        print(f"Role Assigned:   [{role}]")
        print("------------------------\n")
        
        session.update({'user_id': str(res.user.id), 'email': email, 'role': role})
        return redirect('/')
        
    except Exception as e:
        print(f"SUPABASE ERROR: {e}") 
        return f"<h1>Detailed Auth Error:</h1><p>{e}</p><br><a href='/'>Go Back</a>"

@app.route('/view/<int:job_id>')
def view_file(job_id):
    job = supabase.table('print_jobs').select("file_url").eq("id", job_id).single().execute()
    response = requests.get(job.data['file_url'], stream=True)
    return Response(response.iter_content(chunk_size=1024), mimetype='application/pdf', headers={"Content-Disposition": "inline"})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        color_mode = request.form.get('color_mode', 'B/W')
        t_stamp = int(time.time())
        
        # WINDOWS FIX: Use a dynamic temp folder instead of hardcoded Linux "/tmp"
        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, f"{t_stamp}.pdf")
        file.save(local_path)
        
        count, final_path = process_pdf_and_count(local_path, local_path, "")
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

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001)
