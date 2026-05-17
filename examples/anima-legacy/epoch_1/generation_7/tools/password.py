#!/usr/bin/env python3
"""
password.py — Password & passphrase generator. Zero dependencies.

Usage:
  python3 password.py                    # 16-char password
  python3 password.py -n 24              # 24-char password
  python3 password.py -w 5               # 5-word passphrase
  python3 password.py -c 10              # Generate 10 passwords
  python3 password.py --no-symbols       # Letters + digits only
  python3 password.py --pin 6            # 6-digit PIN
  python3 password.py -w 4 --sep .       # Passphrase with dot separator
  python3 password.py --check "MyP@ss1"  # Check password strength
"""

import secrets
import string
import argparse
import math
import sys

# Wordlist: 1024 common English words (3-6 chars) → exactly 10 bits/word
WORDLIST = [
    "acid", "acme", "acre", "aged", "aide", "also", "arch", "area",
    "army", "atom", "aunt", "auto", "avid", "axis", "back", "bail",
    "bait", "bake", "ball", "band", "bank", "bare", "bark", "barn",
    "base", "bath", "bead", "beam", "bean", "bear", "beat", "beef",
    "been", "beer", "bell", "belt", "bend", "best", "bike", "bill",
    "bind", "bird", "bite", "blade", "blank", "blast", "blaze", "bleed",
    "blend", "bless", "blind", "block", "blood", "bloom", "blown", "blow",
    "blue", "blur", "board", "boat", "body", "bold", "bolt", "bomb",
    "bond", "bone", "book", "boost", "boot", "bore", "born", "boss",
    "both", "bound", "bowl", "brain", "brand", "brave", "bread", "break",
    "breed", "brick", "bride", "brief", "bring", "broad", "broke", "brook",
    "brown", "brush", "build", "built", "bulk", "bump", "bunch", "burn",
    "burst", "bush", "busy", "cabin", "cable", "cafe", "cage", "cake",
    "calm", "came", "camp", "candy", "cape", "card", "care", "carry",
    "cart", "case", "cash", "cast", "catch", "cause", "cave", "cease",
    "chain", "chair", "chalk", "charm", "chart", "chase", "cheap", "check",
    "cheek", "chef", "chess", "chest", "chief", "child", "chill", "chin",
    "chip", "choir", "chop", "chunk", "cite", "city", "civil", "clad",
    "claim", "clap", "clash", "class", "clay", "clean", "clear", "clerk",
    "click", "cliff", "climb", "cling", "clip", "clock", "clone", "close",
    "cloth", "cloud", "club", "clue", "coach", "coal", "coast", "coat",
    "code", "coil", "coin", "cold", "cone", "cook", "cool", "cope",
    "copy", "cord", "core", "corn", "cost", "couch", "could", "count",
    "court", "cover", "cozy", "crack", "craft", "crane", "crash", "crazy",
    "cream", "crew", "crime", "crisp", "crop", "cross", "crowd", "crown",
    "crude", "crush", "cube", "curb", "cure", "curl", "curve", "cute",
    "cycle", "daily", "dairy", "dale", "dame", "damp", "dance", "dare",
    "dark", "dart", "data", "dawn", "deal", "dear", "death", "debt",
    "decay", "deck", "deed", "deep", "deer", "delay", "delta", "demo",
    "dense", "deny", "depth", "derby", "desk", "devil", "dial", "diary",
    "dice", "diet", "digit", "dirt", "disc", "dish", "dock", "dodge",
    "doing", "dome", "done", "donor", "doom", "door", "dose", "doubt",
    "dough", "dove", "down", "draft", "drag", "drain", "drama", "drank",
    "draw", "drawn", "dream", "dress", "drew", "dried", "drift", "drill",
    "drink", "drip", "drive", "drop", "drove", "drum", "drunk", "dual",
    "dude", "duke", "dull", "dump", "dune", "dusk", "dust", "dusty",
    "duty", "dwarf", "each", "eager", "eagle", "earl", "earn", "earth",
    "ease", "east", "eaten", "echo", "edge", "edit", "eight", "elder",
    "elect", "elite", "elbow", "empty", "enemy", "enjoy", "enter", "entry",
    "epic", "equal", "equip", "error", "essay", "ethic", "even", "event",
    "every", "exact", "exam", "exile", "exist", "exit", "exotic", "extra",
    "eyed", "fable", "face", "fact", "fade", "fail", "faint", "fair",
    "fairy", "faith", "fake", "fall", "false", "fame", "fancy", "fang",
    "fare", "farm", "fast", "fatal", "fate", "fault", "favor", "fear",
    "feast", "feat", "feed", "feel", "feet", "fell", "felt", "fence",
    "fern", "ferry", "fever", "fiber", "field", "fifth", "fifty", "fight",
    "file", "fill", "film", "final", "find", "fine", "fire", "firm",
    "first", "fish", "fist", "five", "fixed", "flag", "flame", "flash",
    "flat", "fled", "fleet", "flesh", "flew", "flies", "flood", "floor",
    "flour", "flow", "fluid", "flush", "foam", "focal", "focus", "fold",
    "folk", "font", "food", "fool", "foot", "force", "forge", "form",
    "forth", "forum", "found", "four", "fox", "frame", "frank", "fraud",
    "free", "fresh", "fried", "front", "frost", "froze", "fruit", "fuel",
    "fully", "fun", "fund", "funny", "fury", "fuse", "gain", "gale",
    "gang", "gap", "gaze", "gear", "gem", "gene", "genre", "ghost",
    "giant", "gift", "given", "glad", "gland", "glass", "gleam", "globe",
    "gloom", "glory", "glove", "glow", "glue", "goal", "goat", "going",
    "gold", "golf", "gone", "good", "grace", "grade", "grain", "grand",
    "grant", "grasp", "grass", "grave", "great", "green", "greet", "grew",
    "grief", "grill", "grin", "grind", "grip", "gross", "group", "grove",
    "grow", "grown", "guard", "guess", "guest", "guide", "guild", "guilt",
    "guru", "habit", "half", "hall", "halt", "hand", "happy", "hard",
    "harm", "harsh", "haste", "hat", "hate", "haul", "haven", "hawk",
    "heal", "heap", "heard", "heart", "heat", "heavy", "hedge", "heel",
    "held", "hello", "hence", "herb", "hero", "hike", "hill", "hint",
    "hip", "hire", "hold", "hole", "holy", "home", "honey", "honor",
    "hood", "hook", "hope", "horn", "horse", "host", "hotel", "hour",
    "house", "hover", "human", "humor", "hung", "hunt", "hurry", "hurt",
    "idea", "ideal", "image", "index", "indie", "inner", "input", "irony",
    "issue", "ivory", "jewel", "join", "joint", "joke", "jolly", "joy",
    "judge", "juice", "jump", "just", "keen", "keep", "kept", "kick",
    "kind", "king", "kiss", "knack", "kneel", "knelt", "knew", "knife",
    "knit", "knock", "knot", "known", "label", "labor", "lace", "lack",
    "laid", "lake", "lamp", "land", "lane", "large", "laser", "last",
    "late", "later", "laugh", "lawn", "layer", "lead", "leaf", "lean",
    "learn", "lease", "least", "left", "legal", "lemon", "lend", "lens",
    "level", "lever", "light", "like", "limb", "limit", "line", "link",
    "lion", "list", "live", "liver", "load", "loan", "local", "lock",
    "lodge", "logic", "lone", "long", "look", "lord", "lose", "lost",
    "loud", "love", "lover", "loyal", "luck", "lunar", "lunch", "lure",
    "lying", "mad", "made", "magic", "maid", "main", "major", "maker",
    "male", "mall", "manor", "many", "map", "march", "mark", "marry",
    "marsh", "mask", "mass", "match", "mate", "math", "mayor", "meal",
    "mean", "medal", "media", "meet", "mercy", "mere", "merge", "merit",
    "mesh", "metal", "midst", "mild", "milk", "mill", "mind", "mine",
    "minor", "minus", "miss", "mix", "moat", "model", "moist", "mold",
    "money", "month", "mood", "moon", "moral", "more", "moss", "most",
    "motor", "mount", "mouse", "mouth", "move", "movie", "much", "mud",
    "mural", "music", "must", "myth", "nail", "name", "navy", "near",
    "neat", "neck", "need", "nerve", "nest", "never", "next", "nice",
    "night", "nine", "noble", "node", "noise", "none", "norm", "north",
    "nose", "note", "novel", "nurse", "nylon", "oak", "occur", "ocean",
    "odds", "offer", "often", "olive", "once", "onset", "open", "opera",
    "opted", "orbit", "order", "organ", "other", "ought", "outer", "owner",
    "oxide", "pace", "pack", "paid", "pain", "pair", "pale", "palm",
    "panel", "panic", "paper", "park", "party", "past", "paste", "patch",
    "path", "pause", "peace", "peach", "peak", "pearl", "pen", "penny",
    "perch", "piano", "pick", "piece", "pilot", "pine", "pink", "pipe",
    "pitch", "place", "plain", "plan", "plane", "plant", "plate", "play",
    "plaza", "plead", "plum", "plumb", "plump", "plunge", "plus", "poem",
    "poet", "point", "polar", "pole", "poll", "pond", "pool", "poor",
    "pop", "porch", "pork", "port", "pose", "post", "pot", "pound",
    "pour", "power", "pray", "press", "price", "pride", "prime", "print",
    "prior", "prize", "probe", "proof", "prose", "proud", "prove", "pub",
    "pull", "pulse", "pump", "punch", "pupil", "pure", "purse", "push",
    "put", "queen", "quest", "quick", "quiet", "quilt", "quit", "quite",
    "quota", "quote", "race", "radar", "rage", "raid", "rail", "rain",
    "raise", "rally", "ramp", "ranch", "range", "rank", "rapid", "rare",
    "ratio", "raw", "reach", "read", "ready", "real", "realm", "rebel",
    "red", "reef", "refer", "reign", "relay", "rely", "renew", "rent",
    "reply", "reset", "rest", "rider", "ridge", "rifle", "right", "rigid",
    "ring", "riot", "rise", "risen", "risk", "rival", "river", "road",
    "robot", "rock", "rode", "role", "roll", "roman", "roof", "room",
    "root", "rope", "rose", "rough", "round", "route", "royal", "rude",
    "ruin", "rule", "ruler", "run", "rural", "rush", "sack", "sad",
    "safe", "saint", "sake", "sale", "salt", "same", "sand", "sauce",
    "save", "scale", "scan", "scare", "scene", "scent", "scope", "score",
    "scout", "sea", "seal", "seat", "seed", "seek", "seize", "self",
    "sell", "send", "sense", "serve", "set", "seven", "shade", "shaft",
    "shake", "shall", "shame", "shape", "share", "shark", "sharp", "shed",
    "sheer", "sheet", "shelf", "shell", "shift", "shine", "ship", "shirt",
    "shock", "shoe", "shoot", "shore", "short", "shot", "shout", "show",
    "shown", "shut", "sick", "side", "siege", "sight", "sign", "silk",
    "silly", "since", "sit", "site", "six", "sixth", "size", "skill",
    "skin", "skip", "skull", "slam", "slap", "slate", "slave", "sleep",
    "slept", "slice", "slide", "slim", "slip", "slope", "slow", "small",
    "smart", "smell", "smile", "smoke", "snap", "snow", "soak", "soap",
    "soar", "sock", "soft", "soil", "solar", "sole", "solid", "solve",
]  # exactly 1024 words → 10 bits/word

def generate_password(length=16, use_symbols=True):
    """Generate a random password."""
    chars = string.ascii_letters + string.digits
    if use_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure at least one of each required type
    password = []
    password.append(secrets.choice(string.ascii_uppercase))
    password.append(secrets.choice(string.ascii_lowercase))
    password.append(secrets.choice(string.digits))
    if use_symbols:
        password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

    # Fill the rest
    remaining = length - len(password)
    for _ in range(remaining):
        password.append(secrets.choice(chars))

    # Shuffle
    result = list(password)
    for i in range(len(result) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        result[i], result[j] = result[j], result[i]

    return ''.join(result)


def generate_passphrase(words=4, separator='-', capitalize=True):
    """Generate a random passphrase."""
    selected = [secrets.choice(WORDLIST) for _ in range(words)]
    if capitalize:
        selected = [w.capitalize() for w in selected]
    return separator.join(selected)


def generate_pin(length=4):
    """Generate a random PIN."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def calculate_entropy(password, mode='password', **kwargs):
    """Calculate password entropy in bits."""
    if mode == 'passphrase':
        word_count = kwargs.get('words', 4)
        return word_count * math.log2(len(WORDLIST))
    elif mode == 'pin':
        return len(password) * math.log2(10)
    else:
        # Estimate charset size from actual characters
        charset = 0
        has_lower = any(c in string.ascii_lowercase for c in password)
        has_upper = any(c in string.ascii_uppercase for c in password)
        has_digit = any(c in string.digits for c in password)
        has_symbol = any(c not in string.ascii_letters + string.digits for c in password)
        if has_lower: charset += 26
        if has_upper: charset += 26
        if has_digit: charset += 10
        if has_symbol: charset += 30
        return len(password) * math.log2(max(charset, 1))


def strength_label(entropy):
    """Human-readable strength label."""
    if entropy < 28: return "Very Weak"
    if entropy < 36: return "Weak"
    if entropy < 60: return "Moderate"
    if entropy < 80: return "Strong"
    if entropy < 100: return "Very Strong"
    return "Excellent"


def strength_bar(entropy, width=20):
    """Visual strength bar."""
    fill = min(int(entropy / 128 * width), width)
    return '█' * fill + '░' * (width - fill)


def main():
    parser = argparse.ArgumentParser(
        description='Password & passphrase generator — zero dependencies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python3 password.py              # 16-char password\n'
               '  python3 password.py -n 24         # 24-char password\n'
               '  python3 password.py -w 5          # 5-word passphrase\n'
               '  python3 password.py --pin 6       # 6-digit PIN\n'
               '  python3 password.py -c 5          # 5 passwords\n'
    )
    parser.add_argument('-n', '--length', type=int, default=16, help='Password length (default: 16)')
    parser.add_argument('-w', '--words', type=int, help='Generate passphrase with N words')
    parser.add_argument('--pin', type=int, metavar='N', help='Generate N-digit PIN')
    parser.add_argument('-c', '--count', type=int, default=1, help='Number to generate (default: 1)')
    parser.add_argument('--no-symbols', action='store_true', help='Exclude symbols')
    parser.add_argument('--sep', default='-', help='Passphrase separator (default: -)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Output only the password')
    parser.add_argument('--json', action='store_true', help='JSON output for scripting')
    parser.add_argument('--check', metavar='PW', help='Check strength of existing password')

    args = parser.parse_args()

    # Check mode
    if args.check:
        pw = args.check
        entropy = calculate_entropy(pw, mode='password')
        strength = strength_label(entropy)
        bar = strength_bar(entropy)

        # Detailed analysis
        has_lower = any(c in string.ascii_lowercase for c in pw)
        has_upper = any(c in string.ascii_uppercase for c in pw)
        has_digit = any(c in string.digits for c in pw)
        has_symbol = any(c not in string.ascii_letters + string.digits for c in pw)

        if args.json:
            import json
            print(json.dumps({"password": pw, "length": len(pw),
                "entropy": round(entropy, 1), "strength": strength,
                "charset": {"lower": has_lower, "upper": has_upper,
                    "digits": has_digit, "symbols": has_symbol}}))
        elif args.quiet:
            print(f"{entropy:.0f}")
        else:
            print(f"\n  Password:  {'*' * min(len(pw), 4)}{pw[4:] if len(pw) > 4 else ''}")
            print(f"  Length:    {len(pw)}")
            print(f"  Entropy:   {entropy:.1f} bits")
            print(f"  Strength:  {bar} {strength}")
            print(f"\n  Charset:   {'✓' if has_lower else '✗'} lowercase  {'✓' if has_upper else '✗'} uppercase  {'✓' if has_digit else '✗'} digits  {'✓' if has_symbol else '✗'} symbols")
            if entropy < 60:
                print(f"\n  Tip: Use at least 12 chars with mixed case, digits, and symbols")
            print()
        sys.exit(0)

    # Validate inputs
    if args.length < 1:
        parser.error("password length must be at least 1")
    if args.words is not None and args.words < 1:
        parser.error("word count must be at least 1")
    if args.pin is not None and args.pin < 1:
        parser.error("PIN length must be at least 1")
    if args.count < 1:
        parser.error("count must be at least 1")

    for i in range(args.count):
        if args.pin:
            pw = generate_pin(args.pin)
            entropy = calculate_entropy(pw, mode='pin')
            mode_label = f"{args.pin}-digit PIN"
        elif args.words:
            pw = generate_passphrase(args.words, separator=args.sep)
            entropy = calculate_entropy(pw, mode='passphrase', words=args.words)
            mode_label = f"{args.words}-word passphrase"
        else:
            pw = generate_password(args.length, use_symbols=not args.no_symbols)
            entropy = calculate_entropy(pw, mode='password')
            mode_label = f"{args.length}-char password"

        if args.json:
            import json
            print(json.dumps({"password": pw, "type": mode_label,
                "entropy": round(entropy, 1),
                "strength": strength_label(entropy)}))
        elif args.quiet:
            print(pw)
        else:
            strength = strength_label(entropy)
            bar = strength_bar(entropy)
            if args.count > 1:
                print(f"  {i+1}. {pw}")
            else:
                print(f"\n  {pw}\n")
                print(f"  Type:     {mode_label}")
                print(f"  Entropy:  {entropy:.1f} bits")
                print(f"  Strength: {bar} {strength}")
                print()

    if args.count > 1 and not args.quiet and not args.json:
        print(f"\n  [{mode_label}, ~{entropy:.0f} bits each]")


if __name__ == '__main__':
    main()
