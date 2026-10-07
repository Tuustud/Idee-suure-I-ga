from flask import Flask, jsonify, render_template, request

from filter import (
    choose_activity,
    get_available_locations,
    get_available_requirements,
)

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/vabaaeg")
def free_time():
    """Loe valikute loetelud andmebaasist ja anna need HTML-ile."""
    try:
        requirements = get_available_requirements()
        locations = get_available_locations()
    except FileNotFoundError:
        app.logger.exception("Andmebaasi ei leitud")
        requirements = []
        locations = []

    return render_template(
        "vabaaeg.html",
        available_requirements=requirements,
        available_locations=locations,
    )


@app.route("/tulemus")
def result_page():
    return render_template("tulemus.html")


def convert_minutes_to_category(value):
    """Teisenda minutite arv andmebaasi ajakategooriaks."""
    try:
        minutes = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError("Aeg peab olema arv.")

    if minutes <= 0:
        raise ValueError("Aeg peab olema suurem kui 0.")

    if minutes <= 15:
        return "0-15min"
    if minutes <= 45:
        return "15-45min"

    # Andmebaasi pikim kategooria on 45 min - 1,5 h.
    return "45min-1.5h"


def validate_requirements(requirements):
    """Kontrolli, et valitud nõuded pärinevad andmebaasist."""
    if not isinstance(requirements, list):
        raise ValueError("Vahendite valik peab olema loetelu.")

    cleaned = [str(value).strip() for value in requirements if str(value).strip()]

    if len(cleaned) > 2:
        raise ValueError("Valida saab maksimaalselt 2 vahendit.")

    available = set(get_available_requirements())
    unknown = [value for value in cleaned if value not in available]

    if unknown:
        raise ValueError("Valitud vahendit andmebaasis ei ole.")

    return set(cleaned)


def validate_location(location):
    """Kontrolli, et valitud asukoht pärineb andmebaasist."""
    location = str(location or "").strip().lower()

    if not location:
        raise ValueError("Vali asukoht.")

    available = set(get_available_locations())
    if location not in available:
        raise ValueError("Valitud asukohta andmebaasis ei ole.")

    return location


@app.route("/genereeri", methods=["POST"])
def generate_activity():
    """Võta veebilehe valikud vastu ja tagasta sobiv tegevus."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Vigane päring."}), 400

    try:
        time_category = convert_minutes_to_category(data.get("aeg"))
        capabilities = validate_requirements(data.get("vahendid", []))
        location_category = validate_location(data.get("asukoht"))

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
