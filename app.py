from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from datetime import datetime

from dotenv import load_dotenv

# =========================================================
# FIREBASE
# =========================================================

import firebase_admin
from firebase_admin import credentials, firestore, auth


# =========================================================
# GEMINI
# =========================================================

from google import genai


# =========================================================
# LOAD ENVIRONMENT VARIABLES
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
# FIREBASE ADMIN + FIRESTORE
# =========================================================

db = None

try:

    firebase_key_path = "firebase-key.json"

    if not firebase_admin._apps:

        if os.path.exists(firebase_key_path):

            cred = credentials.Certificate(
                firebase_key_path
            )

            firebase_admin.initialize_app(cred)

            print("Firebase connected successfully")

        else:

            print("firebase-key.json not found")

    if firebase_admin._apps:

        db = firestore.client()

        print("Firestore connected successfully")

except Exception as error:

    print("Firebase connection error:")
    print(error)

    db = None


# =========================================================
# GEMINI AI
# =========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

gemini_client = None


if GEMINI_API_KEY:

    try:

        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("Gemini AI connected successfully")

    except Exception as error:

        print("Gemini connection error:")
        print(error)

else:

    print("GEMINI_API_KEY not found")


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
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    if "user" in session:

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# FIREBASE LOGIN
# =========================================================

@app.route(
    "/auth/firebase-login",
    methods=["POST"]
)
def firebase_login():

    if db is None:

        return jsonify({

            "success": False,

            "message":
                "Firebase is not configured."

        }), 500


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "message":
                "Invalid request."

        }), 400


    # Get Firebase ID Token

    id_token = str(

        data.get(
            "idToken",
            ""
        )

    ).strip()


    if not id_token:

        return jsonify({

            "success": False,

            "message":
                "Authentication token is missing."

        }), 400


    try:

        # =================================================
        # VERIFY FIREBASE TOKEN
        # =================================================

        decoded_token = auth.verify_id_token(
            id_token
        )


        # =================================================
        # GET USER DETAILS
        # =================================================

        uid = decoded_token.get(
            "uid"
        )


        email = decoded_token.get(
            "email",
            ""
        ).lower()


        username = decoded_token.get(
            "name",
            ""
        )


        if not email:

            return jsonify({

                "success": False,

                "message":
                    "Email not found."

            }), 400


        if not username:

            username = email.split("@")[0]


        # =================================================
        # FIRESTORE USER DOCUMENT
        # =================================================

        user_ref = (

            db.collection("users")
            .document(uid)

        )


        user_doc = user_ref.get()


        # =================================================
        # CREATE USER IF NOT EXISTS
        # =================================================

        if not user_doc.exists:

            user_ref.set({

                "uid": uid,

                "username": username,

                "email": email,

                "created_at":
                    datetime.now().isoformat()

            })


        else:

            user_data = user_doc.to_dict()

            username = user_data.get(

                "username",

                username

            )


        # =================================================
        # CREATE FLASK SESSION
        # =================================================

        session["user"] = uid

        session["email"] = email

        session["username"] = username


        return jsonify({

            "success": True,

            "message":
                "Login successful.",

            "username": username

        })


    except Exception as error:

        print("Firebase login error:")
        print(error)


        return jsonify({

            "success": False,

            "message":
                "Authentication failed."

        }), 401


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
            "email",
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

        "username":
            session.get(
                "username"
            ),

        "email":
            session.get(
                "email"
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

            "message":
                "Please login first."

        }), 401


    if db is None:

        return jsonify({

            "success": False,

            "message":
                "Firestore is not connected."

        }), 500


    plan = request.get_json(
        silent=True
    )


    if not plan:

        return jsonify({

            "success": False,

            "message":
                "Invalid plan."

        }), 400


    try:

        uid = session["user"]


        # =================================================
        # FIRESTORE AUTO ID
        # =================================================

        plan_ref = (

            db.collection("users")
            .document(uid)
            .collection("plans")
            .document()

        )


        plan["id"] = plan_ref.id


        plan["created_at"] = (
            datetime.now().isoformat()
        )


        plan_ref.set(plan)


        return jsonify({

            "success": True,

            "message":
                "Study plan saved successfully!",

            "plan": plan

        })


    except Exception as error:

        print("Firestore save error:")
        print(error)


        return jsonify({

            "success": False,

            "message":
                "Failed to save study plan."

        }), 500


# =========================================================
# GET STUDY PLANS
# =========================================================

@app.route("/api/plans")
def get_plans():

    if "user" not in session:

        return jsonify({

            "success": False,

            "message":
                "Please login first."

        }), 401


    if db is None:

        return jsonify({

            "success": False,

            "message":
                "Firestore is not connected."

        }), 500


    try:

        uid = session["user"]


        plans_ref = (

            db.collection("users")
            .document(uid)
            .collection("plans")

        )


        plans = []


        for document in plans_ref.stream():

            plan = document.to_dict()

            plan["id"] = document.id

            plans.append(plan)


        return jsonify({

            "success": True,

            "plans": plans

        })


    except Exception as error:

        print("Firestore fetch error:")
        print(error)


        return jsonify({

            "success": False,

            "message":
                "Failed to load plans."

        }), 500


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


    if db is None:

        return jsonify({

            "success": False,

            "message":
                "Firestore is not connected."

        }), 500


    try:

        uid = session["user"]


        plan_ref = (

            db.collection("users")
            .document(uid)
            .collection("plans")
            .document(plan_id)

        )


        plan_doc = plan_ref.get()


        if not plan_doc.exists:

            return jsonify({

                "success": False,

                "message":
                    "Plan not found."

            }), 404


        plan_ref.delete()


        return jsonify({

            "success": True,

            "message":
                "Plan deleted."

        })


    except Exception as error:

        print("Firestore delete error:")
        print(error)


        return jsonify({

            "success": False,

            "message":
                "Failed to delete plan."

        }), 500


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


    if db is None:

        return jsonify({

            "success": False,

            "message":
                "Firestore is not connected."

        }), 500


    try:

        uid = session["user"]


        plans_ref = (

            db.collection("users")
            .document(uid)
            .collection("plans")

        )


        documents = plans_ref.stream()


        for document in documents:

            document.reference.delete()


        return jsonify({

            "success": True,

            "message":
                "All plans cleared."

        })


    except Exception as error:

        print("Firestore clear error:")
        print(error)


        return jsonify({

            "success": False,

            "message":
                "Failed to clear plans."

        }), 500


# =========================================================
# GEMINI AI CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    if "user" not in session:

        return jsonify({

            "success": False,

            "message":
                "Please login first."

        }), 401


    if gemini_client is None:

        return jsonify({

            "success": False,

            "message":
                "Gemini AI is not configured."

        }), 500


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "message":
                "Invalid request."

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

            "message":
                "Please enter a question."

        }), 400


    username = session.get(
        "username",
        "Student"
    )


    prompt = f"""
You are Planora AI, an intelligent and friendly AI study planning assistant.

Student name: {username}

You help students with:

- Study planning
- Exam preparation
- Revision strategies
- Time management
- Subject-wise preparation
- Daily study schedules
- Important topics
- Learning strategies
- Practice questions
- Mock test preparation

Student question:

{question}

Give a practical, clear and student-friendly answer.
"""


    try:

        print("=" * 60)

        print("Gemini request received")

        print(
            "Student:",
            username
        )

        print(
            "Question:",
            question
        )

        print("=" * 60)


        result = (

            gemini_client
            .models
            .generate_content(

                model="gemini-3.6-flash",

                contents=prompt

            )

        )


        answer = getattr(

            result,

            "text",

            None

        )


        if not answer:

            return jsonify({

                "success": False,

                "message":
                    "Gemini returned an empty response."

            }), 500


        return jsonify({

            "success": True,

            "response": answer

        })


    except Exception as error:

        print("=" * 60)

        print("GEMINI ERROR")

        print(
            type(error).__name__
        )

        print(
            str(error)
        )

        print("=" * 60)


        return jsonify({

            "success": False,

            "message":
                "AI service is temporarily unavailable."

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

    print("PLANORA AI")

    print("AI Study Planner")

    print("=" * 55)


    if db:

        print(
            "Firebase connected"
        )

        print(
            "Firestore connected"
        )

    else:

        print(
            "Firebase not connected"
        )


    if GEMINI_API_KEY:

        print(
            "Gemini API key detected"
        )

    else:

        print(
            "Gemini API key NOT detected"
        )


    print(
        "http://127.0.0.1:5000"
    )

    print("=" * 55)


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )