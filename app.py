from flask import Flask, request, redirect, session, render_template_string
import sqlite3, pickle, datetime, os

app = Flask(__name__)
app.secret_key = "ai_healthcare_secret"

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "health.db")

# ---------------- MODEL ----------------
model = pickle.load(open("model/disease_model.pkl", "rb"))

SYMPTOMS = ["fever", "cough", "headache", "fatigue", "nausea"]

# ---------------- REMEDIES ----------------
REMEDIES = {
    "Flu": {
        "remedies": ["Warm fluids", "Steam inhalation", "Rest", "Paracetamol"],
        "care": ["Avoid cold food", "Consult doctor if fever > 3 days"]
    },
    "Cold": {
        "remedies": ["Gargling", "Honey + ginger", "Steam"],
        "care": ["Avoid dust", "Wear warm clothes"]
    },
    "Migraine": {
        "remedies": ["Dark room rest", "Hydration", "Cold compress"],
        "care": ["Avoid screens", "Reduce stress"]
    }
}

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            symptoms TEXT,
            disease TEXT,
            confidence INTEGER,
            risk TEXT
        )
    """)
    con.commit()
    con.close()

init_db()

# ---------------- NLP ----------------
def nlp_symptoms(text):
    text = text.lower()
    return [1 if s in text else 0 for s in SYMPTOMS]

# ---------------- BASE UI ----------------
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Healthcare App</title>
<style>
body { font-family: Arial; background:#eef2f7; margin:0; }
.header { background:#0d6efd; color:white; padding:15px; text-align:center; font-size:18px; }
.card {
    background:white;
    margin:15px;
    padding:20px;
    border-radius:15px;
    box-shadow:0 5px 15px #ccc;
}
input { width:100%; padding:10px; margin:8px 0; }
button {
    background:#0d6efd; color:white; border:none;
    padding:12px; width:100%;
    border-radius:10px; font-size:16px;
}
.nav {
    position:fixed; bottom:0; width:100%;
    background:white; display:flex;
    justify-content:space-around;
    box-shadow:0 -2px 10px #ccc;
}
.nav a {
    padding:12px; text-decoration:none;
    color:#0d6efd; font-weight:bold;
}
</style>
</head>
<body>
<div class="header">AI Healthcare App</div>
{{ content | safe }}
</body>
</html>
"""

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = get_db()
        user = con.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        ).fetchone()
        con.close()
        if user:
            session["user"] = user[0]
            return redirect("/dashboard")

    return render_template_string(BASE_HTML, content="""
    <div class="card">
        <h3>Login</h3>
        <form method="post">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button>Login</button>
        </form>
        <p><a href="/signup">Create account</a></p>
    </div>
    """)

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        con = get_db()
        try:
            con.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (request.form["username"], request.form["password"])
            )
            con.commit()
        except:
            pass
        con.close()
        return redirect("/")
    return render_template_string(BASE_HTML, content="""
    <div class="card">
        <h3>Sign Up</h3>
        <form method="post">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button>Create</button>
        </form>
    </div>
    """)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    checkboxes = "".join(
        [f"<label><input type='checkbox' name='{s}'> {s.capitalize()}</label><br>" for s in SYMPTOMS]
    )
    return render_template_string(BASE_HTML, content=f"""
    <div class="card">
        <h3>Health Analysis</h3>
        <form method="post" action="/analyze">
            <input name="text" placeholder="I have fever and headache">
            {checkboxes}
            <br><button>Analyze</button>
        </form>
    </div>

    <div class="nav">
        <a href="/dashboard">Home</a>
        <a href="/history">History</a>
        <a href="/logout">Logout</a>
    </div>
    """)

# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/")

    text = request.form.get("text","")
    nlp_data = nlp_symptoms(text)
    checkbox_data = [1 if s in request.form else 0 for s in SYMPTOMS]

    symptoms_data = [
        1 if (nlp_data[i] or checkbox_data[i]) else 0
        for i in range(len(SYMPTOMS))
    ]

    disease = model.predict([symptoms_data])[0]
    confidence = int(max(model.predict_proba([symptoms_data])[0]) * 100)

    if confidence > 70:
        risk, color = "High", "#dc3545"
    elif confidence > 40:
        risk, color = "Medium", "#ffc107"
    else:
        risk, color = "Low", "#28a745"

    session["result"] = {
        "disease": disease,
        "confidence": confidence,
        "risk": risk,
        "color": color,
        "remedies": REMEDIES.get(disease, {}).get("remedies", []),
        "care": REMEDIES.get(disease, {}).get("care", []),
        "chart": symptoms_data
    }

    con = get_db()
    con.execute(
        "INSERT INTO history VALUES(NULL,?,?,?,?,?,?)",
        (session["user"], str(datetime.date.today()),
         str(symptoms_data), disease, confidence, risk)
    )
    con.commit()
    con.close()

    return redirect("/result")

# ---------------- RESULT DASHBOARD ----------------
@app.route("/result")
def result():
    if "user" not in session or "result" not in session:
        return redirect("/dashboard")

    r = session["result"]

    return render_template_string(
        BASE_HTML + """
        <div class="card" style="border-left:8px solid {{ color }}">
            <h2>Diagnosis Result</h2>
            <h3>Disease: {{ disease }}</h3>
            <p><b>Confidence:</b> {{ confidence }}%</p>
            <p><b>Risk Level:</b> {{ risk }}</p>

            <h4>🩺 Remedies</h4>
            <ul>{% for x in remedies %}<li>{{ x }}</li>{% endfor %}</ul>

            <h4>⚠️ Care Instructions</h4>
            <ul>{% for x in care %}<li>{{ x }}</li>{% endfor %}</ul>

            <div style="width:180px;height:180px;margin:auto;">
                <canvas id="chart"></canvas>
            </div>
        </div>

        <div class="nav">
            <a href="/dashboard">New</a>
            <a href="/history">History</a>
            <a href="/logout">Logout</a>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        new Chart(document.getElementById("chart"), {
            type: "doughnut",
            data: {
                labels: {{ symptoms | tojson }},
                datasets: [{
                    data: {{ chart | tojson }},
                    backgroundColor: ["#0d6efd","#dc3545","#ffc107","#28a745","#6f42c1"]
                }]
            },
            options: {
                cutout: "65%",
                plugins: { legend: { position: "bottom" } }
            }
        });
        </script>
        """,
        disease=r["disease"],
        confidence=r["confidence"],
        risk=r["risk"],
        color=r["color"],
        remedies=r["remedies"],
        care=r["care"],
        chart=r["chart"],
        symptoms=SYMPTOMS
    )

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")
    con = get_db()
    rows = con.execute(
        "SELECT date,disease,confidence,risk FROM history WHERE user_id=? ORDER BY id DESC",
        (session["user"],)
    ).fetchall()
    con.close()
    items = "".join([f"<li>{r[0]} | {r[1]} | {r[2]}% | {r[3]}</li>" for r in rows])
    return render_template_string(BASE_HTML, content=f"""
    <div class="card">
        <h3>Health History</h3>
        <ul>{items}</ul>
    </div>
    <div class="nav">
        <a href="/dashboard">Home</a>
        <a href="/logout">Logout</a>
    </div>
    """)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
