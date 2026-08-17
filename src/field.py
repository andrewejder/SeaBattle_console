FIELD_LENGTH = 10


class FieldStatus:
    free = 0
    range_of_ship = 1
    ship = 2
    hit = 3
    kill = 4
    ship_radius = 5


class SBField:
    """Class representing a Battleship game board."""

    def __init__(self, mode: str = "me"):
        self._mode = mode  # "me" or "opponent"
        self.field = [
            [FieldStatus.free for _ in range(FIELD_LENGTH)]
            for _ in range(FIELD_LENGTH)
        ]
        self.placed_ships = []
        self._max_ships = {1: 4, 2: 3, 3: 2, 4: 1}

    def place_ship(self, x: int, y: int, r: int, length: int) -> bool:
        """Place a ship on the field if position is valid.

        :param x: Column index (0..9)
        :param y: Row index (0..9)
        :param r: Rotation (0 - horizontal, 1 - vertical)
        :param length: Ship length (1..4)
        :return: Success status (bool)
        """
        # Check ship quantity limits
        current_count = sum(1 for s in self.placed_ships if s["len"] == length)
        if current_count >= self._max_ships.get(length, 0):
            return False

        # Calculate ship cell coordinates
        ship_cells = []
        for i in range(length):
            cx = x + i * (1 - r)
            cy = y + i * r
            if not (0 <= cx < FIELD_LENGTH and 0 <= cy < FIELD_LENGTH):
                return False
            ship_cells.append((cy, cx))

        # Calculate halo (surrounding) cell coordinates
        halo_cells = set()
        for cy, cx in ship_cells:
            for _r in range(cy - 1, cy + 2):
                for _c in range(cx - 1, cx + 2):
                    if 0 <= _r < FIELD_LENGTH and 0 <= _c < FIELD_LENGTH:
                        if (_r, _c) not in ship_cells:
                            halo_cells.add((_r, _c))

        # Check for collisions
        for cy, cx in ship_cells:
            if self.field[cy][cx] != FieldStatus.free:
                return False
        for cy, cx in halo_cells:
            if self.field[cy][cx] == FieldStatus.ship:
                return False

        # Apply ship and halo to field
        _f_check = [row.copy() for row in self.field]
        for cy, cx in halo_cells:
            if _f_check[cy][cx] == FieldStatus.free:
                _f_check[cy][cx] = FieldStatus.range_of_ship

        for cy, cx in ship_cells:
            _f_check[cy][cx] = FieldStatus.ship

        self.placed_ships.append(
            {
                "len": length,
                "cells": ship_cells,
                "halo": list(halo_cells),
                "hits": set(),
            }
        )

        self.field = [row.copy() for row in _f_check]
        return True

    def make_shoot(self, x: int, y: int) -> bool:
        """Process a shot at target coordinates.

        :param x: Column index (0..9)
        :param y: Row index (0..9)
        :return: True if hit/destroyed, False if missed or already shot
        """
        if not (0 <= x < FIELD_LENGTH and 0 <= y < FIELD_LENGTH):
            return False

        target = self.field[y][x]

        if target in (
            FieldStatus.hit,
            FieldStatus.kill,
            FieldStatus.ship_radius,
        ):
            return False

        if target == FieldStatus.ship:
            self.field[y][x] = FieldStatus.hit
            for ship in self.placed_ships:
                if (y, x) in ship["cells"]:
                    ship["hits"].add((y, x))
                    # Check if ship is destroyed
                    if len(ship["hits"]) == ship["len"]:
                        for cy, cx in ship["cells"]:
                            self.field[cy][cx] = FieldStatus.kill
                        for cy, cx in ship["halo"]:
                            if self.field[cy][cx] != FieldStatus.kill:
                                self.field[cy][cx] = FieldStatus.ship_radius
            return True
        else:
            self.field[y][x] = FieldStatus.ship_radius
            return False

    def is_lost(self) -> bool:
        """Check if all ships on the board are destroyed."""
        return not any(FieldStatus.ship in row for row in self.field)
