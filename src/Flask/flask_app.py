from flask import Flask, jsonify, render_template, request

from filter import choose_activity

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/vabaaeg")
def free_time():
    return render_template("vabaaeg.html")


def convert_minutes_to_category(value):
    """Teisenda veebist saadud minutite arv andmebaasi ajakategooriaks."""
    try:
        minutes = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError("Aeg peab olema arv minutites.")

    if minutes <= 0:
        raise ValueError("Aeg peab olema suurem kui 0 minutit.")

    if minutes <= 15:
        return "0-15min"
    if minutes <= 45:
        return "15-45min"

    # Andmebaasi pikim ajakategooria on 45 min - 1,5 h.
    # Kui kasutajal on rohkem aega, võib talle endiselt pakkuda selle kategooria tegevusi.
    return "45min-1.5h"


def convert_tools_to_capabilities(tools):
    """Teisenda veebilehel valitud vahendid andmebaasi nõuete kujule."""
    if not isinstance(tools, list):
        tools = []

    selected = {str(tool).strip() for tool in tools}
    capabilities = set()

    if "Paber" in selected and "Pliiats" in selected:
        capabilities.add("Paber-ja-Pliiats")

    if "Laetud telefon" in selected:
        capabilities.add("Telefon/Arvuti")

    if "Wi-Fi/andmeside" in selected:
        capabilities.add("Wi-Fi/andmeside")

    if "Teine isik (võõras)" in selected or "Teine isik (tuttav)" in selected:
        capabilities.add("teine inimene")

    return capabilities


def convert_location_to_category(location):
    """Teisenda veebilehe konkreetne asukoht andmebaasi üldiseks asukohakategooriaks."""
    location = str(location or "").strip()

    mapping = {
        "Haigla ooteruum": "rahvarohke",
        "Bussipeatus/jaam": "rahvarohke",
        "Park": "vaba õhk",
        "Raamatukogu": "rahvarohke",
        "Buss": "rahvarohke",
        # Kui ükski etteantud koht ei sobi, pakutakse ainult tegevusi,
        # millel andmebaasis puudub konkreetne asukohanõue.
        "Mitte midagi sobivat": "",
    }

    if location not in mapping:
        raise ValueError("Vali asukoht rippmenüüst.")

    return mapping[location]


@app.route("/genereeri", methods=["POST"])
def generate_activity():
    """Võta veebilehe valikud vastu ja tagasta sobiv tegevus."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Vigane päring."}), 400

    try:
        time_category = convert_minutes_to_category(data.get("aeg"))
        capabilities = convert_tools_to_capabilities(data.get("vahendid", []))
        location_category = convert_location_to_category(data.get("asukoht"))

        activity = choose_activity(
            time_category=time_category,
            capabilities=capabilities,
            location_category=location_category,
        )

    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    except FileNotFoundError as error:
        app.logger.exception("Andmebaasi ei leitud")
        return jsonify({"success": False, "error": str(error)}), 500
    except Exception:
        app.logger.exception("Tegevuse genereerimine ebaõnnestus")
        return jsonify({
            "success": False,
            "error": "Tegevuse genereerimisel tekkis serveri viga."
        }), 500

    if activity is None:
        return jsonify({
            "success": True,
            "found": False,
            "message": "Nende valikutega sobivat tegevust praegu andmebaasis ei ole."
        })

    return jsonify({
        "success": True,
        "found": True,
        "activity": {
            "id": activity["id"],
            "name": activity["name"],
            "instructions": activity["instructions"],
        }
    })


if __name__ == "__main__":
    app.run(debug=True)
