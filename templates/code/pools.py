"""Optional: spare pictures per story section, used when a block runs longer than the pictures its VISUAL line names
(each picture is used once per block, so a long block needs more). Without this file the act's own clips are the spare pool.

Rules: only vetted material; a located photo stays with its own subject (never in a pool for another place);
generic stock stays generic. Order matters: earlier entries are used first.
"""

NIGHT = ["px:000000"]
TOWN = ["photo:place#0", "photo:place#1"]

POOLS = {"open": NIGHT, "main": TOWN + NIGHT, "closing": TOWN}


def section(block):
    """which pool a V.O. block draws from. block = {"id", "act", "lines": [ids], "start", "end"}."""
    if block["act"] == "COLD OPEN":
        return "open"
    if block["act"] == "CLOSING":
        return "closing"
    return "main"
