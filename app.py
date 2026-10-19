
from flask import Flask, render_template, request, jsonify
from pathlib import Path
import sqlite3
import json

app = Flask(__name__)

PEOPLE_FOLDER = Path(app.static_folder) / "people"
DATABASE = Path(app.instance_path) / "leaderboard.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

PLAYERS = [
    "Max", "Quinn", "Chase", "Will", "Walter",
    "Connor", "Noah", "Jaden", "Jackson"
]

ATTRIBUTES = [
    "Height", "Build", "Smarts", "Athleticism",
    "Kindliness", "Humorous", "Manners"
]

RATINGS = {
    "Max":     {"Build": 70, "Smarts": 99, "Athleticism": 94, "Kindliness": 91, "Humorous": 82, "Manners": 93},
    "Quinn":   {"Build": 89, "Smarts": 88, "Athleticism": 95, "Kindliness": 81, "Humorous": 88, "Manners": 85},
    "Chase":   {"Build": 75, "Smarts": 95, "Athleticism": 83, "Kindliness": 89, "Humorous": 83, "Manners": 80},
    "Will":    {"Build": 95, "Smarts": 83, "Athleticism": 88, "Kindliness": 94, "Humorous": 90, "Manners": 94},
    "Walter":  {"Build": 80, "Smarts": 99, "Athleticism": 87, "Kindliness": 97, "Humorous": 91, "Manners": 81},
    "Connor":  {"Build": 96, "Smarts": 79, "Athleticism": 85, "Kindliness": 80, "Humorous": 98, "Manners": 61},
    "Noah":    {"Build": 73, "Smarts": 86, "Athleticism": 93, "Kindliness": 85, "Humorous": 93, "Manners": 85},
    "Jaden":   {"Build": 96, "Smarts": 80, "Athleticism": 94, "Kindliness": 96, "Humorous": 90, "Manners": 95},
    "Jackson": {"Build": 86, "Smarts": 96, "Athleticism": 85, "Kindliness": 89, "Humorous": 90, "Manners": 89}
}

HEIGHTS = {
    "Max":  "6'0\"",
    "Quinn": "6'3\"",
    "Chase": "5'11\"",
    "Will": "5'11\"",
    "Walter": "6'5\"",
    "Connor": "5'11\"",
    "Noah": "6'0\"",
    "Jaden": "5'8\"",
    "Jackson": "5'9\""
}


def height_ovr(height):
    feet = int(height.split("'")[0])
    inches = int(height.split("'")[1].replace('"', ""))
    total_inches = feet * 12 + inches
    return max(1, min(99, 99 - (77 - total_inches) * 3))


def get_rating(player, attribute):
    if attribute == "Height":
        return height_ovr(HEIGHTS[player])
    return RATINGS[player][attribute]


def init_database():
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                overall INTEGER NOT NULL,
                money INTEGER NOT NULL,
                fuhed INTEGER NOT NULL,
                build TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_database()


@app.route("/")
def home():
    return render_template("game.html")


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/tier-list")
def tier_list():
    PEOPLE_FOLDER.mkdir(parents=True, exist_ok=True)

    people = [
        {
            "name": image.stem,
            "src": "/static/people/" + image.name
        }
        for image in sorted(
            PEOPLE_FOLDER.iterdir(),
            key=lambda image: image.name.lower()
        )
        if image.is_file()
        and image.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    return render_template("index.html", people=people)


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT name, overall, money, fuhed, created_at
            FROM leaderboard
            ORDER BY overall DESC, money DESC, fuhed DESC, id ASC
            LIMIT 100
        """).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/leaderboard", methods=["POST"])
def save_leaderboard():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    build = data.get("build")
    overall = data.get("overall")
    money = data.get("money")
    fuhed = data.get("fuhed")

    if not name or len(name) > 24:
        return jsonify({"error": "Enter a name of 1–24 characters."}), 400

    if not isinstance(build, dict):
        return jsonify({"error": "Your build is missing."}), 400

    if set(build.keys()) != set(ATTRIBUTES):
        return jsonify({"error": "Your build must contain all seven attributes."}), 400

    if any(player not in PLAYERS for player in build.values()):
        return jsonify({"error": "Invalid player in build."}), 400

    if len(set(build.values())) != 7:
        return jsonify({"error": "Each player can only be selected once."}), 400

    try:
        # Recalculate scores on the server instead of trusting browser values.
        scores = {
            attribute: get_rating(player, attribute)
            for attribute, player in build.items()
        }

        calculated_overall = round(sum(scores.values()) / 7)

        money_attributes = ["Smarts", "Kindliness", "Humorous", "Manners"]
        fuhed_attributes = ["Build", "Humorous", "Manners", "Height"]

        calculated_money = round(
            sum(scores[a] for a in money_attributes) /
            len(money_attributes)
        )

        calculated_fuhed = round(
            sum(scores[a] for a in fuhed_attributes) /
            len(fuhed_attributes)
        )

        # Reject a submission if the supplied scores don't match the build.
        if (
            overall != calculated_overall
            or money != calculated_money
            or fuhed != calculated_fuhed
        ):
            return jsonify({"error": "The submitted scores don't match your build. Please refresh and try again."}), 400

        with sqlite3.connect(DATABASE) as connection:
            connection.execute("""
                INSERT INTO leaderboard
                    (name, overall, money, fuhed, build)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                calculated_overall,
                calculated_money,
                calculated_fuhed,
                json.dumps(build)
            ))

        return jsonify({
            "success": True,
            "message": "Your score has been submitted!"
        }), 201

    except (TypeError, ValueError):
        return jsonify({"error": "Invalid score data."}), 400


if __name__ == "__main__":
    app.run(debug=True)
