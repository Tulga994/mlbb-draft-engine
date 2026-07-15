import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    db_url = os.environ["DATABASE_URL"]
    return psycopg2.connect(db_url)


def load_heroes_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, role, archetypes, counters, countered_by, meta_strength FROM heroes;")
    rows = cursor.fetchall()

    heroes = {}
    for row in rows:
        name, role, archetypes, counters, countered_by, meta_strength = row
        heroes[name] = {
            "role": role,
            "archetypes": set(archetypes),
            "counters": set(counters),
            "countered_by": set(countered_by),
            "meta_strength": meta_strength,
        }

    cursor.close()
    conn.close()
    return heroes


def load_compositions_from_db():
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