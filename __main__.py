from src import process
from src.field import SBField
from src.net import Network


def main():
    net = Network()

    # Step 1: Initialize Network Connection
    net_mode = process.init()
    if net_mode == "s":
        ip = net.get_local_ip()
        print(f"📡 Hosting server on {ip}:{net.port}...")
        client_addr = net.start_server()
        print(f"✅ Client connected from: {client_addr[0]}")
    else:
        ip, port = process.get_ip()
        print(f"📡 Connecting to server {ip}:{port}...")
        net.connect(ip, port)
        print("✅ Successfully connected to server!")

    # Step 2: Main Match Loop (Supports Rematches)
    while True:
        my_field = SBField()
        opponent_field = SBField(mode="opponent")

        # Fleet Placement
        process.fill_my_field(my_field)

        # Readiness Sync
        net.reset_ready()
        if not net.wait_for_opponent():
            break

        # Gameplay
        process.game(my_field, opponent_field, net, net_mode)

        # Rematch Prompt
        if not process.ask_rematch(net):
            break


if __name__ == "__main__":
    main()
