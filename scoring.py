from db_loader import load_heroes_from_db, load_compositions_from_db

HEROES = load_heroes_from_db()  # pulls all 40 heroes from Neon at startup
COMPOSITIONS = load_compositions_from_db()  # pulls all 9 compositions from Neon at startup

# Directed: key comp is considered strong against every comp in its value set.
# This is a judgment call about MLBB strategy, not a scraped/verified fact --
# treat it as a starting draft to correct from your own competitive experience.
COMPOSITION_COUNTERS = {
    "dive_burst": {"protect_the_carry", "poke_siege"},
    "protect_the_carry": {"split_push", "sustain_grind"},
    "poke_siege": {"all_in_lockdown", "five_man_teamfight"},
    "split_push": {"five_man_teamfight", "all_in_lockdown"},
    "five_man_teamfight": {"pick_off_burst", "sustain_grind"},
    "pick_off_burst": {"protect_the_carry", "poke_siege"},
    "sustain_grind": {"pick_off_burst", "dive_burst"},
    "all_in_lockdown": {"dive_burst", "pick_off_burst"},
    "anti_tank_execute": {"sustain_grind", "all_in_lockdown"},
}

WEIGHTS = {
    "early": {"flex": 3.0, "counter": 1.0, "synergy": 0.5, "role_need": 1.0, "comp_fit": 0.0, "meta": 1.0,
              "comp_counter": 0.0},
    "mid": {"flex": 1.0, "counter": 2.0, "synergy": 1.5, "role_need": 1.5, "comp_fit": 2.0, "meta": 0.5,
            "comp_counter": 1.5},
    "late": {"flex": 0.2, "counter": 2.0, "synergy": 1.0, "role_need": 2.5, "comp_fit": 2.5, "meta": 0.3,
             "comp_counter": 2.0},
}


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

    have_lanes = {HEROES[h]["lane"] for h in ally_picks}  # which of the 5 lanes are already taken
    lane_need_score = 1.0 if hero["lane"] not in have_lanes else 0.0  # 1 if this hero fills an empty lane

    target_comp, missing_tags = predict_composition(ally_picks)  # see what comp we're building
    comp_fit_score = len(hero["archetypes"] & missing_tags)  # hero's tags cover any of what that comp still needs?

    enemy_comp, _ = predict_composition(enemy_picks)  # what comp is the enemy building?
    hypothetical_picks = ally_picks + [hero_name]  # what if we added this hero to our team?
    our_comp_if_picked, _ = predict_composition(hypothetical_picks)
    if enemy_comp is not None and our_comp_if_picked is not None and enemy_comp in COMPOSITION_COUNTERS.get(
            our_comp_if_picked, set()):
        comp_counter_score = 1.0  # picking this hero would push us toward a comp that beats theirs
    else:
        comp_counter_score = 0.0

    meta_score = hero["meta_strength"] / 10

    return (
            w["flex"] * flex_score
            + w["counter"] * counter_score
            + w["synergy"] * synergy_score
            + w["role_need"] * lane_need_score
            + w["comp_fit"] * comp_fit_score
            + w["comp_counter"] * comp_counter_score
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
