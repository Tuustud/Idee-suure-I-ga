from flask import Flask, jsonify, render_template, request

from filter import (
    choose_activity,
    get_available_locations,
    get_available_requirements,
    get_available_times,
)

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/vabaaeg")
def free_time():
    """Loe valikute loetelud andmebaasist ja anna need HTML-ile."""
    try:
        times = get_available_times()
        requirements = get_available_requirements()
        locations = get_available_locations()
    except FileNotFoundError:
        app.logger.exception("Andmebaasi ei leitud")
        times = []
        requirements = []
        locations = []

    return render_template(
        "vabaaeg.html",
        available_times=times,
        available_requirements=requirements,
        available_locations=locations,
    )


@app.route("/tulemus")
def result_page():
    return render_template("tulemus.html")


def validate_time_category(value):
    """Kontrolli, et valitud ajavahemik pärineb andmebaasist."""
    value = str(value or "").strip()

    if not value:
        raise ValueError("Vali ajavahemik.")

    available = set(get_available_times())
    if value not in available:
        raise ValueError("Valitud ajavahemikku andmebaasis ei ole.")

    return value


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
        time_category = validate_time_category(data.get("aeg"))
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
