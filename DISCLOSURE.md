<!-- SPDX-License-Identifier: CC0-1.0 -->
# Homerow-Gated Palm Rejection

### A method for context-aware trackpad sensitivity using keyboard anchor-key occupancy state

**Author:** Mithril
**Date of first public disclosure:** 2026-04-22
**Version:** 1.0

---

## Licensing and Patent Non-Assertion

**Licensing.** This document (the disclosure, `DISCLOSURE.md`) is released under **Creative Commons CC0 1.0 Universal** (public domain dedication). The accompanying reference implementation (`hgpr.py` and related code in this repository) is released under the **Apache License, Version 2.0**, which includes an express patent grant from contributors to all users of the covered work.

**Patent non-assertion.** The author hereby irrevocably disclaims, on behalf of themselves and their successors and assigns, any and all right to assert any patent claim — including but not limited to method, system, apparatus, and non-transitory computer-readable medium claims — against any party practicing the methods, systems, or embodiments disclosed in this document. This disclosure is intended to place the subject matter in the public domain as prior art under 35 U.S.C. § 102 and equivalent laws in other jurisdictions, and to defeat any future patent claim purporting to cover the disclosed subject matter by anyone, including the author.

**Defensive intent.** Public disclosure intended to establish prior art against future patent claims by any party on the methods, systems, and embodiments described herein.

**Citation.** Mithril. *Homerow-Gated Palm Rejection: A Method for Context-Aware Trackpad Sensitivity Using Keyboard Anchor-Key Occupancy State.* Defensive Publication, 22 April 2026.

---

## 1. Abstract

A family of methods for dynamically adjusting the input-disambiguation parameters of a pointing device (trackpad, touchpad, touchscreen, stylus/pen digitizer, or other surface-contact input device) based on the real-time occupancy state of one or more designated *anchor keys* on an associated keyboard. Unlike prior art binary "disable-while-typing" approaches (e.g., `syndaemon`, Windows Precision Touchpad palm check, Synaptics Accidental Contact Mitigation), which gate on recent-keystroke timing, the methods disclosed herein use the **spatial occupancy pattern** of specific anchor keys as deterministic context classifiers. These classifiers partition user intent into discrete input postures (typing, gesture, transitional), with each posture applying a distinct parameter set to the pointing device's sensitivity, palm rejection, tap threshold, pointer acceleration, and gesture recognition pipeline.

## 2. Background and Problem

Modern laptop trackpads must distinguish intentional pointer/gesture input from inadvertent palm, wrist, or finger-at-rest contact. Prior art falls into the following buckets:

1. **Temporal heuristics** (`syndaemon`, libinput `Disable While Typing`, TouchFreeze): disable trackpad events for *N* milliseconds after any keystroke. Coarse, timing-based; punishes legitimate intermixed typing-and-pointing.
2. **Spatial classifiers on the trackpad itself** (Synaptics Accidental Contact Mitigation; Schwarz et al. 2014 probabilistic palm rejection, CHI): use contact size, pressure, and temporal evolution to classify each contact. Effective but probabilistic and non-deterministic from the user's perspective.
3. **Same-surface gesture disambiguation** (Apple US20100148995A1, US10585493B2; TouchKeys/NIME 2012): treat the keyboard itself as a touch-sensitive surface and use multi-finger contact patterns to enter gesture modes. Requires specialized hardware.
4. **Home-row-triggered pointing modes** (IBM/Lenovo US6529186B1, US6939066B2): simultaneous or chorded press of home-row keys triggers a discrete pointing mode, typically using the TrackPoint or an equivalent pointer. These methods trigger *mode entry* on a key-chord event; they do not gate continuous sensitivity parameters of a physically separate trackpad based on continuous occupancy state.

None of the above uses the discrete occupancy state of specific named anchor keys on an otherwise standard mechanical (non-touch-sensitive) keyboard as the context signal continuously gating the sensitivity, palm rejection, tap threshold, pointer acceleration, or gesture recognition parameters of a physically separate pointing device. That distinction is what this disclosure draws.

## 3. Core Method

### 3.1 Definitions

- **Anchor key:** a key designated as a posture-classification input. Default set: `{F, J}` (QWERTY homerow notches). Configurable to any key set, including `{A, ;}`, `{D, K}`, Colemak equivalents `{T, N}`, Dvorak equivalents `{U, H}`, etc., or arbitrary user-selected keys. Anchor keys may be keys on a physical keyboard, regions on a virtual/on-screen keyboard, or any discrete occupancy sensor (see §4.6).
- **Occupancy:** the boolean (or continuous, in variants) state "a finger is currently resting on this key." On discrete mechanical keyboards, occupancy is inferred from key-down / key-up events combined with a configurable rearm window. On continuous-sensing keyboards (capacitive, analog hall-effect, optical, force-sensitive), occupancy is read directly from the sensor value relative to a configurable threshold.
- **Posture:** a discrete classification of the user's current interaction intent, computed from the occupancy pattern of anchor keys.

### 3.2 Posture Classifier

Given anchor-key set `A = {a_1, a_2, ..., a_n}` and per-key occupancy function `occ(a_i) in {0, 1}` (or `[0, 1]` in continuous variants):

- If `for all a_i in A : occ(a_i) = 1` → **TYPING_POSTURE**
- Else if `there exists a_i in A : occ(a_i) = 1` → **TRANSITIONAL_POSTURE** (optional intermediate class)
- Else → **GESTURE_POSTURE**

Additional posture classes may be defined based on subsets of `A` (e.g., only left-hand anchor occupied → **RIGHT_HAND_GESTURE** for asymmetric keyboards or one-handed operation; only right-hand anchor occupied → **LEFT_HAND_GESTURE**). Posture classes are user-configurable and may be extended without limit.

### 3.3 Posture-to-Parameter Mapping

Each posture maps to a parameter set applied to the associated pointing device. Representative parameters include:

- Tap detection threshold
- Palm rejection aggressiveness
- Pointer acceleration / speed
- Scroll gesture gate (open / closed)
- Multi-finger gesture gate (open / closed)
- Click-and-drag tolerance
- Stylus / pen palm rejection aggressiveness
- Gesture recognition sensitivity

Parameter mapping is fully user-configurable and is not limited to the values above.

### 3.4 Hysteresis and Grace

Transitions between postures are subject to per-direction hysteresis windows (e.g., 120 ms grace on `TYPING → GESTURE`) to suppress flapping during natural typing-pointing interleaving. Grace windows are independently configurable per posture transition.

## 4. Embodiments

The disclosure explicitly covers — but is not limited to — the following implementations.

### 4.1 Software-Only (Mechanical Proxy)

A userspace daemon subscribes to keyboard input events (Linux `evdev`, macOS IOKit HID, Windows Raw Input, or equivalent) and maintains anchor-key occupancy via a keydown-plus-rearm-window heuristic. Posture changes trigger parameter updates on the pointing device through the operating system's input configuration API (for example: `xinput set-prop`, libinput configuration hot-reload, Hyprland configuration reload, GNOME settings APIs, KDE settings APIs, Windows HID output-report APIs, macOS touchpad configuration APIs). See `hgpr.py` in the accompanying repository for a reference implementation.

### 4.2 Analog / Capacitive Keyboard (True Occupancy)

A daemon polls continuous per-key sensor values from an analog-hall-effect keyboard (e.g., Wooting 60HE, Keychron Q1 HE, Razer Huntsman Analog), a capacitive-sensing keyboard, an optical-switch keyboard, or any other continuous-value keyboard. Occupancy is determined by threshold on the analog value (`occ := value > epsilon`, typical `epsilon = 0.05` normalized). This yields true boop-first occupancy: a finger resting at sub-actuation depth registers as present.

### 4.3 Firmware-Integrated

The anchor-key occupancy signal is computed in keyboard firmware and emitted as a side-channel HID report (or equivalent transport) consumed by the trackpad driver or the host operating system's input stack. No userspace daemon required.

### 4.4 Unified Device

Keyboard and trackpad are physically integrated into a single device such that the anchor-key occupancy signal is consumed internally by the combined device's firmware, producing an external input stream to the host that is already posture-disambiguated.

### 4.5 Touchscreen / On-Screen Keyboard

The method applies analogously to virtual keyboards where anchor keys are screen regions and occupancy is determined by continuous touch contact (not tap-release). Posture gates the sensitivity of concurrent-surface gestures, stylus palm rejection, pen tilt interpretation, or multi-touch pan/zoom.

### 4.6 Non-Keyboard Anchors

Anchor-occupancy inputs are not limited to keyboard keys. Any discrete occupancy sensor (foot pedal, capacitive armrest zone, or eye-tracker fixation region — or any other input producing a boolean or continuous occupancy signal) may serve as an anchor under the same posture-classification framework.

### 4.7 Keycap Capacitive Pointing Surfaces

Anchor keys themselves serve as capacitive X/Y pointing surfaces in addition to their role as posture classifiers. The physical hardware required — mechanical keyboards with per-key capacitive sensing of finger position — is established in prior art (Apple US20100148995A1, US10585493B2; US7659887B2; US6288707B1; TouchKeys / NIME 2012). This embodiment covers the specific integration in which:

- Anchor keys (e.g., F and J) emit continuous X/Y contact-position data via capacitive sensing across each keycap's top surface, independent of key depression.
- The HGPR posture classifier (§3.2) gates interpretation of this data. In TYPING_POSTURE (both anchors occupied at actuation depth), X/Y deltas are suppressed. In GESTURE_POSTURE (at least one anchor lifted or at sub-actuation contact), X/Y deltas are emitted as pointer or scroll events.
- Left-anchor (e.g., F) output is assignable to pointer movement; right-anchor (e.g., J) output is assignable to scroll. Assignment is user-configurable — either anchor may drive pointer, scroll, gesture input, or any other input channel.
- The combined device requires no separate trackpad; the anchor keys function as both posture classifier and pointing surface.

This embodiment extends §4.1–§4.2 by collapsing the pointing device of §3.3 into the anchor-key surface itself, with the posture classifier gating event emission rather than gating the parameters of a physically separate trackpad.

## 5. Reference Implementation

A reference implementation of Embodiment 4.1 in Python, for Linux with X11/Xorg, is provided as `hgpr.py` in the accompanying repository under the Apache License 2.0. It is intentionally minimal to demonstrate the method. Production implementations may extend to Wayland compositors, macOS, Windows, additional posture classes, continuous occupancy, and the other embodiments described in §4.

## 6. Scope of Disclosure

For purposes of establishing prior art, the author intends this disclosure to cover, among others, embodiments in **method**, **system**, **apparatus**, and **non-transitory computer-readable medium** claim formats, whether implemented in hardware, firmware, software, or any combination thereof, including:

1. Any method gating pointing-device input-disambiguation parameters on the real-time occupancy state of one or more designated keyboard keys, where "occupancy" is determined by any means (mechanical keydown-plus-rearm, capacitive, analog hall-effect, optical, piezoelectric, force-sensitive, or any other sensing modality).
2. Any such method using two or more designated anchor keys to define discrete posture classes.
3. Any such method applying differing parameters per posture.
4. Any such method with per-transition hysteresis or grace windows.
5. Any such method implemented in userspace, kernel space, keyboard firmware, trackpad firmware, or unified-device firmware.
6. Any such method applied to pointing devices including trackpads, touchpads, touchscreens, stylus / pen digitizers, and any other surface-contact or proximity-sensing input device.
7. Any such method applied to virtual / on-screen keyboards where anchor occupancy is determined by screen-contact state.
8. Any such method using non-keyboard occupancy sensors (foot pedals, armrest sensors, or eye-tracker fixation — or any other input producing a boolean or continuous occupancy signal) as anchors.
9. Any system, apparatus, or non-transitory computer-readable medium comprising means for performing any of the above.
10. The specific named classifier **"Homerow-Gated Palm Rejection"** and an associated pointing-device latency metric measured from initial surface contact to first emitted cursor event.
