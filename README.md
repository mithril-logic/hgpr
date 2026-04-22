# hgpr — Homerow-Gated Palm Rejection

A Linux daemon that uses the occupancy of your keyboard's homerow anchor keys (default `F` and `J`) to deterministically switch your trackpad between **typing** and **gesture** postures. Each posture applies its own libinput parameters — tap detection, palm rejection, disable-while-typing — so the trackpad knows you're typing because your hands are *on the homerow*, not because you typed something 500 ms ago.

Ships as a **defensive publication** (`DISCLOSURE.md`, CC0) plus a **reference implementation** (`hgpr.py`, Apache 2.0). Intended to establish prior art and preserve freedom to implement.

## Why

Mac trackpads feel good partly because palm rejection is tuned end-to-end and is context-aware in ways `syndaemon` and libinput's `Disable While Typing` are not. HGPR is a different angle on the same problem: deterministic posture classification from keyboard state, instead of probabilistic contact classification on the trackpad itself.

See `DISCLOSURE.md` for the method write-up and prior art discussion.

## Status

Proof of concept. X11/Xorg only. Patches welcome for:

- Wayland (Hyprland `hyprctl`, GNOME `gsettings`, KDE `kwriteconfig6`)
- macOS (IOKit HID + private touchpad frameworks)
- Windows (Raw Input + HID feature reports)
- Continuous-occupancy variant for Wooting / analog-hall keyboards

## Requirements

- Linux with **Xorg** (Wayland not supported yet)
- Python 3.9+
- `python-evdev` (`pip install evdev`)
- `xinput` installed and accessible in `$PATH`
- User membership in the `input` group
- A trackpad whose `xinput list` entry contains the string in `TRACKPAD_HINT` (default: `"Touchpad"`)

## Install

```bash
# one-time: add yourself to the input group (log out and back in after)
sudo usermod -aG input $USER

# install python dependency
pip install --user evdev

# clone this repo
git clone https://github.com/mithril-logic/hgpr && cd hgpr

# test-run in foreground
python3 hgpr.py
```

Type for a few seconds, then move a finger to the trackpad. You should see:

```
[hgpr] trackpad id=13, watching 1 keyboard(s)
```

and in another terminal, `xinput list-props <id>` should show `libinput Tapping Enabled` toggling between `0` and `1` as you move your fingers on and off the homerow.

## Configuration

Edit the constants at the top of `hgpr.py`:

| Constant | Meaning | Default |
|---|---|---|
| `ANCHOR_KEYS` | Set of `evdev` keycodes treated as anchors | `{KEY_F, KEY_J}` |
| `REARM_MS` | Milliseconds a key remains "occupied" after release | `400` |
| `GRACE_MS` | Delay on TYPING → GESTURE transition (anti-flap) | `120` |
| `POLL_INTERVAL` | Seconds between `select()` polls | `0.02` |
| `TRACKPAD_HINT` | Substring match against `xinput list` entries | `"Touchpad"` |
| `POSTURE` | Dict of posture-name → {xinput property: value} | See source |

### Alternate layouts

Index fingers on non-QWERTY layouts rest differently:

- **QWERTY:** `{KEY_F, KEY_J}` (default)
- **Colemak:** `{KEY_T, KEY_N}`
- **Dvorak:** `{KEY_U, KEY_H}`
- **Workman:** `{KEY_T, KEY_N}`

You can also pick any other anchor keys — the method is not limited to index fingers or to the homerow.

## Run as a service

A user-level systemd unit is provided in `systemd/hgpr.service`:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/hgpr.service ~/.config/systemd/user/
# edit ExecStart to point to the actual path of hgpr.py
systemctl --user daemon-reload
systemctl --user enable --now hgpr.service
journalctl --user -u hgpr.service -f
```

## Troubleshooting

**`No keyboards found. Are you in the 'input' group?`** — you're not in the `input` group yet. Run `sudo usermod -aG input $USER` and log out and back in.

**`No trackpad matched TRACKPAD_HINT`** — run `xinput list` and look for the actual name of your trackpad; set `TRACKPAD_HINT` to a substring of it.

**Nothing happens when I lift my fingers off the homerow** — check that `xinput list-props <trackpad-id>` actually has `libinput Tapping Enabled` and `libinput Disable While Typing Enabled`. If your driver is not `libinput`, edit the `POSTURE` dict to use properties your driver exposes.

## Licensing

- **`DISCLOSURE.md`** — Creative Commons **CC0 1.0 Universal** (public domain dedication). See the licensing section at the top of the file for the full patent non-assertion.
- **Code (`hgpr.py`, systemd units, everything else)** — Apache License, Version 2.0. This includes an express patent grant from contributors.

The author has irrevocably disclaimed all patent rights in the method disclosed here. Anyone can implement, ship, extend, or commercialize it. The disclosure is intended to establish prior art and preserve freedom to implement.

## Prior art, cited patents, academic references

See §2 and §6 of `DISCLOSURE.md`. Notable:

- Apple US20100148995A1, US10585493B2 (touch-sensitive mechanical keyboard)
- IBM/Lenovo US6529186B1, US6939066B2 (home-row triggered pointing mode)
- Synaptics Accidental Contact Mitigation
- Schwarz et al., *Probabilistic Palm Rejection*, CHI 2014
- *TypeBoard*, UIST; *ResType*, CHI 2023; *LongPad*, CHI; *TouchKeys*, NIME 2012
- `syndaemon`, libinput `Disable While Typing`, TouchFreeze, Windows Precision Touchpad palm check

## Boop latency

This project introduces **boop latency** as a proposed trackpad benchmark: the number of milliseconds from capacitive or mechanical contact on the trackpad surface to the emission of a corresponding cursor event to userspace. Sub-10 ms is the goal. If you know of existing measurements on Apple, Windows Precision, or Linux `libinput` stacks, please open an issue.
