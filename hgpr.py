#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Mithril
"""hgpr: Homerow-Gated Palm Rejection daemon.

Watches keyboard anchor keys (default F, J) via evdev and switches the
trackpad between TYPING and GESTURE postures by setting libinput
properties through `xinput set-prop`. X11/Xorg only for now.
"""

import time
import subprocess
from collections import defaultdict
from evdev import InputDevice, ecodes, list_devices
from select import select

# ---- Config ----------------------------------------------------------------
ANCHOR_KEYS   = {ecodes.KEY_F, ecodes.KEY_J}
REARM_MS      = 400     # "still occupied" window after key release
GRACE_MS      = 120     # delay TYPING -> GESTURE transition
POLL_INTERVAL = 0.02
TRACKPAD_HINT = "Touchpad"   # substring match against `xinput list`

POSTURE = {
    "TYPING":  {"libinput Tapping Enabled": "0",
                "libinput Disable While Typing Enabled": "1"},
    "GESTURE": {"libinput Tapping Enabled": "1",
                "libinput Disable While Typing Enabled": "0"},
}

# ---- State -----------------------------------------------------------------
last_up       = defaultdict(float)
is_down       = defaultdict(bool)
posture       = "GESTURE"
last_release  = 0.0

def now_ms() -> float:
    return time.monotonic() * 1000.0

def find_kbds():
    for p in list_devices():
        d = InputDevice(p)
        caps = d.capabilities().get(ecodes.EV_KEY, [])
        if ecodes.KEY_F in caps and ecodes.KEY_J in caps:
            yield d

def find_tp() -> str:
    out = subprocess.check_output(["xinput", "list"]).decode()
    for line in out.splitlines():
        if TRACKPAD_HINT.lower() in line.lower() and "slave  pointer" in line:
            return line.split("id=")[1].split()[0]
    raise RuntimeError(
        f"No trackpad matched TRACKPAD_HINT={TRACKPAD_HINT!r}. "
        "Run `xinput list` to find the right name and edit the constant."
    )

def apply(p: str, tp: str) -> None:
    global posture
    if p == posture:
        return
    posture = p
    for k, v in POSTURE[p].items():
        subprocess.run(["xinput", "set-prop", tp, k, v], check=False)

def compute() -> str:
    t = now_ms()
    occ = sum(1 for k in ANCHOR_KEYS
              if is_down[k] or (t - last_up.get(k, 0)) < REARM_MS)
    return "TYPING" if occ == len(ANCHOR_KEYS) else "GESTURE"

def main() -> None:
    global last_release
    devs = {d.fd: d for d in find_kbds()}
    if not devs:
        raise RuntimeError(
            "No keyboards found. Ensure you are in the 'input' group "
            "(`sudo usermod -aG input $USER`) and have logged out/in."
        )
    tp = find_tp()
    print(f"[hgpr] trackpad id={tp}, watching {len(devs)} keyboard(s)")

    while True:
        r, _, _ = select(devs, [], [], POLL_INTERVAL)
        for fd in r:
            for ev in devs[fd].read():
                if ev.type != ecodes.EV_KEY or ev.code not in ANCHOR_KEYS:
                    continue
                if ev.value == 1:            # key down
                    is_down[ev.code] = True
                elif ev.value == 0:          # key up
                    is_down[ev.code] = False
                    last_up[ev.code] = now_ms()
                    last_release = now_ms()

        target = compute()
        if target == "GESTURE" and posture == "TYPING" \
           and (now_ms() - last_release) < GRACE_MS:
            continue
        apply(target, tp)

if __name__ == "__main__":
    main()
