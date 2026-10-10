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

    # Praeguses andmebaasis esineb see kirjaviga ühel real.
    aliases = {
        "Paber-ja-Pliats": "Paber-ja-Pliiats",
    }
    return aliases.get(value, value)


def _normalize_location(value):
    """Normaliseeri asukoha väärtus võrdlemiseks."""
    return (value or "").strip().lower()


def _check_database():
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(f"Andmebaasi ei leitud: {DATABASE_FILE}")


def get_available_times():
    """Tagasta time veeru unikaalsed mittetühjad ajavahemikud."""
    _check_database()

    with sqlite3.connect(DATABASE_FILE) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT time
            FROM items
            WHERE TRIM(COALESCE(time, '')) <> ''
            """
        ).fetchall()

    times = {(row[0] or "").strip() for row in rows if (row[0] or "").strip()}

    # Tuntud ajavahemikud kuvatakse loogilises pikkuse järjekorras.
    # Kui andmebaasi lisatakse uus ajavahemik, jääb see samuti loetellu.
    return sorted(
        times,
        key=lambda value: (TIME_LEVELS.get(value, 999), value.casefold()),
    )


def get_available_requirements():
    """Tagasta requires1 ja requires2 veergude unikaalsed mittetühjad väärtused."""
    _check_database()

    with sqlite3.connect(DATABASE_FILE) as conn:
        rows = conn.execute(
            """
            SELECT requires1 FROM items
            UNION ALL
            SELECT requires2 FROM items
            """
        ).fetchall()

    requirements = {
        _normalize_requirement(row[0])
        for row in rows
        if _normalize_requirement(row[0])
    }

    return sorted(requirements, key=str.casefold)


def get_available_locations():
    """Tagasta location veeru unikaalsed mittetühjad väärtused."""
    _check_database()

    with sqlite3.connect(DATABASE_FILE) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT location
            FROM items
            WHERE TRIM(COALESCE(location, '')) <> ''
            """
        ).fetchall()

    locations = {
        _normalize_location(row[0])
        for row in rows
        if _normalize_location(row[0])
    }

    return sorted(locations, key=str.casefold)


def find_matching_activities(time_category, capabilities, location_category):
    """Leia tegevused kasutaja aja, vahendite ja asukoha järgi."""
    if time_category not in TIME_LEVELS:
        raise ValueError(f"Tundmatu ajakategooria: {time_category}")

    _check_database()

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

        # Pikemat tegevust ei pakuta, kui kasutajal pole piisavalt aega.
        if activity_time_level is None or activity_time_level > user_time_level:
            continue

        required_1 = _normalize_requirement(row["requires1"])
        required_2 = _normalize_requirement(row["requires2"])
        required = {value for value in (required_1, required_2) if value}

        # Kasutajal peab olema vähemalt kõik see, mida tegevus nõuab.
        if not required.issubset(capabilities):
            continue

        activity_location = _normalize_location(row["location"])

        # Tühi location tähendab, et tegevus sobib igas asukohas.
        if activity_location and activity_location != location_category:
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
