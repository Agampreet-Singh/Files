#!/usr/bin/env python3

import time
import random
import sys
import argparse

# We'll multiply all delays by this factor. >1 means slower, <1 means faster.
SLOW_FACTOR = 1.0

# small helper to centralize sleeps so they can be adjusted easily
def _sleep(t):
    time.sleep(max(0.0, t * SLOW_FACTOR))

def slow_print(s, delay=0.02):
    """Print characters slowly. 'delay' is per-character base time; multiplied by SLOW_FACTOR."""
    for ch in s:
        sys.stdout.write(ch)
        sys.stdout.flush()
        _sleep(delay)
    print()


def phase_header(n, title):
    print("\n" + "="*40)
    print(f"Phase {n}: {title}")
    print("="*40)


def simulate_progress(steps=20, delay=0.06):
    """Render a simple progress bar. 'delay' is base per-step time (multiplied by SLOW_FACTOR)."""
    for i in range(steps+1):
        bar = "#" * i + "-" * (steps - i)
        pct = int((i / steps) * 100) if steps else 100
        sys.stdout.write(f"\r[{bar}] {pct}%")
        sys.stdout.flush()
        _sleep(delay)
    print("\n")


def phase1_find_connected_device():
    phase_header(1, "Finding the Connected iPhone")
    slow_print("Scanning USB ports and network interfaces for devices...", 0.03)
    simulate_progress(18, 0.05)
    # simulation result
    found = random.choice([True, False, True])  # bias toward True for demo
    _sleep(0.4)
    if found:
        slow_print("Potential device found (USB ID: 0x1234:0xabcd).", 0.01)
    else:
        slow_print("No device found. (Simulation result: try again.)", 0.01)
    _sleep(0.25)
    return found


def phase2_identify_model():
    phase_header(2, "Found iPhone 13")
    slow_print("Querying device properties...", 0.03)
    simulate_progress(12, 0.04)
    _sleep(0.3)
    model = "iPhone 13"
    slow_print(f"Model identified: {model}", 0.01)
    _sleep(0.3)
    return model


def phase3_try_jailbreak():
    phase_header(3, "Trying JailBreak")
    slow_print("Preparing jailbreak payload (simulated)...", 0.03)
    simulate_progress(20, 0.03)
    # randomized simulated success chance
    success = random.random() < 0.75
    _sleep(0.4)
    if success:
        slow_print("Exploit chain executed (simulation): kernel patch applied.", 0.01)
    else:
        slow_print("Exploit failed (simulation). Retrying might help.", 0.01)
    _sleep(0.25)
    return success


def phase4_jailbreak_access(success):
    phase_header(4, "JailBreak Access")
    _sleep(0.2)
    if success:
        slow_print("Jailbreak environment ready (simulated shell).", 0.02)
        simulate_progress(8, 0.05)
        _sleep(0.25)
        return True
    else:
        slow_print("No jailbreak environment available. Aborting phase.", 0.02)
        _sleep(0.15)
        return False


def phase5_get_new_passcode():
    phase_header(5, "Getting Input for New Passcode")
    slow_print("Enter a NEW passcode you want to set (simulation):", 0.01)
    _sleep(0.1)
    while True:
        new_pass = input("New passcode (digits or text, 4-12 chars): ").strip()
        _sleep(0.05)
        if 4 <= len(new_pass) <= 12:
            slow_print("New passcode accepted.", 0.01)
            _sleep(0.25)
            return new_pass
        else:
            print("Passcode must be 4-12 characters. Try again.")
            _sleep(0.15)


def phase6_enter_jailbreak():
    phase_header(6, "Entering JailBreak")
    slow_print("Mounting simulated filesystem and opening settings...", 0.03)
    simulate_progress(10, 0.04)
    _sleep(0.3)
    slow_print("Ready to apply passcode change (simulation).", 0.01)
    _sleep(0.2)


def phase7_access_granted():
    phase_header(7, "Access Granted")
    slow_print("Simulated privileges escalated. You can change passcode now.", 0.02)
    simulate_progress(6, 0.04)
    _sleep(0.25)


def phase8_password_changed(new_pass):
    phase_header(8, "Password Changed")
    slow_print("Applying new passcode to simulated account...", 0.03)
    simulate_progress(12, 0.03)
    slow_print("Passcode changed successfully in simulation.", 0.02)
    _sleep(0.25)
    # store as simulated 'real' pass
    return new_pass


def phase9_try_password(sim_pass):
    phase_header(9, "Try Password")
    slow_print("You may now try the passcode on the simulated lock (type to test).", 0.01)
    _sleep(0.12)
    attempt = input("Enter passcode to try: ").strip()
    _sleep(0.05)
    if attempt == sim_pass:
        slow_print("ACCESS GRANTED — simulation only.", 0.01)
        return True
    else:
        slow_print("ACCESS DENIED — wrong passcode (simulation).", 0.01)
        return False


def main():
    global SLOW_FACTOR
    parser = argparse.ArgumentParser(description="Fake Passcode Hack Simulator (slower, configurable)")
    parser.add_argument('--slow', type=float, default=1.0,
                        help='Multiply all delays by this factor. >1 = slower, <1 = faster (default: 1.0)')
    parser.add_argument('--seed', type=int, default=None, help='Optional random seed for reproducible runs')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    SLOW_FACTOR = max(0.01, args.slow)

    slow_print("IPhone JailBreak\n", 0.01)
    _sleep(0.2)

    if not phase1_find_connected_device():
        print("Simulation ended: no device found. Re-run to try again.")
        return

    model = phase2_identify_model()
    _sleep(0.15)

    jb_success = phase3_try_jailbreak()
    if not phase4_jailbreak_access(jb_success):
        print("Simulation ended: jailbreak failed.")
        return

    new_pass = phase5_get_new_passcode()
    phase6_enter_jailbreak()
    phase7_access_granted()
    sim_pass = phase8_password_changed(new_pass)
    success = phase9_try_password(sim_pass)
    if success:
        slow_print("\nSimulation complete: well done!", 0.02)
    else:
        slow_print("\nSimulation complete: try again or choose a different passcode.", 0.02)


if __name__ == "__main__":
    main()
