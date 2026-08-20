"""
engines/color_mapping.py — zzluxora v6.0

Color mapping pipeline sesuai `markdowns/script_math_model.md`:
  §[4] V-A → HSV (rule-based, 4 quadrants)
  §[5] HSV → RGB (Foley & van Dam)
  §[6] RGB → RGBW (W = min)

Source of truth: skripsi BAB 3 (script_andreas_v3) + script_math_model.md.
"""
from typing import Tuple


# Tunable parameters (math model §[10])
W_AROUSAL = (0.40, 0.35, 0.25)   # bpm_n, rms_n, onset_n
W_VALENCE = (0.50, 0.30, 0.20)   # chroma_n, sc_n, mfcc1_n
ALPHA_SAT = 0.60                 # S blend (A weight)
BETA_VAL = 0.50                  # V_hsv blend (rms weight)
V_HSV_MIN = 0.10                 # minimum brightness
MAJOR_INDICES = (0, 2, 4, 5, 7, 9, 11)  # C, D, E, F, G, A, B


def compute_va(bpm_n: float, rms_n: float, onset_n: float,
               chroma_n: float, sc_n: float, mfcc1_n: float) -> Tuple[float, float]:
    """
    Hitung Valence & Arousal dari fitur ternormalisasi.
    Sesuai `script_math_model.md §[3]`.

    Returns:
        (V, A) tuple, masing-masing ∈ [0, 1]
    """
    w1, w2, w3 = W_AROUSAL
    A = w1 * bpm_n + w2 * rms_n + w3 * onset_n

    w4, w5, w6 = W_VALENCE
    V = w4 * chroma_n + w5 * sc_n + w6 * (1.0 - abs(mfcc1_n - 0.5) * 2.0)

    # Clamp
    V = max(0.0, min(1.0, V))
    A = max(0.0, min(1.0, A))

    return V, A


def get_quadrant(V: float, A: float) -> str:
    """
    Tentukan kuadran V-A sesuai `script_math_model.md §[3]`.
        Q1: V>0.5, A>0.5  → Praise (warm)
        Q2: V≤0.5, A>0.5  → Intens (purple)
        Q3: V≤0.5, A≤0.5  → Kontemplatif (blue)
        Q4: V>0.5, A≤0.5  → Damai (cyan/green)
    """
    if V > 0.5 and A > 0.5:
        return "Q1"
    if V <= 0.5 and A > 0.5:
        return "Q2"
    if V <= 0.5 and A <= 0.5:
        return "Q3"
    return "Q4"


def get_quadrant_name(q: str) -> str:
    """Nama kuadran yang human-readable."""
    return {"Q1": "Praise", "Q2": "Intens", "Q3": "Kontemplatif", "Q4": "Damai"}.get(q, "Unknown")


def va_to_hsv(V: float, A: float, chroma_peak: int = 6, rms_norm: float = 0.5) -> Tuple[float, float, float]:
    """
    Map V-A ke HSV color space. Sesuai `script_math_model.md §[4]`.

    Args:
        V: Valence [0, 1]
        A: Arousal [0, 1]
        chroma_peak: 0-11 (peak chroma index untuk hue correction)
        rms_norm: RMS normalized [0, 1] (untuk V_hsv)

    Returns:
        (H, S, V_hsv) — H ∈ [0, 360), S dan V_hsv ∈ [0, 1]
    """
    # Hue base per kuadran
    if V > 0.5 and A > 0.5:                # Q1 Praise → warm
        H_base = 30 + (V - 0.5) * 60
    elif V <= 0.5 and A > 0.5:              # Q2 Intens → purple
        H_base = 270 + (0.5 - V) * 120
    elif V <= 0.5 and A <= 0.5:             # Q3 Kontemplatif → blue
        H_base = 200 + (0.5 - V) * 120
    else:                                   # Q4 Damai → cyan/green
        H_base = 150 + (V - 0.5) * 100

    # Koreksi chroma: H = H_base + (ChromaPeak - 6) × 5°
    H = (H_base + (chroma_peak - 6) * 5) % 360

    # Saturation
    S = ALPHA_SAT * A + (1.0 - ALPHA_SAT) * abs(2 * V - 1)
    S = max(0.0, min(1.0, S))

    # Value (brightness)
    V_hsv = BETA_VAL * rms_norm + (1.0 - BETA_VAL) * A
    V_hsv = max(V_HSV_MIN, min(1.0, V_hsv))

    return round(H, 2), round(S, 4), round(V_hsv, 4)


def hsv_to_rgb(H: float, S: float, V: float) -> Tuple[float, float, float]:
    """
    Convert HSV → RGB (Foley & van Dam). Sesuai `script_math_model.md §[5]`.

    Args:
        H: Hue ∈ [0, 360)
        S: Saturation ∈ [0, 1]
        V: Value ∈ [0, 1]

    Returns:
        (R, G, B) ∈ [0, 1]
    """
    C = V * S
    Hp = H / 60.0
    X = C * (1 - abs(Hp % 2 - 1))
    m = V - C

    if Hp < 1:
        R1, G1, B1 = C, X, 0
    elif Hp < 2:
        R1, G1, B1 = X, C, 0
    elif Hp < 3:
        R1, G1, B1 = 0, C, X
    elif Hp < 4:
        R1, G1, B1 = 0, X, C
    elif Hp < 5:
        R1, G1, B1 = X, 0, C
    else:
        R1, G1, B1 = C, 0, X

    R = R1 + m
    G = G1 + m
    B = B1 + m

    return R, G, B


def rgb_to_rgbw(R: float, G: float, B: float) -> Tuple[float, float, float, float]:
    """
    Extract white channel. Sesuai `script_math_model.md §[6]`.
        W = min(R, G, B)
        R' = R - W, G' = G - W, B' = B - W

    Returns:
        (R', G', B', W) ∈ [0, 1]
    """
    W = min(R, G, B)
    return R - W, G - W, B - W, W


def hsv_to_drgbw(H: float, S: float, V: float) -> dict:
    """
    Full pipeline: HSV → RGB → RGBW → 8-bit DRGBW.

    Returns:
        dict dengan keys: dimmer, r, g, b, w, rgb_255
    """
    R, G, B = hsv_to_rgb(H, S, V)
    Rp, Gp, Bp, W = rgb_to_rgbw(R, G, B)

    return {
        "dimmer": int(round(V * 255)),
        "r": int(round(Rp * 255)),
        "g": int(round(Gp * 255)),
        "b": int(round(Bp * 255)),
        "w": int(round(W * 255)),
        "rgb_255": (int(round(R * 255)), int(round(G * 255)), int(round(B * 255))),
    }


def va_to_drgbw(V: float, A: float, chroma_peak: int = 6, rms_norm: float = 0.5) -> dict:
    """
    Convenience: V-A → HSV → DRGBW.
    """
    H, S, V_hsv = va_to_hsv(V, A, chroma_peak, rms_norm)
    drgbw = hsv_to_drgbw(H, S, V_hsv)
    drgbw["hue"] = H
    drgbw["saturation"] = S
    drgbw["value_hsv"] = V_hsv
    drgbw["quadrant"] = get_quadrant(V, A)
    return drgbw
