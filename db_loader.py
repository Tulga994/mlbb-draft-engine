import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and makes DATABASE_URL available via os.environ


def get_connection():
    db_url = os.environ["DATABASE_URL"]  # pulls the connection string out of the environment, not hardcoded in code
    return psycopg2.connect(db_url)


def load_heroes_from_db():
    """Returns a dict shaped exactly like the old HEROES dict, e.g.
    {"Khufra": {"role": "Tank", "lane": "Roam", "archetypes": {...}, "counters": {...}, "countered_by": {...}, "meta_strength": 8}}
    """
    conn = get_connection()
    cursor = conn.cursor()  # a cursor is what actually sends queries and reads results back, one at a time

    cursor.execute("SELECT name, role, lane, archetypes, counters, countered_by, meta_strength FROM heroes;")
    rows = cursor.fetchall()  # pulls every matching row back as a list of tuples

    heroes = {}
    for row in rows:  # each row is a tuple: (name, role, lane, archetypes, counters, countered_by, meta_strength)
        name, role, lane, archetypes, counters, countered_by, meta_strength = row  # unpack the tuple into named variables
        heroes[name] = {
            "role": role,
            "lane": lane,
            "archetypes": set(archetypes),  # psycopg2 hands back TEXT[] as a Python list -- convert to set
            "counters": set(counters),  # to match what score_hero's & operator expects
            "countered_by": set(countered_by),
            "meta_strength": meta_strength,
        }

    cursor.close()
    conn.close()  # always close the connection when you're done with it
    return heroes


def load_compositions_from_db():
    """Returns a dict shaped like the old COMPOSITIONS dict, e.g.
    {"dive_burst": {"dive", "burst", "engage", "snowball"}}
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, signature_tags FROM compositions;")
    rows = cursor.fetchall()

    compositions = {}
    for row in rows:
        name, signature_tags = row
        compositions[name] = set(signature_tags)

    cursor.close()
    conn.close()
    return compositions


if __name__ == "__main__":
    heroes = load_heroes_from_db()
    comps = load_compositions_from_db()
    print(f"Loaded {len(heroes)} heroes and {len(comps)} compositions from Neon:\n")
    for name, data in heroes.items():
        print(f"  {name}: {data}")