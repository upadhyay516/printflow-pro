from flask import Flask, request, render_template_string, redirect, session, jsonify, url_for
from supabase import create_client, Client
import os
import tempfile
import uuid
import PyPDF2

app = Flask(__name__)
app.secret_key = "printflow_pro_key"

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
    <title>PrintFlow Pro | JIIT Portal</title>
    
    <link rel="icon" type="image/png" href="https://qsfwlyucognzoojijgul.supabase.co/storage/v1/object/public/assets/PF_Logo.png">
    
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --bg-color: #f8fafc;
            --surface: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --radius: 12px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            line-height: 1.5;
            min-height: 100vh;
        }

        .container { max-width: 1000px; margin: 0 auto; padding: 40px 20px; }

        nav {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 20px; border-bottom: 1px solid var(--border);
            margin-bottom: 40px;
        }

        .brand {
            font-size: 24px; font-weight: 700; color: var(--primary);
            display: flex; align-items: center; gap: 8px;
        }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 30px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .input-group { margin-bottom: 20px; }
        .input-group label { 
            display: block; margin-bottom: 8px; color: var(--text-main); 
            font-weight: 600; font-size: 14px;
        }
        
        input[type="email"], input[type="password"], select {
            width: 100%; padding: 12px 15px;
            border: 1px solid var(--border);
            border-radius: 8px; color: var(--text-main);
            font-family: inherit; font-size: 15px;
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            outline: none; border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            width: 100%; padding: 12px 20px;
            background: var(--primary); color: white;
            border: none; border-radius: 8px;
            font-family: inherit; font-size: 16px; font-weight: 600;
            cursor: pointer; transition: background 0.2s;
            text-decoration: none;
        }

        .btn:hover { background: var(--primary-hover); }

        .btn-outline {
            background: transparent; color: var(--text-main);
            border: 1px solid var(--border);
        }
        .btn-outline:hover { background: var(--bg-color); }

        .queue-grid { display: grid; gap: 15px; margin-top: 20px; }
        .queue-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 20px;
            background: var(--bg-color); border: 1px solid var(--border);
            border-radius: 8px;
        }
        
        .badge {
            padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;
        }
        .badge.ready { background: #d1fae5; color: #065f46; }
        .badge.queued { background: #fef3c7; color: #92400e; }

        .dashboard-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 30px; }
        @media (max-width: 768px) { .dashboard-grid { grid-template-columns: 1fr; } }
        
        .file-upload-wrapper {
            position: relative; border: 2px dashed var(--border);
            border-radius: 8px; padding: 40px 20px; text-align: center;
            background: var(--bg-color); transition: all 0.2s;
        }
        .file-upload-wrapper:hover { border-color: var(--primary); }
        .file-upload-wrapper input[type="file"] {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0; cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <div class="brand"><i data-lucide="printer"></i> PrintFlow Pro</div>
            {% if session.get('user') %}
                <a href="{{ url_for('logout') }}" class="btn btn-outline" style="width: auto; padding: 8px 16px; font-size: 14px;">Logout</a>
            {% endif %}
        </nav>

        {% if error %}
            <div class="card" style="border-color: var(--danger); background: #fef2f2; margin-bottom: 20px;">
                <p style="color: var(--danger); font-weight: 500;"><i data-lucide="alert-circle" style="vertical-align: middle;"></i> {{ error }}</p>
            </div>
        {% endif %}

        {% if not session.get('user') %}
            <div class="card" style="max-width: 400px; margin: 0 auto;">
                <h2 style="margin-bottom: 24px; text-align: center;">Welcome Back</h2>
                <form action="/auth" method="POST">
                    <div class="input-group">
                        <label>Email Address</label>
                        <input type="email" name="email" placeholder="student@jiit.ac.in" required>
                    </div>
                    <div class="input-group">
                        <label>Password</label>
                        <input type="password" name="password" placeholder="••••••••" required>
                    </div>
                    <button type="submit" name="action" value="login" class="btn">Sign In</button>
                    <p style="margin-top: 16px; text-align: center; color: var(--text-muted); font-size: 14px;">
                        Need an account? <button type="submit" name="action" value="signup" style="background:none; border:none; color: var(--primary); cursor:pointer; font-weight:600; font-family: inherit;">Sign Up</button>
                    </p>
                </form>
            </div>

        {% elif session.get('user') == 'staff@jiit.ac.in' %}
            <div class="card">
                <h2 style="margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                    <i data-lucide="layout-dashboard"></i> Staff Dashboard
                </h2>
                <div class="queue-grid">
                    {% for job in jobs %}
                    <div class="queue-item" style="{% if job.status == 'Ready' %}border-left: 4px solid var(--success);{% else %}border-left: 4px solid var(--warning);{% endif %}">
                        <div>
                            <h3 style="font-size: 16px; color: var(--text-main);">{{ job.user_email }}</h3>
                            <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">{{ job.pages }} Pages • {{ job.color_mode }} • ₹{{ job.price }}</p>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <span class="badge {% if job.status == 'Ready' %}ready{% else %}queued{% endif %}">{{ job.status }}</span>
                            <a href="{{ job.file_url }}" target="_blank" class="btn btn-outline" style="padding: 6px 12px; font-size: 13px; width: auto;">View PDF</a>
                            {% if job.status != 'Ready' %}
                                <a href="/update/{{ job.id }}/Ready" class="btn" style="padding: 6px 12px; font-size: 13px; width: auto; background: var(--success);">Mark Done</a>
                            {% endif %}
                        </div>
                    </div>
                    {% else %}
                        <p style="color: var(--text-muted); text-align: center; padding: 20px;">No pending print jobs in the queue.</p>
                    {% endfor %}
                </div>
            </div>

        {% else %}
            <div class="dashboard-grid">
                <div class="card">
                    <h2 style="margin-bottom: 20px; font-size: 18px;">New Print Job</h2>
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <div class="file-upload-wrapper input-group">
                            <i data-lucide="file-up" style="color: var(--primary); width: 32px; height: 32px; margin-bottom: 12px;"></i>
                            <p style="color: var(--text-main); font-weight: 500;">Click to upload or drag and drop</p>
                            <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">PDF files only</p>
                            <input type="file" name="file" accept=".pdf" required>
                        </div>
                        <div class="input-group">
                            <label>Print Configuration</label>
                            <select name="color_mode">
                                <option value="B&W">Black & White (₹3/page)</option>
                                <option value="Color">Color (₹11/page)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn"><i data-lucide="printer"></i> Submit Document</button>
                    </form>
                </div>

                <div class="card">
                    <h2 style="margin-bottom: 20px; font-size: 18px;">My Orders</h2>
                    <div class="queue-grid">
                        {% for job in jobs %}
                        <div class="queue-item">
                            <div>
                                <h3 style="font-size: 15px; color: var(--text-main);">{{ job.file_url.split('/')[-1] | truncate(30) }}</h3>
                                <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">{{ job.pages }} Pages • ₹{{ job.price }}</p>
                            </div>
                            <span class="badge {% if job.status == 'Ready' %}ready{% else %}queued{% endif %}">{{ job.status }}</span>
                        </div>
                        {% else %}
                            <p style="color: var(--text-muted); text-align: center; padding: 20px;">You haven't submitted any files yet.</p>
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
            return render_template_string(HTML_TEMPLATE, error="Account created successfully. Please check your email to verify.")
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
