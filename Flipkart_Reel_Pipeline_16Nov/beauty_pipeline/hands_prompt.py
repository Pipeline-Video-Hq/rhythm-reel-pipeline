"""Hand and arm clause for hands-only close-up frame prompts (user 2026-11-06, ID 4 S4: both forearms entered from the same corner and crossed).
Usage:  python3 hands_prompt.py <hold> [hand]     hold in {pinch, wrap, flat_palm, two_hand_grip, fan, tilt_up}, hand in {right, left} (default right)
        from python: from hands_prompt import hands_clause
Print the clause and paste it into EVERY close-up frame prompt. It names which hand holds the product, which edge each forearm enters from,
and what the other hand does, so the model cannot put both arms in one corner or cross them."""
import sys

HOLDS = {
    "pinch": "pinched between the thumb and first two fingers at the edges, label facing the camera",
    "wrap": "gripped by the fingers wrapped around the middle of the body (bottle or tube upright), label facing the camera",
    "flat_palm": "resting flat on the open palm held palm-up with the fingers slightly curled (only for flat light items)",
    "two_hand_grip": "held in both hands, a hand at each side, label facing the camera",
    "fan": "fanned like cards between the thumb and fingers of both hands",
    "tilt_up": "held between thumb and fingers, tilted slightly toward the light, label facing the camera",
}


def hands_clause(hold, hand="right"):
    other = "left" if hand == "right" else "right"
    side = "bottom-right" if hand == "right" else "bottom-left"
    oside = "bottom-left" if hand == "right" else "bottom-right"
    if hold in ("two_hand_grip", "fan"):
        return (f"HANDS: exactly two hands of one person. Her left forearm enters from the bottom-left corner and her right forearm enters from the bottom-right "
                f"corner, they come up and meet in front of the product without crossing, both elbows pointing down and outward, the product {HOLDS[hold]}. "
                "Both wrists and forearms are visible and continuous down to the frame edge, same skin tone, same sleeve and the same bangle or none on both wrists.")
    return (f"HANDS: exactly two hands of one person, anatomically correct. Her {hand} hand holds the product {HOLDS[hold]}; its forearm enters from the {side} corner of the frame "
            f"and rises up toward the product (the wrist and the forearm are continuous down to the frame edge). Her {other} hand is either completely out of frame or its forearm enters from the "
            f"separate {oside} corner and rests relaxed on the table surface beside the product, never from the same corner, never crossing the other arm. "
            "Same skin tone, same sleeve and the same bangle or none on both wrists.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in HOLDS:
        sys.exit("Usage: python3 hands_prompt.py <" + "|".join(HOLDS) + "> [right|left]")
    print(hands_clause(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "right"))
