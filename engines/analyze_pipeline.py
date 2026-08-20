"""
engines/analyze_pipeline.py — zzluxora v6.0

8-stage audio analysis pipeline sesuai `markdowns/script_math_model.md`:

  STAGE 1: Load Audio           (librosa.load)
  STAGE 2: Extract Features     (7 fitur audio)
  STAGE 3: Normalize             (min-max [0,1])
  STAGE 4: Compute V-A           (rule-based, weighted sum)
  STAGE 5: Segment Song          (SSM + heuristic labeling)
  STAGE 6: Per-segment V-A+Color (8-bit DRGBW per segment)
  STAGE 7: Chase Timing Rules    (BPM-based 500/700/1500ms)
  STAGE 8: Build AnalyzeResult   (final orchestrator)

Source of truth: skripsi BAB 3 (`script_andreas_v3`) + `script_math_model.md`.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
import os
import numpy as np

from engines import color_mapping as cm
from engines.va_presets import VAPreset, apply_preset


# Progress callback signature: (percent: int, message: str) -> None
ProgressCallback = Optional[Callable[[int, str], None]]


@dataclass
class AudioFeatures:
    """Raw audio features (STAGE 2 output)."""
    duration: float
    tempo: float
    rms_mean: float
    sc_mean: float
    mfcc1_mean: float
    chroma_major: float
    chroma_peak: int
    onset_rate: float
    beat_times: List[float] = field(default_factory=list)
    rms_times: List[float] = field(default_factory=list)
    rms_values: List[float] = field(default_factory=list)
    sc_times: List[float] = field(default_factory=list)
    sc_values: List[float] = field(default_factory=list)
    sb_mean: float = 0.0


@dataclass
class NormalizedFeatures:
    """Min-max normalized features (STAGE 3 output)."""
    bpm: float
    rms: float
    sc: float
    mfcc1: float
    onset_rate: float
    chroma_major: float


@dataclass
class VAResult:
    """Valence & Arousal + quadrant (STAGE 4 output)."""
    valence: float
    arousal: float
    quadrant: str
    quadrant_name: str = ""


@dataclass
class HSV:
    """HSV color (math model §[4] output)."""
    h: float
    s: float
    v: float


@dataclass
class DRGBW:
    """8-bit RGBW + dimmer (math model §[5-6] output)."""
    dimmer: int
    r: int
    g: int
    b: int
    w: int


@dataclass
class Segment:
    """Song segment with V-A + color + pattern (STAGE 6 output)."""
    index: int
    label: str
    start: float
    end: float
    duration: float
    rms: float
    sc: float
    va: Optional[VAResult] = None
    hsv: Optional[HSV] = None
    drgbw: Optional[DRGBW] = None
    pattern: str = "all_on"  # all_on | running | gradient | center_out


@dataclass
class AnalyzeResult:
    """Final analyze result (STAGE 8 output)."""
    filepath: str
    filename: str
    features: AudioFeatures
    normalized: NormalizedFeatures
    va: VAResult
    hsv: HSV
    drgbw: DRGBW
    segments: List[Segment] = field(default_factory=list)
    chase_timing_ms: int = 700


class AnalyzePipeline:
    """
    8-stage audio analysis pipeline.
    Source: script_math_model.md (skripsi BAB 3).
    """

    # Normalization ranges (math model §[2])
    RANGES: Dict[str, tuple] = {
        "bpm": (60, 180),
        "rms": (0.01, 0.50),
        "sc": (500, 5000),
        "mfcc1": (-300, 100),
        "onset_rate": (0.5, 8.0),
        "chroma_major": (0.0, 1.0),
    }

    # Chase timing rules (math model §[8])
    CHASE_TIMING_BRACKETS = (
        (120, 500),   # BPM > 120 → 500ms
        (90, 700),    # 90 ≤ BPM ≤ 120 → 700ms
        (0, 1500),    # BPM < 90 → 1500ms
    )

    # ────────────────────────────────────────────
    # STAGE 1: Load Audio
    # ────────────────────────────────────────────
    def stage_1_load_audio(self, audio_path: str) -> tuple:
        """STAGE 1: Load audio dengan librosa."""
        import librosa
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        return y, sr, duration

    # ────────────────────────────────────────────
    # STAGE 2: Extract Features
    # ────────────────────────────────────────────
    def stage_2_extract_features(self, y, sr) -> AudioFeatures:
        """STAGE 2: Extract 7 fitur audio. Lihat math model §[1]."""
        import librosa

        # Tempo / BPM
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        if hasattr(tempo, "__len__"):
            tempo = float(tempo[0])
        else:
            tempo = float(tempo)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        # RMS Energy
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = float(np.mean(rms))

        # Spectral Centroid
        sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        sc_mean = float(np.mean(sc))

        # MFCC (13 coefficients)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc1_mean = float(np.mean(mfcc[0]))

        # Chroma
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        major_indices = list(cm.MAJOR_INDICES)
        major_energy = float(np.sum(chroma_mean[major_indices]))
        total_energy = float(np.sum(chroma_mean))
        chroma_major = major_energy / total_energy if total_energy > 0 else 0.5
        chroma_peak = int(np.argmax(chroma_mean))

        # Onset
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        duration = float(librosa.get_duration(y=y, sr=sr))
        onset_rate = float(len(onset_frames) / duration) if duration > 0 else 0.0

        # Spectral Bandwidth (untuk display)
        sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        sb_mean = float(np.mean(sb))

        return AudioFeatures(
            duration=round(duration, 2),
            tempo=round(tempo, 1),
            rms_mean=round(rms_mean, 4),
            sc_mean=round(sc_mean, 1),
            mfcc1_mean=round(mfcc1_mean, 2),
            chroma_major=round(chroma_major, 4),
            chroma_peak=chroma_peak,
            onset_rate=round(onset_rate, 2),
            sb_mean=round(sb_mean, 1),
            beat_times=beat_times,
            rms_times=librosa.frames_to_time(np.arange(len(rms)), sr=sr).tolist(),
            rms_values=rms.tolist(),
            sc_times=librosa.frames_to_time(np.arange(len(sc)), sr=sr).tolist(),
            sc_values=sc.tolist(),
        )

    # ────────────────────────────────────────────
    # STAGE 3: Normalize
    # ────────────────────────────────────────────
    @staticmethod
    def _norm(v: float, key: str) -> float:
        """Min-max normalize sesuai math model §[2]."""
        lo, hi = AnalyzePipeline.RANGES.get(key, (0.0, 1.0))
        if hi == lo:
            return 0.5
        return max(0.0, min(1.0, (v - lo) / (hi - lo)))

    def stage_3_normalize(self, features: AudioFeatures) -> NormalizedFeatures:
        """STAGE 3: Normalize ke [0, 1]."""
        return NormalizedFeatures(
            bpm=self._norm(features.tempo, "bpm"),
            rms=self._norm(features.rms_mean, "rms"),
            sc=self._norm(features.sc_mean, "sc"),
            mfcc1=self._norm(features.mfcc1_mean, "mfcc1"),
            onset_rate=self._norm(features.onset_rate, "onset_rate"),
            chroma_major=features.chroma_major,  # already 0-1
        )

    # ────────────────────────────────────────────
    # STAGE 4: Compute V-A
    # ────────────────────────────────────────────
    def stage_4_compute_va(self, n: NormalizedFeatures) -> VAResult:
        """STAGE 4: V-A weighted sum. Lihat math model §[3]."""
        V, A = cm.compute_va(n.bpm, n.rms, n.onset_rate, n.chroma_major, n.sc, n.mfcc1)
        q = cm.get_quadrant(V, A)
        return VAResult(
            valence=round(V, 4),
            arousal=round(A, 4),
            quadrant=q,
            quadrant_name=cm.get_quadrant_name(q),
        )

    # ────────────────────────────────────────────
    # STAGE 5: Segment Song
    # ────────────────────────────────────────────
    def stage_5_segment(self, y, sr, duration: float) -> List[Segment]:
        """STAGE 5: SSM-based structural segmentation."""
        import librosa

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
        ssm = librosa.segment.recurrence_matrix(chroma, mode="affinity", sym=True)
        novelty = librosa.segment.novelty(ssm)

        # Peak picking
        peaks = []
        if len(novelty) > 2:
            threshold = float(np.mean(novelty)) + 0.5 * float(np.std(novelty))
            for i in range(1, len(novelty) - 1):
                if (
                    novelty[i] > threshold
                    and novelty[i] > novelty[i - 1]
                    and novelty[i] > novelty[i + 1]
                ):
                    peaks.append(i)

        boundary_times = librosa.frames_to_time(peaks, sr=sr, hop_length=512).tolist()
        boundary_times = [0.0] + boundary_times + [duration]

        if len(boundary_times) < 4:
            n = 4
            boundary_times = [duration * i / n for i in range(n + 1)]
        elif len(boundary_times) > 10:
            novelty_at_peaks = [novelty[p] for p in peaks]
            top_indices = np.argsort(novelty_at_peaks)[-7:]
            top_peaks = sorted([peaks[i] for i in top_indices])
            boundary_times = (
                [0.0] + librosa.frames_to_time(top_peaks, sr=sr, hop_length=512).tolist() + [duration]
            )

        # Build segments
        segments: List[Segment] = []
        total_segs = len(boundary_times) - 1
        global_rms_mean = float(np.mean(librosa.feature.rms(y=y)[0]))

        for i in range(total_segs):
            start = boundary_times[i]
            end = boundary_times[i + 1]
            seg_duration = end - start

            start_sample = int(start * sr)
            end_sample = min(int(end * sr), len(y))
            y_seg = y[start_sample:end_sample]

            if len(y_seg) < int(sr * 0.5):
                continue

            seg_rms = float(np.mean(librosa.feature.rms(y=y_seg)[0]))
            seg_sc = float(np.mean(librosa.feature.spectral_centroid(y=y_seg, sr=sr)[0]))

            rel_pos = (start + end) / 2 / duration
            if i == 0 and seg_duration < duration * 0.15:
                label = "intro"
            elif i == total_segs - 1 and seg_duration < duration * 0.15:
                label = "outro"
            elif seg_rms > global_rms_mean * 1.15:
                label = "chorus"
            elif 0.3 < rel_pos < 0.7 and seg_rms < global_rms_mean * 0.9:
                label = "bridge"
            else:
                label = "verse"

            segments.append(
                Segment(
                    index=i,
                    label=label,
                    start=round(start, 2),
                    end=round(end, 2),
                    duration=round(seg_duration, 2),
                    rms=round(seg_rms, 4),
                    sc=round(seg_sc, 1),
                )
            )

        return segments

    # ────────────────────────────────────────────
    # STAGE 6: Per-segment V-A + Color + Pattern
    # ────────────────────────────────────────────
    def stage_6_segment_color(
        self, segments: List[Segment], af: AudioFeatures,
        va_preset: Optional[VAPreset] = None,
    ) -> List[Segment]:
        """
        STAGE 6: Compute V-A + HSV + DRGBW + multi-fixture pattern per segment.

        Strategy: per-segment modulate arousal by local intensity ratio
        (segment_rms / global_rms) untuk reflect local dynamics.

        va_preset (v6 Phase 3): optional VAPreset override. If None, uses
        default hue ranges from color_mapping.va_to_hsv().
        """
        global_rms_norm = self._norm(af.rms_mean, "rms")

        for seg in segments:
            seg_rms_norm = self._norm(seg.rms, "rms")

            # Modulasi arousal: local RMS ratio applied to BPM
            rms_ratio = seg_rms_norm / max(global_rms_norm, 0.01)
            modulated_bpm = min(af.tempo * rms_ratio, 180.0)
            seg_bpm_norm = self._norm(modulated_bpm, "bpm")

            seg_n = NormalizedFeatures(
                bpm=seg_bpm_norm,
                rms=seg_rms_norm,
                sc=self._norm(seg.sc, "sc"),
                mfcc1=self._norm(af.mfcc1_mean, "mfcc1"),
                onset_rate=self._norm(af.onset_rate, "onset_rate"),
                chroma_major=af.chroma_major,
            )
            seg_va = self.stage_4_compute_va(seg_n)

            if va_preset is not None:
                H, S, V_hsv = apply_preset(
                    va_preset, seg_va.valence, seg_va.arousal,
                    af.chroma_peak, seg_rms_norm,
                )
            else:
                H, S, V_hsv = cm.va_to_hsv(
                    seg_va.valence, seg_va.arousal, af.chroma_peak, seg_rms_norm
                )
            seg_hsv = HSV(h=H, s=S, v=V_hsv)

            drgbw = cm.hsv_to_drgbw(H, S, V_hsv)
            seg_drgbw = DRGBW(
                dimmer=drgbw["dimmer"],
                r=drgbw["r"],
                g=drgbw["g"],
                b=drgbw["b"],
                w=drgbw["w"],
            )

            seg.va = seg_va
            seg.hsv = seg_hsv
            seg.drgbw = seg_drgbw
            seg.pattern = self._pick_pattern(seg_va.arousal, af.tempo)

        return segments

    # ────────────────────────────────────────────
    # STAGE 7: Chase Timing Rules
    # ────────────────────────────────────────────
    def stage_7_chase_timing(self, af: AudioFeatures) -> int:
        """STAGE 7: BPM-based chase timing (math model §[8])."""
        bpm = af.tempo
        for threshold, ms in self.CHASE_TIMING_BRACKETS:
            if bpm > threshold:
                return ms
        return 1500

    # ────────────────────────────────────────────
    # STAGE 8: Build Result
    # ────────────────────────────────────────────
    @staticmethod
    def _pick_pattern(arousal: float, bpm: float) -> str:
        """Pilih multi-fixture pattern (math model §[8] Pola Multi-Fixture)."""
        if arousal > 0.7:
            return "all_on"
        if bpm > 120:
            return "running"
        if arousal < 0.3:
            return "gradient"
        return "center_out"

    # ────────────────────────────────────────────
    # Public API
    # ────────────────────────────────────────────
    def run_with_features(
        self, features: AudioFeatures, va_preset: Optional[VAPreset] = None,
    ) -> AnalyzeResult:
        """
        Run pipeline dari pre-computed features (untuk testing / programmatic use).
        Skip STAGE 1, 2, 5, 6 (no audio data).
        """
        n = self.stage_3_normalize(features)
        va = self.stage_4_compute_va(n)
        if va_preset is not None:
            H, S, V_hsv = apply_preset(
                va_preset, va.valence, va.arousal, features.chroma_peak, n.rms,
            )
        else:
            H, S, V_hsv = cm.va_to_hsv(va.valence, va.arousal, features.chroma_peak, n.rms)
        hsv = HSV(h=H, s=S, v=V_hsv)
        drgbw_dict = cm.hsv_to_drgbw(H, S, V_hsv)
        drgbw = DRGBW(
            dimmer=drgbw_dict["dimmer"],
            r=drgbw_dict["r"],
            g=drgbw_dict["g"],
            b=drgbw_dict["b"],
            w=drgbw_dict["w"],
        )
        chase_timing = self.stage_7_chase_timing(features)
        return AnalyzeResult(
            filepath="<features>",
            filename="<features>",
            features=features,
            normalized=n,
            va=va,
            hsv=hsv,
            drgbw=drgbw,
            segments=[],
            chase_timing_ms=chase_timing,
        )

    def run(
        self, audio_path: str, progress: ProgressCallback = None,
        va_preset: Optional[VAPreset] = None,
    ) -> AnalyzeResult:
        """
        Run full 8-stage pipeline dari audio file.
        Emit progress (percent, message) via callback.
        va_preset (v6 Phase 3): optional VAPreset override for V-A → HSV mapping.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # STAGE 1
        if progress: progress(5, "Stage 1/3: Load audio waveform with librosa...")
        y, sr, duration = self.stage_1_load_audio(audio_path)

        # STAGE 2
        if progress: progress(20, "Stage 1/3: Extract spectral features (MFCC, centroid, tempo)...")
        af = self.stage_2_extract_features(y, sr)

        # STAGE 3
        if progress: progress(35, "Stage 1/3: Normalize features to [0,1]...")
        n = self.stage_3_normalize(af)

        # STAGE 4
        if progress: progress(50, "Stage 1/3: Compute Valence-Arousal (rule-based)...")
        va = self.stage_4_compute_va(n)

        # STAGE 5
        if progress: progress(65, "Stage 2/3: Segment song via self-similarity matrix (SSM)...")
        segments = self.stage_5_segment(y, sr, duration)

        # STAGE 6
        if progress: progress(78, "Stage 3/3: Map V-A to HSV per segment...")
        segments = self.stage_6_segment_color(segments, af, va_preset=va_preset)

        # STAGE 7
        if progress: progress(90, "Stage 3/3: Compute chase timing (BPM-based)...")
        chase_timing = self.stage_7_chase_timing(af)

        # STAGE 8
        if progress: progress(97, "Stage 3/3: Convert HSV to RGBW (8-bit DRGBW)...")
        if va_preset is not None:
            H, S, V_hsv = apply_preset(
                va_preset, va.valence, va.arousal, af.chroma_peak, n.rms,
            )
        else:
            H, S, V_hsv = cm.va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)
        hsv = HSV(h=H, s=S, v=V_hsv)
        drgbw_dict = cm.hsv_to_drgbw(H, S, V_hsv)
        drgbw = DRGBW(
            dimmer=drgbw_dict["dimmer"],
            r=drgbw_dict["r"],
            g=drgbw_dict["g"],
            b=drgbw_dict["b"],
            w=drgbw_dict["w"],
        )

        if progress: progress(100, "Analysis complete!")

        return AnalyzeResult(
            filepath=audio_path,
            filename=os.path.basename(audio_path),
            features=af,
            normalized=n,
            va=va,
            hsv=hsv,
            drgbw=drgbw,
            segments=segments,
            chase_timing_ms=chase_timing,
        )
