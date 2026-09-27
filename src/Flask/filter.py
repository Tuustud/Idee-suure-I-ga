from pathlib import Path
import random
import sqlite3

DATABASE_FILE = Path(__file__).with_name("database.db")

TIME_LEVELS = {
    "0-15min": 1,
    "15-45min": 2,
    "45min-1.5h": 3,
}


def _normalize_requirement(value):
    """Normaliseeri andmebaasi nõude väärtus."""
    value = (value or "").strip()

    # Andmebaasis on praegu üks kirjaviga: Paber-ja-Pliats.
    aliases = {
        "Paber-ja-Pliats": "Paber-ja-Pliiats",
    }
    return aliases.get(value, value)


def _normalize_location(value):
    """Normaliseeri andmebaasi asukohaväärtused."""
    value = (value or "").strip().lower()

    aliases = {
        "vaba õhk": "vaba õhk",
        "rahvarohke": "rahvarohke",
    }
    return aliases.get(value, value)


def find_matching_activities(time_category, capabilities, location_category):
    """
    Leia tegevused, mis sobivad kasutaja aja, vahendite ja asukohaga.

    - Lühema ajakategooria tegevus sobib ka siis, kui kasutajal on rohkem aega.
    - Tühi requires1/requires2 tähendab, et tegevus seda vahendit ei nõua.
    - Tühi location tähendab, et tegevusel pole konkreetset asukohanõuet.
    - Kui kasutaja valib "Mitte midagi sobivat", sobivad ainult tegevused,
      mille location on andmebaasis tühi.
    """
    if time_category not in TIME_LEVELS:
        raise ValueError(f"Tundmatu ajakategooria: {time_category}")

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(f"Andmebaasi ei leitud: {DATABASE_FILE}")

    capabilities = {_normalize_requirement(value) for value in capabilities}
    location_category = _normalize_location(location_category)
    user_time_level = TIME_LEVELS[time_category]

    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, instructions, time, requires1, requires2, location
            FROM items
            ORDER BY id
            """
        ).fetchall()

    matches = []

    for row in rows:
        activity_time = (row["time"] or "").strip()
        activity_time_level = TIME_LEVELS.get(activity_time)

        if activity_time_level is None or activity_time_level > user_time_level:
            continue

        required_1 = _normalize_requirement(row["requires1"])
        required_2 = _normalize_requirement(row["requires2"])
        required = {value for value in (required_1, required_2) if value}

        if not required.issubset(capabilities):
            continue

        activity_location = _normalize_location(row["location"])

        # Tühi asukohaväli tähendab, et tegevus sobib igal pool.
        # Konkreetse asukohanõudega tegevus peab vastama kasutaja kategooriale.
        if activity_location:
            if not location_category or activity_location != location_category:
                continue

        matches.append({
            "id": row["id"],
            "name": row["name"],
            "instructions": row["instructions"],
            "time": activity_time,
            "requires1": required_1,
            "requires2": required_2,
            "location": activity_location,
        })

    return matches


def choose_activity(time_category, capabilities, location_category):
    """Leia sobivad tegevused ja vali neist juhuslikult üks."""
    matches = find_matching_activities(
        time_category=time_category,
        capabilities=capabilities,
        location_category=location_category,
    )

    if not matches:
        return None

    return random.choice(matches)
