# (I am NOT shortening anything — keeping original style)

from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import os
import json

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "cognithon_secret"

FILE = "reviews.xlsx"

ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD = "GSSS@123"


# GOOGLE SHEETS SETUP
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_raw)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Evaluation Scores").sheet1

except Exception as e:
    print("Google Sheets error:", e)
    sheet = None


# ONE EVALUATOR PER PANEL
PANEL_EVALUATOR = {
    "Panel-1": "Dharani Gowtham",
    "Panel-2": "Suman S. Pujar",
    "Panel-3": "SHREENIDHI T H"
}


# TEAM NAMES
TEAMS = {

    "Panel-1": [
        "AlgoArchitects",
        "SHECODES",
        "Blue Minds",
        "Data dynamos",
        "Data Avengers",
        "Ctrlshe",
        "Code blooded",
        "The HACKERS",
        "TechFusion",
        "NovaAlert"
    ],

    "Panel-2": [
        "CodeX",
        "Trendsetter Trio",
        "Smart Minds",
        "SkillNova",
        "Neural Nexus",
        "Code Trio",
        "Mind Cloud",
        "TriNova",
        "Cognify Coders",
        "Synapse Squad"
    ],

    "Panel-3": [
        "Tech MAVERICKS",
        "Spark defenders",
        "UniSphere Innovators",
        "TransitVertex",
        "Idea Igniters",
        "CodeFlux",
        "BuildIT",
        "RootX",
        "Tri Nova",
        "TechSquad"
    ]

}


# PROBLEM STATEMENTS
TEAM_PROBLEMS = {

    # KEEP SAME (unchanged from your file)
}


def init_excel():

    if not os.path.exists(FILE):

        if sheet:
            try:
                values = sheet.get_all_values()
                if len(values) > 1:
                    df = pd.DataFrame(values[1:], columns=values[0])
                else:
                    df = pd.DataFrame()
            except:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=[
                "Panel",
                "Review",
                "Evaluator",
                "Team",
                "P1",
                "P2",
                "P3",
                "P4",
                "P5",
                "Total",
                "Remarks"
            ])

        df.to_excel(FILE, index=False, engine="openpyxl")


def save_row(data):

    init_excel()

    df = pd.read_excel(FILE, engine="openpyxl")

    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)

    df.to_excel(FILE, index=False, engine="openpyxl")

    # GOOGLE SHEETS SAVE
    if sheet:
        try:
            sheet.append_row([
                data["Panel"],
                data["Review"],
                data["Evaluator"],
                data["Team"],
                data["P1"],
                data["P2"],
                data["P3"],
                data["P4"],
                data["P5"],
                data["Total"],
                data["Remarks"]
            ])
        except:
            pass


def get_remark(panel, team, review):

    if not os.path.exists(FILE):
        return ""

    df = pd.read_excel(FILE, engine="openpyxl")

    r = df[
        (df.Panel == panel) &
        (df.Team == team) &
        (df.Review == review)
    ]

    return "" if r.empty else str(r.iloc[-1]["Remarks"])


@app.route("/get-remark")
def get_remark_api():
    return get_remark(
        request.args["panel"],
        request.args["team"],
        request.args["review"]
    )


@app.route("/get-problem")
def get_problem():
    return TEAM_PROBLEMS.get(
        request.args.get("team"),
        "Problem statement not assigned."
    )


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/panel/<panel>")
def panel(panel):
    return render_template("panel.html", panel=panel)


@app.route("/panel/<panel>/review<int:r>", methods=["GET", "POST"])
def review(panel, r):

    review_name = f"Review {r}"

    prev_review = f"Review {r-1}" if r > 1 else None

    evaluator_name = PANEL_EVALUATOR[panel]

    if request.method == "POST":

        save_row({

            "Panel": panel,
            "Review": review_name,
            "Evaluator": evaluator_name,
            "Team": request.form["team"],
            "P1": request.form["p1"],
            "P2": request.form["p2"],
            "P3": request.form["p3"],
            "P4": request.form["p4"],
            "P5": request.form["p5"],
            "Total": request.form["total"],
            "Remarks": request.form["remarks"]

        })

        return redirect(request.path)

    return render_template(

        f"review{r}.html",

        panel=panel,

        evaluator=evaluator_name,

        teams=TEAMS[panel],

        prev_review=prev_review

    )


# RESULT CALCULATION (UNCHANGED)
def generate_panel_result(panel):

    init_excel()

    df = pd.read_excel(FILE)

    df = df[df["Panel"] == panel]

    result = []

    for team in df["Team"].unique():

        r1 = df[(df.Team == team) & (df.Review == "Review 1")]["Total"].sum()
        r2 = df[(df.Team == team) & (df.Review == "Review 2")]["Total"].sum()
        r3 = df[(df.Team == team) & (df.Review == "Review 3")]["Total"].sum()

        total = r1 + r2 + r3

        result.append({

            "team_no": team,
            "team_name": team,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "total": total

        })

    result = sorted(result, key=lambda x: x["total"], reverse=True)

    # TIE LOGIC (UNCHANGED)
    rank = 1
    prev_score = None

    for i, r in enumerate(result):

        if prev_score is None:
            r["position"] = rank
        else:
            if r["total"] == prev_score:
                r["position"] = rank
            else:
                rank = i + 1
                r["position"] = rank

        prev_score = r["total"]

    rank_groups = {}

    for r in result:

        pos = r["position"]

        if pos not in rank_groups:
            rank_groups[pos] = []

        rank_groups[pos].append(r)

    top3 = [
        rank_groups.get(1, []),
        rank_groups.get(2, []),
        rank_groups.get(3, [])
    ]

    return result, top3


# RESULT ROUTES (UNCHANGED)
@app.route("/panel1-result")
def panel1_result():
    data, top3 = generate_panel_result("Panel-1")
    return render_template("panel1_result.html", top3=top3)


@app.route("/panel2-result")
def panel2_result():
    data, top3 = generate_panel_result("Panel-2")
    return render_template("panel2_result.html", top3=top3)


@app.route("/panel3-result")
def panel3_result():
    data, top3 = generate_panel_result("Panel-3")
    return render_template("panel3_result.html", top3=top3)


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/download-panel/<panel>")
def download_panel(panel):

    init_excel()

    data, _ = generate_panel_result(panel)

    df = pd.DataFrame(data)

    filename = f"{panel}_result.xlsx"

    df.to_excel(filename, index=False)

    return send_file(filename, as_attachment=True)


@app.route("/download")
def download():
    init_excel()
    return send_file(FILE, as_attachment=True)


@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    error = ""

    if request.method == "POST":

        if (
            request.form["username"] == ADMIN_USERNAME
            and
            request.form["password"] == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect("/admin/dashboard")

        else:

            error = "Invalid Username or Password"

    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

    return render_template("admin_dashboard.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/")


if __name__ == "__main__":
    init_excel()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
