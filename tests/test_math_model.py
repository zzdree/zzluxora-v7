"""
tests/test_math_model.py â€” zzluxora v6.0

RELEASE BLOCKER.
Test case dari `script_math_model.md Â[sect][9]`: "10.000 Reasons"

Expected output:
    A = 0.126
    V = 0.627
    Quadrant = Q4 (Damai/tenang)
    H = 162.7Â° (cyan)
    S = 0.178
    V_hsv = 0.135
    D = 34, R = 0, G = 6, B = 4, W = 28
    Chase timing = 1500ms (BPM < 90)

Run:   python -m pytest tests/test_math_model.py -v
       python tests/test_math_model.py  (built-in runner)
"""
import sys
from pathlib import Path

# Add project root ke sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engines.analyze_pipeline import AnalyzePipeline, AudioFeatures
from engines.color_mapping import (
    va_to_hsv, hsv_to_rgb, rgb_to_rgbw, hsv_to_drgbw,
    get_quadrant, get_quadrant_name, compute_va,
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Test case dari math model Â[sect][9] "10.000 Reasons"
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def make_10k_features() -> AudioFeatures:
    """Raw features untuk '10.000 Reasons' test case."""
    return AudioFeatures(
        duration=300.0,
        tempo=73,
        rms_mean=0.08,
        sc_mean=1800.0,
        mfcc1_mean=-120.0,
        chroma_major=0.72,
        chroma_peak=6,
        onset_rate=1.5,
    )


def test_10k_reasons_normalization():
    """STAGE 3: Normalized values harus match math model Â[sect][9]."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    n = pipeline.stage_3_normalize(af)

    assert abs(n.bpm - 0.108) < 0.001, f"BPM_n expected 0.108, got {n.bpm}"
    assert abs(n.rms - 0.143) < 0.001, f"RMS_n expected 0.143, got {n.rms}"
    assert abs(n.sc - 0.289) < 0.001, f"SC_n expected 0.289, got {n.sc}"
    assert abs(n.mfcc1 - 0.450) < 0.001, f"MFCC1_n expected 0.450, got {n.mfcc1}"
    assert abs(n.onset_rate - 0.133) < 0.001, f"Onset_n expected 0.133, got {n.onset_rate}"
    assert abs(n.chroma_major - 0.720) < 0.001, f"ChromaMajor_n expected 0.720, got {n.chroma_major}"
    print("  âœ“ test_10k_reasons_normalization PASSED")


def test_10k_reasons_va():
    """STAGE 4: V-A harus match A=0.126, V=0.627, Q4 (math model Â[sect][9])."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    n = pipeline.stage_3_normalize(af)
    va = pipeline.stage_4_compute_va(n)

    assert abs(va.arousal - 0.126) < 0.001, f"A expected 0.126, got {va.arousal}"
    assert abs(va.valence - 0.627) < 0.001, f"V expected 0.627, got {va.valence}"
    assert va.quadrant == "Q4", f"Expected Q4, got {va.quadrant}"
    assert va.quadrant_name == "Damai", f"Expected 'Damai', got {va.quadrant_name}"
    print("  âœ“ test_10k_reasons_va PASSED")


def test_10k_reasons_hsv():
    """STAGE 6/8: HSV harus match H=162.7Â°, S=0.178, V_hsv=0.135."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    n = pipeline.stage_3_normalize(af)
    va = pipeline.stage_4_compute_va(n)

    H, S, V_hsv = va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)

    assert abs(H - 162.7) < 0.5, f"H expected 162.7Â°, got {H}Â°"
    assert abs(S - 0.178) < 0.005, f"S expected 0.178, got {S}"
    assert abs(V_hsv - 0.135) < 0.005, f"V_hsv expected 0.135, got {V_hsv}"
    print(f"  âœ“ test_10k_reasons_hsv PASSED (H={H}Â°, S={S}, V_hsv={V_hsv})")


def test_10k_reasons_drgbw():
    """STAGE 6/8: DRGBW harus match D=34 R=0 G=6 B=4 W=28 (math model Â[sect][9])."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    n = pipeline.stage_3_normalize(af)
    va = pipeline.stage_4_compute_va(n)
    H, S, V_hsv = va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)

    drgbw = hsv_to_drgbw(H, S, V_hsv)

    assert drgbw["dimmer"] == 34, f"D expected 34, got {drgbw['dimmer']}"
    assert drgbw["r"] == 0, f"R expected 0, got {drgbw['r']}"
    assert drgbw["g"] == 6, f"G expected 6, got {drgbw['g']}"
    assert drgbw["b"] == 4, f"B expected 4, got {drgbw['b']}"
    assert drgbw["w"] == 28, f"W expected 28, got {drgbw['w']}"
    print(f"  âœ“ test_10k_reasons_drgbw PASSED (D={drgbw['dimmer']} R={drgbw['r']} G={drgbw['g']} B={drgbw['b']} W={drgbw['w']})")


def test_10k_reasons_chase_timing():
    """STAGE 7: BPM 73 < 90 â†’ 1500ms chase timing."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    timing = pipeline.stage_7_chase_timing(af)
    assert timing == 1500, f"BPM 73 expected 1500ms, got {timing}ms"
    print(f"  âœ“ test_10k_reasons_chase_timing PASSED ({timing}ms)")


def test_10k_reasons_full():
    """End-to-end: run_with_features() harus produce full result match math model."""
    pipeline = AnalyzePipeline()
    af = make_10k_features()
    result = pipeline.run_with_features(af)

    # V-A
    assert abs(result.va.valence - 0.627) < 0.001
    assert abs(result.va.arousal - 0.126) < 0.001
    assert result.va.quadrant == "Q4"

    # HSV
    assert abs(result.hsv.h - 162.7) < 0.5
    assert abs(result.hsv.s - 0.178) < 0.005
    assert abs(result.hsv.v - 0.135) < 0.005

    # DRGBW
    assert result.drgbw.dimmer == 34
    assert result.drgbw.r == 0
    assert result.drgbw.g == 6
    assert result.drgbw.b == 4
    assert result.drgbw.w == 28

    # Chase timing
    assert result.chase_timing_ms == 1500

    print("  âœ“ test_10k_reasons_full PASSED (end-to-end)")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Quadrant tests (math model Â[sect][3])
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_quadrant_q1_praise():
    """Q1: V>0.5, A>0.5 â†’ Praise, warm hue ~48Â°"""
    H, S, V_hsv = va_to_hsv(0.8, 0.8, chroma_peak=6, rms_norm=0.5)
    # H_base = 30 + (0.8-0.5)*60 = 48Â°
    assert 45 < H < 50, f"Q1 H expected ~48Â°, got {H}Â°"
    assert get_quadrant(0.8, 0.8) == "Q1"
    assert get_quadrant_name("Q1") == "Praise"
    print(f"  âœ“ test_quadrant_q1_praise PASSED (H={H}Â°)")


def test_quadrant_q2_intens():
    """Q2: Vâ‰¤0.5, A>0.5 â†’ Intens, purple hue ~294Â°"""
    H, S, V_hsv = va_to_hsv(0.3, 0.7, chroma_peak=6, rms_norm=0.5)
    # H_base = 270 + (0.5-0.3)*120 = 294Â°
    assert 290 < H < 300, f"Q2 H expected ~294Â°, got {H}Â°"
    assert get_quadrant(0.3, 0.7) == "Q2"
    print(f"  âœ“ test_quadrant_q2_intens PASSED (H={H}Â°)")


def test_quadrant_q3_kontemplatif():
    """Q3: Vâ‰¤0.5, Aâ‰¤0.5 â†’ Kontemplatif, blue hue ~224Â°"""
    H, S, V_hsv = va_to_hsv(0.3, 0.3, chroma_peak=6, rms_norm=0.5)
    # H_base = 200 + (0.5-0.3)*120 = 224Â°
    assert 220 < H < 230, f"Q3 H expected ~224Â°, got {H}Â°"
    assert get_quadrant(0.3, 0.3) == "Q3"
    print(f"  âœ“ test_quadrant_q3_kontemplatif PASSED (H={H}Â°)")


def test_quadrant_q4_damai():
    """Q4: V>0.5, Aâ‰¤0.5 â†’ Damai, cyan/green hue ~170Â°"""
    H, S, V_hsv = va_to_hsv(0.7, 0.3, chroma_peak=6, rms_norm=0.5)
    # H_base = 150 + (0.7-0.5)*100 = 170Â°
    assert 165 < H < 175, f"Q4 H expected ~170Â°, got {H}Â°"
    assert get_quadrant(0.7, 0.3) == "Q4"
    print(f"  âœ“ test_quadrant_q4_damai PASSED (H={H}Â°)")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HSVâ†’RGB tests (math model Â[sect][5])
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_hsv_red_pure():
    """HSV(0, 1, 1) â†’ red (1, 0, 0)."""
    R, G, B = hsv_to_rgb(0, 1, 1)
    assert abs(R - 1.0) < 0.01, f"R expected 1.0, got {R}"
    assert abs(G) < 0.01
    assert abs(B) < 0.01
    print("  âœ“ test_hsv_red_pure PASSED")


def test_hsv_white():
    """HSV(0, 0, 1) â†’ white (1, 1, 1)."""
    R, G, B = hsv_to_rgb(0, 0, 1)
    assert abs(R - 1.0) < 0.01
    assert abs(G - 1.0) < 0.01
    assert abs(B - 1.0) < 0.01
    print("  âœ“ test_hsv_white PASSED")


def test_hsv_black():
    """HSV(0, 0, 0) â†’ black (0, 0, 0)."""
    R, G, B = hsv_to_rgb(0, 0, 0)
    assert abs(R) < 0.01
    assert abs(G) < 0.01
    assert abs(B) < 0.01
    print("  âœ“ test_hsv_black PASSED")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# RGBâ†’RGBW tests (math model Â[sect][6])
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_rgbw_pure_red():
    """RGB(1,0,0) â†’ RGBW (1,0,0,0) â€” no white."""
    Rp, Gp, Bp, W = rgb_to_rgbw(1, 0, 0)
    assert abs(Rp - 1.0) < 0.01
    assert abs(Gp) < 0.01
    assert abs(Bp) < 0.01
    assert abs(W) < 0.01
    print("  âœ“ test_rgbw_pure_red PASSED")


def test_rgbw_white_extraction():
    """RGB(0.5,0.5,0.5) â†’ RGBW (0,0,0,0.5) â€” full white extraction."""
    Rp, Gp, Bp, W = rgb_to_rgbw(0.5, 0.5, 0.5)
    assert abs(Rp) < 0.01
    assert abs(Gp) < 0.01
    assert abs(Bp) < 0.01
    assert abs(W - 0.5) < 0.01
    print("  âœ“ test_rgbw_white_extraction PASSED")


def test_rgbw_mixed():
    """RGB(0.7, 0.3, 0.2) â†’ RGBW (0.5, 0.1, 0.0, 0.2) â€” partial white."""
    Rp, Gp, Bp, W = rgb_to_rgbw(0.7, 0.3, 0.2)
    assert abs(Rp - 0.5) < 0.01, f"Rp expected 0.5, got {Rp}"
    assert abs(Gp - 0.1) < 0.01
    assert abs(Bp) < 0.01
    assert abs(W - 0.2) < 0.01
    print("  âœ“ test_rgbw_mixed PASSED")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Chase timing tests (math model Â[sect][8])
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_chase_timing_brackets():
    """Chase timing rules:
        BPM > 120   â†’ 500ms
        90 â‰¤ BPM â‰¤ 120 â†’ 700ms
        BPM < 90    â†’ 1500ms
    """
    pipeline = AnalyzePipeline()

    # High BPM
    af_hi = AudioFeatures(duration=180, tempo=140, rms_mean=0.2, sc_mean=2000,
                          mfcc1_mean=-50, chroma_major=0.6, chroma_peak=6, onset_rate=3.0)
    assert pipeline.stage_7_chase_timing(af_hi) == 500

    # Mid BPM
    af_mid = AudioFeatures(duration=180, tempo=100, rms_mean=0.2, sc_mean=2000,
                           mfcc1_mean=-50, chroma_major=0.6, chroma_peak=6, onset_rate=3.0)
    assert pipeline.stage_7_chase_timing(af_mid) == 700

    # Low BPM
    af_lo = AudioFeatures(duration=180, tempo=70, rms_mean=0.2, sc_mean=2000,
                          mfcc1_mean=-50, chroma_major=0.6, chroma_peak=6, onset_rate=3.0)
    assert pipeline.stage_7_chase_timing(af_lo) == 1500

    # Boundary: 120 â†’ 700ms
    af_b1 = AudioFeatures(duration=180, tempo=120, rms_mean=0.2, sc_mean=2000,
                          mfcc1_mean=-50, chroma_major=0.6, chroma_peak=6, onset_rate=3.0)
    assert pipeline.stage_7_chase_timing(af_b1) == 700

    # Boundary: 121 â†’ 500ms
    af_b2 = AudioFeatures(duration=180, tempo=121, rms_mean=0.2, sc_mean=2000,
                          mfcc1_mean=-50, chroma_major=0.6, chroma_peak=6, onset_rate=3.0)
    assert pipeline.stage_7_chase_timing(af_b2) == 500

    print("  âœ“ test_chase_timing_brackets PASSED")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Pattern selection tests (math model Â[sect][8] Pola)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_pattern_selection():
    """Multi-fixture pattern:
        A > 0.7     â†’ all_on
        BPM > 120   â†’ running
        A < 0.3     â†’ gradient
        else        â†’ center_out
    """
    # All on: high arousal
    assert AnalyzePipeline._pick_pattern(arousal=0.8, bpm=100) == "all_on"

    # Running: high BPM
    assert AnalyzePipeline._pick_pattern(arousal=0.4, bpm=140) == "running"

    # Gradient: low arousal
    assert AnalyzePipeline._pick_pattern(arousal=0.2, bpm=80) == "gradient"

    # Center out: fallback
    assert AnalyzePipeline._pick_pattern(arousal=0.4, bpm=100) == "center_out"

    print("  âœ“ test_pattern_selection PASSED")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Runner
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def main():
    print("=" * 70)
    print("MATH MODEL VERIFICATION â€” zzluxora v6.0 (RELEASE BLOCKER)")
    print("Source: markdowns/script_math_model.md (skripsi BAB 3)")
    print("=" * 70)
    print("\n[1] Test case '10.000 Reasons' (math model Â[sect][9])")
    print("-" * 70)
    test_10k_reasons_normalization()
    test_10k_reasons_va()
    test_10k_reasons_hsv()
    test_10k_reasons_drgbw()
    test_10k_reasons_chase_timing()
    test_10k_reasons_full()

    print("\n[2] Quadrant classification (math model Â[sect][3])")
    print("-" * 70)
    test_quadrant_q1_praise()
    test_quadrant_q2_intens()
    test_quadrant_q3_kontemplatif()
    test_quadrant_q4_damai()

    print("\n[3] HSV â†’ RGB (math model Â[sect][5])")
    print("-" * 70)
    test_hsv_red_pure()
    test_hsv_white()
    test_hsv_black()

    print("\n[4] RGB â†’ RGBW (math model Â[sect][6])")
    print("-" * 70)
    test_rgbw_pure_red()
    test_rgbw_white_extraction()
    test_rgbw_mixed()

    print("\n[5] Chase timing (math model Â[sect][8])")
    print("-" * 70)
    test_chase_timing_brackets()

    print("\n[6] Pattern selection (math model Â[sect][8] Pola)")
    print("-" * 70)
    test_pattern_selection()

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED âœ…  â€”  Math model v6 verified")
    print("=" * 70)


if __name__ == "__main__":
    main()

