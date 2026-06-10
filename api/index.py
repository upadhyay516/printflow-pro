from flask import Flask, request, render_template_string, redirect, session, jsonify
from supabase import create_client, Client
import os
import tempfile
import uuid
import PyPDF2

app = Flask(__name__)
app.secret_key = "printflow_cyber_key"

# ==========================================
# ⚠️ PASTE YOUR SUPABASE KEY HERE
# ==========================================
SUPABASE_URL = "https://qsfwlyucognzoojijgul.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzZndseXVjb2duem9vamlqZ3VsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwNjUwNjgsImV4cCI6MjA5NjY0MTA2OH0.WeipU_k1_Rm6M97gC7LMsjbFspjVRDiPOnAHreeNATc" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrintFlow Pro | Network</title>
    <link rel="icon" type="image/png" href="https://qsfwlyucognzoojijgul.supabase.co/storage/v1/object/public/assets/PF_Logo.png">
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #050507;
            --panel-bg: rgba(20, 20, 25, 0.6);
            --panel-border: rgba(255, 255, 255, 0.08);
            --neon-cyan: #00f3ff;
            --neon-purple: #bc13fe;
            --text-main: #ffffff;
            --text-muted: #8a8d98;
            --danger: #ff2a6d;
            --success: #05d59e;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(0, 243, 255, 0.05), transparent 30%),
                radial-gradient(circle at 85% 20%, rgba(188, 19, 254, 0.05), transparent 30%),
                linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
        }

        h1, h2, h3, .brand { font-family: 'Rajdhani', sans-serif; text-transform: uppercase; letter-spacing: 1px; }

        .container { max-width: 1000px; margin: 0 auto; padding: 40px 20px; }

        nav {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 20px; border-bottom: 1px solid var(--panel-border);
            margin-bottom: 40px;
        }

        .brand {
            font-size: 28px; font-weight: 700;
            background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
        }

        /* Glassmorphism Panels */
        .glass-panel {
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .glass-panel:hover {
            border-color: rgba(0, 243, 255, 0.3);
            box-shadow: 0 10px 40px rgba(0, 243, 255, 0.1);
            transform: translateY(-4px);
        }

        /* Inputs & Selects */
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; margin-bottom: 8px; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 1px;}
        
        input[type="email"], input[type="password"], input[type="file"], select {
            width: 100%; padding: 12px 15px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--panel-border);
            border-radius: 8px; color: var(--text-main);
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }

        input:focus, select:focus {
            outline: none; border-color: var(--neon-purple);
            box-shadow: 0 0 15px rgba(188, 19, 254, 0.2);
            background: rgba(0, 0, 0, 0.6);
        }

        /* Neon Buttons */
        .neon-btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            width: 100%; padding: 14px;
            background: transparent; color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan); border-radius: 8px;
            font-family: 'Rajdhani', sans-serif; font-size: 18px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 2px;
            cursor: pointer; overflow: hidden; position: relative;
            transition: all 0.3s ease; text-decoration: none;
        }

        .neon-btn::before {
            content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.4), transparent);
            transition: all 0.4s ease;
        }

        .neon-btn:hover {
            background: var(--neon-cyan); color: #000;
            box-shadow: 0 0 15px var(--neon-cyan), 0 0 30px rgba(0, 243, 255, 0.4);
        }

        .neon-btn:hover::before { left: 100%; }

        .neon-btn.secondary {
            border-color: var(--neon-purple); color: var(--neon-purple);
        }
        .neon-btn.secondary:hover {
            background: var(--neon-purple); color: #fff;
            box-shadow: 0 0 15px var(--neon-purple);
        }

        /* Queue Grid */
        .queue-grid { display: grid; gap: 15px; margin-top: 20px; }
        .queue-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3); border: 1px solid var(--panel-border);
            border-radius: 12px; transition: all 0.3s ease;
            border-left: 4px solid var(--text-muted);
        }
        .queue-item:hover { background: rgba(255,255,255,0.02); transform: scale(1.01); }
        
        .status-ready { border-left-color: var(--success); }
        .status-printing { border-left-color: var(--neon-cyan); }
        .status-queued { border-left-color: var(--neon-purple); }

        .badge {
            padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase;
        }
        .badge.ready { background: rgba(5, 213, 158, 0.1); color: var(--success); border: 1px solid var(--success); }
        .badge.queued { background: rgba(188, 19, 254, 0.1); color: var(--neon-purple); border: 1px solid var(--neon-purple); }

        .dashboard-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 30px; }
        @media (max-width: 768px) { .dashboard-grid { grid-template-columns: 1fr; } }
        
        .file-upload-wrapper {
            position: relative; border: 2px dashed var(--panel-border);
            border-radius: 12px; padding: 40px 20px; text-align: center;
            transition: all 0.3s;
        }
        .file-upload-wrapper:hover { border-color: var(--neon-cyan); background: rgba(0,243,255,0.02); }
        .file-upload-wrapper input[type="file"] {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0; cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <div class="brand"><i data-lucide="cpu"></i> PRINTFLOW_PRO</div>
            {% if session.get('user') %}
                <a href="/logout" class="neon-btn secondary" style="width: auto; font-size: 14px; padding: 8px 16px;">System Logout</a>
            {% endif %}
        </nav>

        {% if error %}
            <div class="glass-panel" style="border-color: var(--danger); margin-bottom: 20px;">
                <p style="color: var(--danger);"><i data-lucide="alert-triangle"></i> {{ error }}</p>
            </div>
        {% endif %}

        {% if not session.get('user') %}
            <div class="glass-panel" style="max-width: 400px; margin: 0 auto; text-align: center;">
                <h2 style="margin-bottom: 20px; color: var(--neon-cyan);">Access Terminal</h2>
                <form action="/auth" method="POST">
                    <div class="input-group">
                        <input type="email" name="email" placeholder="JIIT Email Address" required>
                    </div>
                    <div class="input-group">
                        <input type="password" name="password" placeholder="Passcode" required>
                    </div>
                    <button type="submit" name="action" value="login" class="neon-btn">Initialize Login</button>
                    <p style="margin-top: 15px; color: var(--text-muted); font-size: 14px;">Unregistered? <button type="submit" name="action" value="signup" style="background:none; border:none; color: var(--neon-purple); cursor:pointer; font-weight:bold;">Create Link</button></p>
                </form>
            </div>

        {% elif session.get('user') == 'staff@jiit.ac.in' %}
            <div class="glass-panel">
                <h2 style="color: var(--neon-purple); margin-bottom: 20px;"><i data-lucide="terminal"></i> Master Command Override</h2>
                <div class="queue-grid">
                    {% for job in jobs %}
                    <div class="queue-item {% if job.status == 'Ready' %}status-ready{% else %}status-queued{% endif %}">
                        <div>
                            <h3 style="color: var(--text-main);">{{ job.user_email }}</h3>
                            <p style="color: var(--text-muted); font-size: 14px; margin-top: 5px;">{{ job.pages }} Pages | {{ job.color_mode }} | ₹{{ job.price }}</p>
                        </div>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span class="badge {% if job.status == 'Ready' %}ready{% else %}queued{% endif %}">{{ job.status }}</span>
                            <a href="{{ job.file_url }}" target="_blank" class="neon-btn secondary" style="padding: 6px 12px; font-size: 12px; width: auto;">Decrypt File</a>
                            {% if job.status != 'Ready' %}
                                <a href="/update/{{ job.id }}/Ready" class="neon-btn" style="padding: 6px 12px; font-size: 12px; width: auto;">Mark Done</a>
                            {% endif %}
                        </div>
                    </div>
                    {% else %}
                        <p style="color: var(--text-muted);">No active network packets found.</p>
                    {% endfor %}
                </div>
            </div>

        {% else %}
            <div class="dashboard-grid">
                <div class="glass-panel">
                    <h2 style="color: var(--neon-cyan); margin-bottom: 20px;"><i data-lucide="upload-cloud"></i> Transmit Data</h2>
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <div class="file-upload-wrapper input-group">
                            <i data-lucide="file-text" style="color: var(--neon-cyan); width: 40px; height: 40px; margin-bottom: 10px;"></i>
                            <p style="color: var(--text-muted);">Drag payload or click to browse</p>
                            <input type="file" name="file" accept=".pdf" required>
                        </div>
                        <div class="input-group">
                            <label>Render Mode</label>
                            <select name="color_mode">
                                <option value="B&W">Monochrome (₹3/pg)</option>
                                <option value="Color">RGB Color (₹11/pg)</option>
                            </select>
                        </div>
                        <button type="submit" class="neon-btn"><i data-lucide="zap"></i> Execute Print Job</button>
                    </form>
                </div>

                <div class="glass-panel">
                    <h2 style="color: var(--neon-purple); margin-bottom: 20px;"><i data-lucide="activity"></i> Network Queue Status</h2>
                    <div class="queue-grid">
                        {% for job in jobs %}
                        <div class="queue-item {% if job.status == 'Ready' %}status-ready{% else %}status-queued{% endif %}">
                            <div>
                                <h3 style="font-size: 16px;">{{ job.file_url.split('/')[-1] | truncate(25) }}</h3>
                                <p style="color: var(--text-muted); font-size: 13px; margin-top: 5px;">{{ job.pages }}pgs | ₹{{ job.price }}</p>
                            </div>
                            <span class="badge {% if job.status == 'Ready' %}ready{% else %}queued{% endif %}">{{ job.status }}</span>
                        </div>
                        {% else %}
                            <p style="color: var(--text-muted);">Your transmission log is empty.</p>
                        {% endfor %}
                    </div>
                </div>
            </div>
        {% endif %}
    </div>
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    user = session.get('user')
    jobs = []
    
    if user:
        try:
            if user == 'staff@jiit.ac.in':
                response = supabase.table('print_jobs').select("*").order('created_at', desc=True).execute()
            else:
                response = supabase.table('print_jobs').select("*").eq('user_email', user).order('created_at', desc=True).execute()
            jobs = response.data
        except Exception as e:
            print("DB Fetch Error:", e)

    return render_template_string(HTML_TEMPLATE, jobs=jobs)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form['email']
    password = request.form['password']
    action = request.form['action']

    try:
        if action == 'signup':
            supabase.auth.sign_up({"email": email, "password": password})
            return render_template_string(HTML_TEMPLATE, error="Registration sequence complete. Check email for verification.")
        else:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user'] = res.user.email
            return redirect(url_for('home'))
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=str(e))

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('home'))

    file = request.files['file']
    color_mode = request.form['color_mode']
    
    if file.filename == '':
        return redirect(url_for('home'))

    if file:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        # Count Pages
        try:
            with open(temp_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
        except:
            num_pages = 1 

        # Calculate Price
        rate = 11 if color_mode == 'Color' else 3
        price = num_pages * rate

        # Upload to Supabase Storage
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        with open(temp_path, 'rb') as f:
            supabase.storage.from_("print-files").upload(file=f, path=unique_filename, file_options={"content-type": "application/pdf"})
        
        file_url = f"{SUPABASE_URL}/storage/v1/object/public/print-files/{unique_filename}"

        # Save to Database
        supabase.table('print_jobs').insert({
            "user_email": session['user'],
            "file_url": file_url,
            "pages": num_pages,
            "color_mode": color_mode,
            "price": price,
            "status": "Queued"
        }).execute()

        os.remove(temp_path)
        return redirect(url_for('home'))

@app.route('/update/<id>/<status>')
def update_status(id, status):
    if session.get('user') == 'staff@jiit.ac.in':
        supabase.table('print_jobs').update({"status": status}).eq("id", id).execute()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
