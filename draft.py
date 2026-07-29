from scoring import HEROES, COMPOSITION_COUNTERS, recommend_picks, predict_composition

TURN_STRUCTURE = [1, 2, 2, 2, 2, 1]


def get_turn_team(turn_index, ally_first):  # whose turn to pick
    is_even_turn = turn_index % 2 == 0
    if ally_first:
        return "ally" if is_even_turn else "enemy"  # ally on even turns, enemy on odd
    else:
        return "enemy" if is_even_turn else "ally"  # flipped -- enemy on even turns, ally on odd


def get_phase(pick_number, total_picks=5):  # at what draft phase we are at
    if pick_number <= max(1, total_picks // 3):
        return "early"
    elif pick_number <= max(2, (total_picks * 2) // 3):
        return "mid"
    return "late"


ALL_LANES = ["EXP", "Jungle", "Mid", "Gold", "Roam"]  # the 5 actual positions a team needs, one hero each


def print_role_tracker(ally_picks):
    filled = {lane: [] for lane in ALL_LANES}  # start every lane empty
    for h in ally_picks:
        filled[HEROES[h]["lane"]].append(h)  # sort each pick into its lane bucket, not its role type

    print("Your squad so far:")
    for lane in ALL_LANES:
        heroes_in_lane = filled[lane]
        status = ", ".join(heroes_in_lane) if heroes_in_lane else "-- empty --"
        print(f"  {lane:8s}: {status}")

    missing = [lane for lane in ALL_LANES if not filled[lane]]
    if missing:
        print(f"Still missing: {', '.join(missing)}")
    else:
        print("All 5 lanes covered.")


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

    first_side = input("Does your team pick first this draft? (y/n): ").strip().lower()
    ally_first = first_side in ("y", "yes")  # anything else counts as "no"

    for turn_index, picks_this_turn in enumerate(TURN_STRUCTURE):  # pair value with its pos
        team = get_turn_team(turn_index, ally_first)

        for pick_count in range(picks_this_turn):
            available = []
            for h in HEROES:
                if h not in ally_picks and h not in enemy_picks:
                    available.append(h)

            if team == "ally":
                phase = get_phase(len(ally_picks) + 1)
                print()
                print_role_tracker(ally_picks)  # show current squad + missing roles before recommending

                enemy_comp, enemy_missing = predict_composition(enemy_picks)
                if enemy_comp:
                    print(f"Enemy appears to be building: {enemy_comp} (still missing: {enemy_missing})")
                else:
                    print("Enemy comp not clear yet.")

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

    print("\n=== FINAL RESULT ===")
    print_role_tracker(ally_picks)
    print("Final enemy team:", enemy_picks)

    final_comp, final_missing = predict_composition(ally_picks)
    print(f"Final predicted comp: {final_comp} | still missing tags: {final_missing}")


def show_info_menu():
    while True:
        print("\n=== INFO MENU ===")
        print("1. Look up a hero's counters")
        print("2. List all heroes by lane")
        print("3. List composition matchups")
        print("4. Back")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            all_names = list(HEROES.keys())
            name_input = input("Hero name: ").strip()
            match = find_hero(name_input, all_names)
            if match is None:
                print(f"  Couldn't find a hero matching '{name_input}'.")
                continue
            hero = HEROES[match]
            print(f"\n{match} -- {hero['role']}, {hero['lane']} lane, meta_strength {hero['meta_strength']}/10")
            counters_str = ", ".join(hero["counters"]) if hero["counters"] else "none listed"
            countered_by_str = ", ".join(hero["countered_by"]) if hero["countered_by"] else "none listed"
            print(f"  Counters: {counters_str}")
            print(f"  Countered by: {countered_by_str}")

        elif choice == "2":
            for lane in ALL_LANES:
                heroes_in_lane = [h for h in HEROES if HEROES[h]["lane"] == lane]
                print(f"{lane:8s}: {', '.join(heroes_in_lane)}")

        elif choice == "3":
            print("\nComposition matchups (left beats right):")
            for comp, beats in COMPOSITION_COUNTERS.items():
                print(f"  {comp:20s} beats: {', '.join(beats)}")

        elif choice == "4":
            break

        else:
            print("  Not a valid option, try again.")


def main():
    print("=== MLBB Draft Engine ===")
    choice = input("Do you want (1) Info or (2) Start Drafting? ").strip()
    if choice == "1":
        show_info_menu()
        again = input("\nStart drafting now? (y/n): ").strip().lower()
        if again in ("y", "yes"):
            run_draft()
    else:
        run_draft()


main()