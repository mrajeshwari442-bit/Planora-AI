from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# =========================================================
# GEMINI
# =========================================================

from google import genai


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "planora-ai-secret-key"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_FILE = "database.json"


# =========================================================
# GEMINI AI
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None

if GEMINI_API_KEY:

    try:

        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("✅ Gemini AI connected successfully")

    except Exception as error:

        print("❌ Gemini connection error:")
        print(error)

else:

    print("⚠️ GEMINI_API_KEY not found")


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def load_database():

    if not os.path.exists(DATABASE_FILE):

        data = {
            "users": {},
            "plans": []
        }

        save_database(data)

        return data

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        data.setdefault(
            "users",
            {}
        )

        data.setdefault(
            "plans",
            []
        )

        return data

    except (
        json.JSONDecodeError,
        OSError
    ):

        return {
            "users": {},
            "plans": []
        }


def save_database(data):

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if "user" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(
                "login.html",
                error="Please enter email and password."
            )

        data = load_database()

        user = data["users"].get(
            email
        )

        if not user:

            return render_template(
                "login.html",
                error="Account not found. Please create an account."
            )

        try:

            password_correct = check_password_hash(
                user["password"],
                password
            )

        except Exception:

            password_correct = False

        if not password_correct:

            return render_template(
                "login.html",
                error="Incorrect password."
            )

        session["user"] = email

        session["username"] = user.get(
            "username",
            "Student"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route(
    "/signup",
    methods=["POST"]
)
def signup():

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill all fields."
        }), 400

    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    data = load_database()

    if email in data["users"]:

        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    data["users"][email] = {

        "username": username,

        "email": email,

        "password": generate_password_hash(
            password
        ),

        "created_at": datetime.now().isoformat()

    }

    save_database(
        data
    )

    session["user"] = email

    session["username"] = username

    return jsonify({

        "success": True,

        "message": "Account created successfully!"

    })


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(

        "index.html",

        username=session.get(
            "username",
            "Student"
        ),

        email=session.get(
            "user",
            ""
        )

    )


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/user")
def current_user():

    if "user" not in session:

        return jsonify({
            "success": False
        }), 401

    return jsonify({

        "success": True,

        "username": session.get(
            "username"
        ),

        "email": session.get(
            "user"
        )

    })


# =========================================================
# SAVE STUDY PLAN
# =========================================================

@app.route(
    "/api/save-plan",
    methods=["POST"]
)
def save_plan():

    if "user" not in session:

        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401

    plan = request.get_json(
        silent=True
    )

    if not plan:

        return jsonify({

            "success": False,

            "message": "Invalid plan."

        }), 400

    data = load_database()

    plan["id"] = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    plan["email"] = session["user"]

    plan["created_at"] = (
        datetime.now().isoformat()
    )

    data["plans"].append(
        plan
    )

    save_database(
        data
    )

    return jsonify({

        "success": True,

        "message": "Study plan saved successfully!",

        "plan": plan

    })


# =========================================================
# GET PLANS
# =========================================================

@app.route("/api/plans")
def get_plans():

    if "user" not in session:

        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401

    data = load_database()

    email = session["user"]

    plans = [

        plan

        for plan in data["plans"]

        if plan.get("email") == email

    ]

    return jsonify({

        "success": True,

        "plans": plans

    })


# =========================================================
# DELETE SINGLE PLAN
# =========================================================

@app.route(
    "/api/delete-plan/<plan_id>",
    methods=["DELETE"]
)
def delete_plan(plan_id):

    if "user" not in session:

        return jsonify({
            "success": False
        }), 401

    data = load_database()

    email = session["user"]

    old_count = len(
        data["plans"]
    )

    data["plans"] = [

        plan

        for plan in data["plans"]

        if not (

            plan.get("id") == plan_id

            and

            plan.get("email") == email

        )

    ]

    save_database(
        data
    )

    if len(data["plans"]) == old_count:

        return jsonify({

            "success": False,

            "message": "Plan not found."

        }), 404

    return jsonify({

        "success": True,

        "message": "Plan deleted."

    })


# =========================================================
# CLEAR ALL PLANS
# =========================================================

@app.route(
    "/api/clear-plans",
    methods=["DELETE"]
)
def clear_plans():

    if "user" not in session:

        return jsonify({
            "success": False
        }), 401

    data = load_database()

    email = session["user"]

    data["plans"] = [

        plan

        for plan in data["plans"]

        if plan.get("email") != email

    ]

    save_database(
        data
    )

    return jsonify({

        "success": True,

        "message": "All plans cleared."

    })


# =========================================================
# 🤖 GEMINI AI CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "user" not in session:

        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401


    # -----------------------------------------------------
    # GEMINI CHECK
    # -----------------------------------------------------

    if gemini_client is None:

        return jsonify({

            "success": False,

            "message": "Gemini AI is not configured. Please check GEMINI_API_KEY in .env."

        }), 500


    # -----------------------------------------------------
    # REQUEST DATA
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "success": False,

            "message": "Invalid request."

        }), 400


    question = str(
        data.get(
            "message",
            ""
        )
    ).strip()


    if not question:

        return jsonify({

            "success": False,

            "message": "Please enter a question."

        }), 400


    # -----------------------------------------------------
    # USER NAME
    # -----------------------------------------------------

    username = session.get(
        "username",
        "Student"
    )


    # -----------------------------------------------------
    # PLANORA AI PROMPT
    # -----------------------------------------------------

    prompt = f"""

You are Planora AI, an intelligent and friendly AI study
planning assistant.

Student name:
{username}

Your main purpose is to help students with:

📚 Study planning
📝 Exam preparation
🔄 Revision strategies
⏰ Time management
📖 Subject-wise preparation
📅 Daily study schedules
🎯 Important topics
🧠 Learning strategies
✍️ Practice questions
📊 Mock test preparation

IMPORTANT RULES:

1. Give practical and realistic study advice.

2. Keep answers simple and easy for students to understand.

3. If the student provides an exam date, calculate the preparation
   schedule based on that information.

4. If the student provides the number of days, use those days.

5. If the student provides daily study hours, divide the schedule
   according to those hours.

6. If subjects are provided, prioritize difficult or important
   subjects.

7. Include revision and practice when creating study plans.

8. Suggest short breaks during long study sessions.

9. Use headings, bullet points and tables when useful.

10. If the student asks for a day-wise study plan, provide a
    clear Day 1, Day 2, Day 3 style schedule.

11. If some information is missing, make a reasonable assumption
    instead of repeatedly asking questions when a useful answer
    can still be provided.

12. You are a study assistant and should stay focused on
    education, study planning and exam preparation.

13. Do not provide unsafe or harmful instructions.

Student's question:

{question}

Now provide the best helpful answer.
"""


    # -----------------------------------------------------
    # GEMINI REQUEST
    # -----------------------------------------------------

    try:

        print("=" * 60)

        print("🤖 Gemini request received")

        print("👤 Student:", username)

        print("💬 Question:", question)

        print("=" * 60)


        result = gemini_client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt

        )


        # -------------------------------------------------
        # GET RESPONSE TEXT
        # -------------------------------------------------

        answer = getattr(
            result,
            "text",
            None
        )


        if not answer:

            print(
                "⚠️ Gemini returned empty response."
            )

            print(
                result
            )

            return jsonify({

                "success": False,

                "message":
                    "Gemini returned an empty response."

            }), 500


        print("✅ Gemini response received")


        return jsonify({

            "success": True,

            "response": answer

        })


    except Exception as error:

        # -------------------------------------------------
        # IMPORTANT DEBUG OUTPUT
        # -------------------------------------------------

        print("")
        print("=" * 60)
        print("❌ GEMINI ERROR")
        print("=" * 60)
        print("ERROR TYPE:")
        print(type(error).__name__)
        print("")
        print("ERROR MESSAGE:")
        print(str(error))
        print("=" * 60)
        print("")


        return jsonify({

            "success": False,

            "message":
                "AI service is temporarily unavailable. Check the terminal for the Gemini error."

        }), 500


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return "Page not found", 404


@app.errorhandler(500)
def server_error(error):

    return "Internal server error", 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print("=" * 55)

    print(
        "📚 PLANORA AI"
    )

    print(
        "🤖 AI Study Planner"
    )

    print("=" * 55)

    print(
        "💾 Local database enabled"
    )

    if GEMINI_API_KEY:

        print(
            "🤖 Gemini API key detected"
        )

    else:

        print(
            "⚠️ Gemini API key NOT detected"
        )

    print(
        "🌐 http://127.0.0.1:5000"
    )

    print("=" * 55)


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )