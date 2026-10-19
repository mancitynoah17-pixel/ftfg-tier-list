
from flask import Flask, render_template
from pathlib import Path

app = Flask(__name__)

PEOPLE_FOLDER = Path(app.static_folder) / "people"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@app.route("/")
def home():
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

if __name__ == "__main__":
    app.run(debug=True)
