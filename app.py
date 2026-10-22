from flask import Flask, render_template, request, jsonify
from pathlib import Path
import sqlite3
import json
import math

app = Flask(__name__)

PEOPLE_FOLDER = Path(app.static_folder) / "people"
DATABASE = Path(app.instance_path) / "leaderboard.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

PLAYERS = [
    "Max", "Quinn", "Chase", "Will", "Walter",
    "Connor", "Noah", "Jaden", "Jackson"
]

# Now 9 total attributes
ATTRIBUTES = [
    "Height",
    "Build",
    "Smarts",
    "Athleticism",
    "Kindliness",
    "Humorous",
    "Manners",
    "Rizz",
    "Vehicle"
]

RATINGS = {
    "Max": {
        "Build": 70,
        "Smarts": 99,
        "Athleticism": 94,
        "Kindliness": 91,
        "Humorous": 82,
        "Manners": 93,
        "Rizz": 93,
        "Vehicle": 99
    },
    "Quinn": {
        "Build": 89,
        "Smarts": 88,
        "Athleticism": 95,
        "Kindliness": 81,
        "Humorous": 88,
        "Manners": 85,
        "Rizz": 84,
        "Vehicle": 92
    },
    "Chase": {
        "Build": 75,
        "Smarts": 95,
        "Athleticism": 83,
        "Kindliness": 89,
        "Humorous": 83,
        "Manners": 80,
        "Rizz": 32,
        "Vehicle": 84
    },
    "Will": {
        "Build": 95,
        "Smarts": 83,
        "Athleticism": 88,
        "Kindliness": 94,
        "Humorous": 90,
        "Manners": 94,
        "Rizz": 95,
        "Vehicle": 90
    },
    "Walter": {
        "Build": 80,
        "Smarts": 99,
        "Athleticism": 87,
        "Kindliness": 97,
        "Humorous": 91,
        "Manners": 81,
        "Rizz": 92,
        "Vehicle": 65
    },
    "Connor": {
        "Build": 96,
        "Smarts": 79,
        "Athleticism": 85,
        "Kindliness": 80,
        "Humorous": 98,
        "Manners": 61,
        "Rizz": 89,
        "Vehicle": 0
    },
    "Noah": {
        "Build": 73,
        "Smarts": 86,
        "Athleticism": 93,
        "Kindliness": 85,
        "Humorous": 93,
        "Manners": 85,
        "Rizz": 91,
        "Vehicle": 85
    },
    "Jaden": {
        "Build": 96,
        "Smarts": 80,
        "Athleticism": 94,
        "Kindliness": 96,
        "Humorous": 90,
        "Manners": 95,
        "Rizz": 92,
        "Vehicle": 75
    },
    "Jackson": {
        "Build": 86,
        "Smarts": 96,
        "Athleticism": 85,
        "Kindliness": 89,
        "Humorous": 90,
        "Manners": 89,
        "Rizz": 97,
        "Vehicle": 81
    }
}

HEIGHTS = {
    "Max": "6'0\"",
    "Quinn": "6'3\"",
    "Chase": "5'11\"",
    "Will": "5'11\"",
    "Walter": "6'5\"",
    "Connor": "5'11\"",
    "Noah": "6'0\"",
    "Jaden": "5'8\"",
    "Jackson": "5'9\""
}


def round_half_up(value):
    """Match JavaScript Math.round for nonnegative scores."""
    return math.floor(value + 0.5)


def height_ovr(height):
    feet = int(height.split("'")[0])
    inches = int(height.split("'")[1].replace('"', ""))
    total_inches = feet * 12 + inches

    return max(
        1,
        min(99, 99 - (77 - total_inches) * 3)
    )


def get_rating(player, attribute):
    if attribute == "Height":
        return height_ovr(HEIGHTS[player])

    return RATINGS[player][attribute]


def calculate_scores(build):
    scores = {
        attribute: get_rating(player, attribute)
        for attribute, player in build.items()
    }

    # Overall:
    # Average of all NINE selected attribute ratings.
    overall = round_half_up(
        sum(scores.values()) / len(ATTRIBUTES)
    )

    # Money:
    # ((Manners + Kindliness) * Smarts) ** 2
    calculated_money = (
        (
            scores["Manners"]
            + scores["Kindliness"]
        )
        * scores["Smarts"]
    ) ** 2

    # Bih's Fuhed:
    # (Height + Build + Humorous + Athleticism + Kindliness) / 8
    #
    # This formula stays exactly the same as before.
    calculated_fuhed = (
        scores["Height"]
        + scores["Build"]
        + scores["Humorous"]
        + scores["Athleticism"]
        + scores["Kindliness"]
    ) / 8

    return {
        "overall": overall,
        "money": calculated_money,
        "fuhed": calculated_fuhed
    }


def init_database():
    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(DATABASE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                overall INTEGER NOT NULL,
                money INTEGER NOT NULL,
                fuhed REAL NOT NULL,
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
    PEOPLE_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

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

    return render_template(
        "index.html",
        people=people
    )


@app.route(
    "/api/leaderboard",
    methods=["GET"]
)
def get_leaderboard():
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT
                name,
                overall,
                money,
                fuhed,
                created_at
            FROM leaderboard
            ORDER BY
                overall DESC,
                money DESC,
                fuhed DESC,
                id ASC
            LIMIT 100
        """).fetchall()

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.route(
    "/api/leaderboard",
    methods=["POST"]
)
def save_leaderboard():
    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    build = data.get("build")

    if not name or len(name) > 24:
        return jsonify({
            "error": (
                "Enter a name of "
                "1–24 characters."
            )
        }), 400

    if not isinstance(build, dict):
        return jsonify({
            "error": "Your build is missing."
        }), 400

    # Must now contain all NINE attributes.
    if set(build.keys()) != set(ATTRIBUTES):
        return jsonify({
            "error": (
                "Your build must contain "
                "all nine attributes."
            )
        }), 400

    # Repeated players are allowed.
    if any(
        not isinstance(player, str)
        or player not in PLAYERS
        for player in build.values()
    ):
        return jsonify({
            "error": "Invalid player in build."
        }), 400

    try:
        # Calculate scores on the server.
        calculated = calculate_scores(build)

        overall = data.get("overall")
        money = data.get("money")
        fuhed = data.get("fuhed")

        if (
            isinstance(overall, bool)
            or not isinstance(
                overall,
                (int, float)
            )
        ):
            return jsonify({
                "error": "Invalid overall score."
            }), 400

        if (
            isinstance(money, bool)
            or not isinstance(
                money,
                (int, float)
            )
        ):
            return jsonify({
                "error": "Invalid money score."
            }), 400

        if (
            isinstance(fuhed, bool)
            or not isinstance(
                fuhed,
                (int, float)
            )
        ):
            return jsonify({
                "error": "Invalid Fuhed score."
            }), 400

        if not all(
            math.isfinite(value)
            for value in (
                overall,
                money,
                fuhed
            )
        ):
            return jsonify({
                "error": "Invalid score data."
            }), 400

        # Make sure browser-calculated scores
        # match server-calculated scores.
        if (
            overall != calculated["overall"]
            or money != calculated["money"]
            or not math.isclose(
                float(fuhed),
                calculated["fuhed"],
                rel_tol=0,
                abs_tol=1e-9
            )
        ):
            return jsonify({
                "error": (
                    "The submitted scores "
                    "don't match your build. "
                    "Please refresh and try again."
                )
            }), 400

        with sqlite3.connect(DATABASE) as connection:
            connection.execute("""
                INSERT INTO leaderboard
                    (
                        name,
                        overall,
                        money,
                        fuhed,
                        build
                    )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                calculated["overall"],
                calculated["money"],
                calculated["fuhed"],
                json.dumps(build)
            ))

        return jsonify({
            "success": True,
            "message": (
                "Your score has been submitted!"
            )
        }), 201

    except (
        TypeError,
        ValueError,
        KeyError,
        OverflowError
    ):
        return jsonify({
            "error": "Invalid score data."
        }), 400


if __name__ == "__main__":
    app.run(debug=True)
