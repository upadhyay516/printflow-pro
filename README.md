# 🖨️ PrintFlow Pro | JIIT Smart Printing Portal

PrintFlow Pro is a full-stack, real-time print queue management web application tailored for the Jaypee Institute of Information Technology (JIIT). It acts as a digital bridge between students and the campus print shop.

Built as a single-file Python Flask application, it handles secure authentication, automated PDF parsing, dynamic cost calculation, real-time queue syncing, and cloud file streaming — all powered by a Supabase backend.

---

## 📑 Table of Contents
- [Core Features](#-core-features)
- [Technology Stack](#-technology-stack)
- [How It Works](#-how-it-works-application-logic)
- [API Routes & Endpoints](#-api-routes--endpoints)
- [Local Setup & Installation](#-local-setup--installation)
- [Environment Variables](#-environment-variables)
- [Usage & Testing](#-usage--testing)

---

## ✨ Core Features

### 👨‍🎓 Student Portal
- **Automated PDF Parsing:** Upload any `.pdf` and `PyPDF2` automatically counts the exact page count — supports full-document or custom page ranges (e.g. `1-3, 5, 7-9`).
- **Dynamic Pricing Engine:** Cost is calculated server-side per page:
  - **Black & White:** ₹3 per page
  - **Color:** ₹11 per page
- **Mock UPI Payment Overlay:** A built-in modal displays a UPI QR code before final submission to simulate a payment confirmation step.
- **Live Dashboard:** A JavaScript polling loop hits `/api/queue` every 4 seconds to show live job status (`Queued`, `Printing`, `Ready`) without any page reloads.
- **Smart ETA Calculation:** The server totals all non-`Ready` pages in the queue and estimates wait time as: `max(2, floor(active_pages / 5) + 2)` minutes.
- **Order History Page:** `/my-orders` shows all past and active jobs for the logged-in student.

### 👨‍💼 Staff (Admin) Portal
- **Role-Based Access:** Logging in with `staff@jiit.ac.in` auto-assigns the `staff` role and redirects to the Admin Dashboard.
- **Master Queue View:** Displays all incoming jobs — student name, page config, price, and current status.
- **Cloud PDF Streaming:** The "VIEW" button streams the PDF directly from the Supabase Storage bucket to the browser inline, without local downloads.
- **One-Click Fulfillment:** Clicking "DONE" changes a job's status to `Ready`, instantly reflecting on the student's live dashboard and moving the job to the read-only history section.

---

## 🛠️ Technology Stack

### Backend
- **[Python 3](https://www.python.org/)** — Core runtime.
- **[Flask](https://flask.palletsprojects.com/)** — Lightweight WSGI framework for routing, sessions, and Jinja2 templating.
- **[PyPDF2](https://pypdf2.readthedocs.io/)** — PDF inspection: page counting and selective page extraction.
- **[Requests](https://requests.readthedocs.io/)** — HTTP streaming for serving Supabase-hosted PDFs to the browser.
- **[Tempfile](https://docs.python.org/3/library/tempfile.html)** — Cross-platform temp directory (`tempfile.gettempdir()`) used for intermediate PDF storage during upload processing.

### Frontend
- **HTML5 + Jinja2** — Server-side rendering; session data and DB rows injected directly into HTML.
- **CSS3** — Custom responsive layout using CSS variables, Flexbox, and CSS Grid. No external CSS frameworks.
- **Vanilla JavaScript** — Asynchronous `fetch()` polling loop for live queue updates.
- **[Lucide Icons](https://lucide.dev/)** — Open-source vector icon set loaded via CDN (`unpkg`).
- **[Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans)** — Google Fonts typeface.

### Database & Storage
- **[Supabase](https://supabase.com/)** — Full backend-as-a-service:
  - **Supabase Auth** — User registration and JWT-based login (`sign_up` / `sign_in_with_password`).
  - **PostgreSQL** — Stores the `print_jobs` table with columns: `student_email`, `file_url`, `page_count`, `price`, `color_mode`, `page_size`, `eta`, `status`, `created_at`.
  - **Supabase Storage** — Hosts uploaded PDFs in the `print-files` bucket, named as `pdf_{timestamp}_{filename}`.

---

## 🧠 How It Works (Application Logic)

1. **Auth Phase:** User signs up or logs in via Supabase Auth. Email `staff@jiit.ac.in` gets the `staff` role; all others get `student`. Role and email are stored in the Flask session.
2. **Upload Phase:** Student selects a PDF, picks color mode and page size, and confirms a mock UPI payment in the overlay modal. The form POSTs to `/upload`.
3. **Processing Phase:** Flask saves the PDF to a system temp directory. `PyPDF2` counts the pages (or extracts a custom range). Price is computed: `page_count × (11 if Color else 3)`.
4. **ETA Phase:** The server queries Supabase for all jobs where `status != 'Ready'`, sums their `page_count`, and calculates an estimated wait time.
5. **Storage Phase:** The processed file is uploaded to Supabase Storage as `pdf_{timestamp}_{original_filename}`. A public URL is retrieved.
6. **DB Phase:** A new row is inserted into `print_jobs` with all metadata and `status: "Queued"`.
7. **Sync Phase:** The student's browser polls `/api/queue` every 4 seconds. When staff marks a job "DONE", the status updates to `Ready` in the DB, which the student's UI reflects on the next poll cycle.

---

## 📍 API Routes & Endpoints

| Route | Method | Role | Purpose |
|---|---|---|---|
| `/` | `GET` | All | Login screen (unauthenticated) or Dashboard (authenticated). Staff see the active queue; students see the upload form. |
| `/my-orders` | `GET` | Student | Student's personal order history with live status updates. |
| `/auth` | `POST` | All | Handles `login` and `signup` via Supabase Auth. Sets `user_id`, `email`, and `role` in session. |
| `/upload` | `POST` | Student | Receives PDF upload, runs page count, calculates price, uploads to Supabase Storage, inserts DB record. |
| `/api/queue` | `GET` | All | Returns the full `print_jobs` table as JSON. Consumed by the frontend polling loop. |
| `/view/<job_id>` | `GET` | Staff | Looks up the file URL for the given job ID and streams the PDF inline to the browser. |
| `/update/<job_id>/<status>` | `GET` | Staff | Updates the `status` field of a job in Supabase (e.g., to `Ready`). |
| `/logout` | `GET` | All | Clears the Flask session and redirects to `/`. |

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
Python 3.8+ is required.
```bash
python --version
```

### 2. Create Project Directory
```bash
mkdir printflow-pro
cd printflow-pro
# Place app.py inside this folder
```

### 3. Install Dependencies
```bash
pip install flask supabase PyPDF2 requests
```

### 4. Configure Environment Variables (Optional)
The app has Supabase credentials hardcoded as fallback defaults, but it's recommended to use environment variables in production:

```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_KEY="your-anon-public-key"
```

### 5. Run the Server
```bash
python app.py
```
The server starts on port `5001` with debug mode enabled.

### 6. Open in Browser
```
[http://127.0.0.1:5001]
(https://printflow-pro-jet.vercel.app/)
```

---

## 🔐 Environment Variables

| Variable | Description | Default (Fallback) |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | Hardcoded project URL in `app.py` |
| `SUPABASE_KEY` | Your Supabase `anon` public API key | Hardcoded key in `app.py` |

> ⚠️ For any production or public deployment, remove the hardcoded credentials and use environment variables or a `.env` file with `python-dotenv`.

---

## 🧪 Usage & Testing

### Student Account
1. Go to `(https://printflow-pro-jet.vercel.app/)` and create a new account with any email (e.g. `student@jiit.ac.in`).
2. Upload a PDF, select color mode and page size, and confirm via the payment overlay.
3. Watch the live queue update on the `/my-orders` page.

### Staff Account
1. Log in with email `staff@jiit.ac.in` and any password (must be registered in Supabase first).
2. View all incoming jobs in the Active Queue table.
3. Click **VIEW** to open the PDF in the browser, then **DONE** to mark it as Ready.

### Supabase Table Schema (`print_jobs`)
```sql
create table print_jobs (
  id bigint generated always as identity primary key,
  student_email text,
  file_url text,
  page_count int,
  price int,
  color_mode text,
  page_size text,
  eta text,
  status text default 'Queued',
  created_at timestamptz default now()
);
```

### Supabase Storage
Create a public bucket named `print-files` in your Supabase project under **Storage**.
