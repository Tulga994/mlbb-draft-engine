from db_loader import load_heroes_from_db, load_compositions_from_db

HEROES = load_heroes_from_db()  # pulls all 40 heroes from Neon at startup
COMPOSITIONS = load_compositions_from_db()  # pulls all 9 compositions from Neon at startup

WEIGHTS = {
    "early": {"flex": 3.0, "counter": 1.0, "synergy": 0.5, "role_need": 1.0, "comp_fit": 0.0, "meta": 1.0},
    "mid": {"flex": 1.0, "counter": 2.0, "synergy": 1.5, "role_need": 1.5, "comp_fit": 2.0, "meta": 0.5},
    "late": {"flex": 0.2, "counter": 2.0, "synergy": 1.0, "role_need": 2.5, "comp_fit": 2.5, "meta": 0.3},
}

TURN_STRUCTURE = [1, 2, 2, 2, 2, 1]


def predict_composition(ally_picks):
    if not ally_picks:
        return None, set()

    covered = set()  # covered is what archetypes we already have and we use it to check what we are missing
    for hero in ally_picks:  # loops that runs for each hero, checks archetypes to add to covered
        covered |= HEROES[hero]["archetypes"]

    best_comp, best_score = None, 0.0
    for comp_name, signature in COMPOSITIONS.items():  # checks each known comp one at a time
        score = len(signature & covered) / len(
            signature)  # check overlaps to see what we have out of the comp signatures
        if score > best_score:  # only the highest score comp is returned so its being compared here
            best_comp, best_score = comp_name, score

    if best_comp is None:
        return None, set()

    missing = COMPOSITIONS[best_comp] - covered
    return best_comp, missing  # returned the highest scored comp with what tags are missing


def score_hero(hero_name, ally_picks, enemy_picks, phase):  # gets called for every candidate by recommend_picks
    hero = HEROES[hero_name]
    w = WEIGHTS[phase]

    flex_score = 1.0 if len(hero["countered_by"]) == 0 else 0.0  # 1 if hero isnt countered by anything, else 0
    counter_score = len(hero["counters"] & set(enemy_picks))  # which of the enemy heroes does this hero counter

    ally_tags = set()  # every archetype tag our own picks already have
    for h in ally_picks:
        for t in HEROES[h]["archetypes"]:
            ally_tags.add(t)
    synergy_score = len(hero["archetypes"] & ally_tags)  # how many tags this candidate shares with our team so far

    have_roles = {HEROES[h]["role"] for h in ally_picks}  # set of roles we've already picked
    role_need_score = 1.0 if hero["role"] not in have_roles else 0.0  # 1 if this hero fills a role we don't have yet

    target_comp, missing_tags = predict_composition(ally_picks)  # see what comp we're building
    comp_fit_score = len(hero["archetypes"] & missing_tags)  # hero's tags cover any of what that comp still needs?

    meta_score = hero["meta_strength"] / 10

    return (
            w["flex"] * flex_score
            + w["counter"] * counter_score
            + w["synergy"] * synergy_score
            + w["role_need"] * role_need_score
            + w["comp_fit"] * comp_fit_score
            + w["meta"] * meta_score
    )


def recommend_picks(ally_picks, enemy_picks, phase):
    available = []  # will hold every hero name that's still pickable
    for h in HEROES:  # loops over every hero that exists in the database
        if h not in ally_picks and h not in enemy_picks:  # skip it if either side already took it
            available.append(h)

    scored = []  # will hold (hero_name, score) pairs so we don't lose track of which score belongs to which hero
    for h in available:
        result = score_hero(h, ally_picks, enemy_picks, phase)  # run the actual scoring logic on this one candidate
        scored.append((h, result))

    # sort
    for i in range(len(scored)):
        for j in range(len(scored) - 1):
            if scored[j][1] < scored[j + 1][1]:
                scored[j], scored[j + 1] = scored[j + 1], scored[j]

    return scored


def get_turn_team(turn_index):  # whose turn to pick
    return "ally" if turn_index % 2 == 0 else "enemy"  # ally goes on even turns, enemy on odd turns


def get_phase(pick_number, total_picks=5):  # at what draft phase we are at
    if pick_number <= max(1, total_picks // 3):
        return "early"
    elif pick_number <= max(2, (total_picks * 2) // 3):
        return "mid"
    return "late"


def find_hero(name_input, available):  # if name entered differently this will try to find
    normalized = name_input.strip().lower().replace(" ", "_")
    for h in available:
        if h.lower() == normalized:
            return h
    return None  # no match found, caller will ask again


def ask_for_hero(prompt_text, available):
    while True:  # keep asking until we get something valid
        raw = input(prompt_text)
        match = find_hero(raw, available)
        if match is not None:
            return match
        print(f"  Couldn't match '{raw}' to an available hero. Try again.")


def run_draft():
    ally_picks = []
    enemy_picks = []

    for turn_index, picks_this_turn in enumerate(TURN_STRUCTURE):  # pair value with its pos
        team = get_turn_team(turn_index)

        for pick_count in range(picks_this_turn):
            available = []
            for h in HEROES:
                if h not in ally_picks and h not in enemy_picks:
                    available.append(h)

            if team == "ally":
                phase = get_phase(len(ally_picks) + 1)
                ranked = recommend_picks(ally_picks, enemy_picks, phase)
                print(f"\n--- Turn {turn_index + 1} [{phase.upper()}] YOUR PICK ---")
                print("Top recommendations:")
                for i, (hero_name, score) in enumerate(ranked[:5], start=1):
                    print(f"  {i}. {hero_name}  (score {score:.2f})")
                picked = ask_for_hero("Enter the hero you're locking in: ", available)
                ally_picks.append(picked)

            else:
                print(f"\n--- Turn {turn_index + 1} ENEMY PICK ---")
                picked = ask_for_hero("Enter what the enemy just picked: ", available)
                enemy_picks.append(picked)

    print("\nFinal ally team:", ally_picks)
    print("Final enemy team:", enemy_picks)

    final_comp, final_missing = predict_composition(ally_picks)
    print(f"Final predicted comp: {final_comp} | still missing tags: {final_missing}")


run_draft()
