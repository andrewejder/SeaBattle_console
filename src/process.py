import ipaddress
import random

from src.field import FIELD_LENGTH

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def init() -> str:
    """Prompt mode selection."""
    print("========================================")
    print("        🚢 BATTLESHIP NETWORK 🚢        ")
    print("========================================")
    while True:
        mode = input("Select mode - Server (s) or Client (c): ").strip().lower()
        if mode in ("s", "c"):
            return mode


def get_ip():
    """Prompt and validate server connection address."""
    while True:
        user_input = input(
            "Enter Server IP and Port (e.g., 192.168.1.5:8080): "
        ).strip()

        if ":" not in user_input:
            print("❌ Invalid format! Please use IP:PORT")
            continue

        ip_str, port_str = user_input.rsplit(":", 1)

        if not port_str.isdigit():
            print("❌ Port must be numeric!")
            continue

        port = int(port_str)
        if not (1 <= port <= 65535):
            print("❌ Port must be between 1 and 65535!")
            continue

        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            print(f"❌ Invalid IP address: '{ip_str}'")
            continue

        return str(ip), port


def fill_my_field_auto(field):
    """Randomly place all fleet ships."""
    ships_to_place = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    for ship_len in ships_to_place:
        placed = False
        attempts = 0
        while not placed:
            x = random.randint(0, FIELD_LENGTH - 1)
            y = random.randint(0, FIELD_LENGTH - 1)
            r = random.randint(0, 1)

            placed = field.place_ship(x, y, r, ship_len)
            attempts += 1

            if attempts > 500:
                field.field = [
                    [0 for _ in range(FIELD_LENGTH)]
                    for _ in range(FIELD_LENGTH)
                ]
                field.placed_ships = []
                fill_my_field_auto(field)


def fill_my_field(field):
    """Setup player fleet via manual or auto placement."""
    while True:
        choice = (
            input("Auto-place ships randomly? (y/n): ").strip().lower()
        )
        if choice in ("y", "n"):
            break

    if choice == "y":
        fill_my_field_auto(field)
        print("\n✅ Fleet deployed automatically!")
        return

    ships_to_place = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    for ship_len in ships_to_place:
        while True:
            print_single_field(field)
            user_input = (
                input(
                    f"Place {ship_len}-deck ship (e.g., 'A1 h' or 'C5 v'): "
                )
                .strip()
                .lower()
            )
            parts = user_input.split()

            if len(parts) != 2:
                print(
                    "❌ Format error! Enter position and rotation (e.g. A1 h)"
                )
                continue

            pos, rot = parts[0], parts[1]

            if rot in ("h", "0"):
                r = 0
            elif rot in ("v", "1"):
                r = 1
            else:
                print("❌ Rotation must be 'h' (horizontal) or 'v' (vertical)!")
                continue

            col_letter = pos[0].upper()
            row_str = pos[1:]

            if col_letter not in LETTERS or not row_str.isdigit():
                print("❌ Invalid coordinate! Use format like A1, B10, J5.")
                continue

            x = LETTERS.index(col_letter)
            y = int(row_str) - 1

            if field.place_ship(x, y, r, ship_len):
                print(f"⚓ {ship_len}-deck ship deployed!")
                break
            else:
                print("❌ Invalid position! Out of bounds or collision.")

    print("\n✅ Fleet successfully deployed!")


def print_single_field(field):
    """Render single field during setup."""
    symbols = {0: "·", 1: "▪", 2: "■", 3: "×", 4: "X", 5: "▪"}
    print("\n    " + "  ".join(LETTERS))
    for n, row in enumerate(field.field):
        row_str = "  ".join(symbols.get(v, str(v)) for v in row)
        print(f"{n + 1:>2}  {row_str}")
    print()


def parse_coords(user_input: str):
    """Parse string coordinates into (x, y) tuple."""
    user_input = user_input.strip().upper()
    if len(user_input) < 2:
        return None
    col_letter = user_input[0]
    row_str = user_input[1:]

    if col_letter not in LETTERS or not row_str.isdigit():
        return None

    x = LETTERS.index(col_letter)
    y = int(row_str) - 1

    if 0 <= x < FIELD_LENGTH and 0 <= y < FIELD_LENGTH:
        return x, y
    return None


def print_boards(my_field, opponent_field):
    """Side-by-side rendering of both player fields."""
    print("\n        🌊 YOUR FLEET 🌊                🎯 OPPONENT BOARD 🎯")
    print("    " + "  ".join(LETTERS) + "        " + "  ".join(LETTERS))

    symbols_me = {0: "·", 1: "▪", 2: "■", 3: "×", 4: "X", 5: "▪"}
    symbols_opp = {0: "·", 1: "·", 2: "·", 3: "×", 4: "X", 5: "▪"}

    for n in range(FIELD_LENGTH):
        my_row = "  ".join(symbols_me.get(v, str(v)) for v in my_field.field[n])
        opp_row = "  ".join(
            symbols_opp.get(v, str(v)) for v in opponent_field.field[n]
        )
        print(f"{n + 1:>2}  {my_row}    {n + 1:>2}  {opp_row}")
    print()


def game(my_field, opponent_field, net, net_mode):
    """Main battle loop."""
    print("🔄 Synchronizing boards with opponent...")
    net.send_data((my_field.field, my_field.placed_ships))
    opp_data = net.recv_data()

    if not opp_data:
        print("❌ Opponent disconnected during setup.")
        return

    opponent_field.field = opp_data[0]
    opponent_field.placed_ships = opp_data[1]
    print("⚔️ Battle starts now!\n")

    my_turn = net_mode == "s"

    while True:
        print_boards(my_field, opponent_field)

        if my_field.is_lost():
            print("☠️ DEFEAT! All your ships were destroyed!")
            break
        if opponent_field.is_lost():
            print("🏆 VICTORY! You destroyed the enemy fleet!")
            break

        if my_turn:
            print("👉 YOUR TURN!")
            user_input = input("Enter fire target (e.g. A5): ")
            coords = parse_coords(user_input)

            if not coords:
                print("❌ Invalid input format! Try again.")
                continue

            x, y = coords
            if opponent_field.field[y][x] in (3, 4, 5):
                print("⚠️ Cell already targeted! Choose another cell.")
                continue

            is_hit = opponent_field.make_shoot(x, y)
            net.send_data((x, y))

            if is_hit:
                print("💥 DIRECT HIT! You fire again.")
            else:
                print("💦 MISS! Turn passes to opponent.")
                my_turn = False

        else:
            print("⏳ Waiting for opponent's strike...")
            coords = net.recv_data()
            if not coords:
                print("🔌 Opponent disconnected.")
                break

            ox, oy = coords
            is_hit = my_field.make_shoot(ox, oy)
            shot_letter = LETTERS[ox]
            shot_num = oy + 1

            if is_hit:
                print(
                    f"💥 Opponent struck {shot_letter}{shot_num} and HIT your ship!"
                )
            else:
                print(f"🛡️ Opponent struck {shot_letter}{shot_num} and MISSED!")
                my_turn = True


def ask_rematch(net) -> bool:
    """Synchronize rematch request between players."""
    while True:
        choice = (
            input("\n🔄 Would you like to play again? (y/n): ").strip().lower()
        )
        if choice in ("y", "n"):
            break

    net.send_data(choice)
    print("⏳ Waiting for opponent's decision...")
    opp_choice = net.recv_data()

    if choice == "y" and opp_choice == "y":
        print("\n🎉 Both players agreed! Restarting match...\n")
        return True
    else:
        print("\n👋 Match ended. Thanks for playing!")
        return False
