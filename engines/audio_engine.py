"""
zzluxora — Audio Engine
Extracts audio features, computes Valence-Arousal, maps to HSV-RGBW.
"""

import numpy as np
import librosa
import os


def extract_features(audio_path):
    """Extract audio features using librosa. Returns dict of features."""
    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # Tempo / BPM
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
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
    major_indices = [0, 2, 4, 5, 7, 9, 11]
    major_energy = float(np.sum(chroma_mean[major_indices]))
    total_energy = float(np.sum(chroma_mean))
    chroma_major = major_energy / total_energy if total_energy > 0 else 0.5
    chroma_peak = int(np.argmax(chroma_mean))

    # Onset
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = float(len(onset_frames) / duration) if duration > 0 else 0

    # Spectral Bandwidth
    sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    sb_mean = float(np.mean(sb))

    # RMS over time (for visualization)
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr).tolist()
    rms_values = rms.tolist()

    # SC over time
    sc_times = librosa.frames_to_time(np.arange(len(sc)), sr=sr).tolist()
    sc_values = sc.tolist()

    return {
        'duration': round(duration, 2),
        'tempo': round(tempo, 1),
        'beat_times': beat_times,
        'rms_mean': round(rms_mean, 4),
        'rms_times': rms_times,
        'rms_values': rms_values,
        'sc_mean': round(sc_mean, 1),
        'sc_times': sc_times,
        'sc_values': sc_values,
        'mfcc1_mean': round(mfcc1_mean, 2),
        'chroma_major': round(chroma_major, 4),
        'chroma_peak': chroma_peak,
        'chroma_mean': chroma_mean.tolist(),
        'onset_rate': round(onset_rate, 2),
        'sb_mean': round(sb_mean, 1),
    }


def segment_song(audio_path, num_segments=None):
    """Segment song into structural sections using SSM + heuristic."""
    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # Compute chroma for self-similarity
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    # Self-similarity matrix
    ssm = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)

    # Use spectral clustering-like approach via novelty curve
    novelty = librosa.segment.novelty(ssm)
    # Find peaks in novelty = segment boundaries
    peaks = []
    threshold = np.mean(novelty) + 0.5 * np.std(novelty)
    for i in range(1, len(novelty) - 1):
        if novelty[i] > threshold and novelty[i] > novelty[i-1] and novelty[i] > novelty[i+1]:
            peaks.append(i)

    # Convert frames to times
    boundary_times = librosa.frames_to_time(peaks, sr=sr, hop_length=512).tolist()
    boundary_times = [0.0] + boundary_times + [duration]

    # Ensure reasonable number of segments (3-8)
    if len(boundary_times) < 4:
        # Too few boundaries, split evenly
        n = 4
        boundary_times = [duration * i / n for i in range(n + 1)]
    elif len(boundary_times) > 10:
        # Too many, keep strongest
        novelty_at_peaks = [novelty[p] for p in peaks]
        top_indices = np.argsort(novelty_at_peaks)[-7:]
        top_peaks = sorted([peaks[i] for i in top_indices])
        boundary_times = [0.0] + librosa.frames_to_time(top_peaks, sr=sr, hop_length=512).tolist() + [duration]

    # Label segments heuristically based on energy and position
    segments = []
    total_segs = len(boundary_times) - 1
    for i in range(total_segs):
        start = boundary_times[i]
        end = boundary_times[i + 1]
        seg_duration = end - start

        # Extract features for this segment
        start_sample = int(start * sr)
        end_sample = min(int(end * sr), len(y))
        y_seg = y[start_sample:end_sample]

        if len(y_seg) < sr * 0.5:
            continue

        seg_rms = float(np.mean(librosa.feature.rms(y=y_seg)[0]))
        seg_sc = float(np.mean(librosa.feature.spectral_centroid(y=y_seg, sr=sr)[0]))

        # Heuristic labeling based on position and energy
        rel_pos = (start + end) / 2 / duration  # relative position 0-1
        if i == 0 and seg_duration < duration * 0.15:
            label = 'intro'
        elif i == total_segs - 1 and seg_duration < duration * 0.15:
            label = 'outro'
        elif seg_rms > np.mean(librosa.feature.rms(y=y)[0]) * 1.15:
            label = 'chorus'
        elif 0.3 < rel_pos < 0.7 and seg_rms < np.mean(librosa.feature.rms(y=y)[0]) * 0.9:
            label = 'bridge'
        else:
            label = 'verse'

        segments.append({
            'index': i,
            'label': label,
            'start': round(start, 2),
            'end': round(end, 2),
            'duration': round(seg_duration, 2),
            'rms': round(seg_rms, 4),
            'sc': round(seg_sc, 1),
        })

    return segments


# === NORMALIZATION ===
RANGES = {
    'tempo': (60, 180),
    'rms_mean': (0.01, 0.50),
    'sc_mean': (500, 5000),
    'mfcc1_mean': (-300, 100),
    'onset_rate': (0.5, 8.0),
    'chroma_major': (0.0, 1.0),
}


def normalize(value, key):
    """Min-max normalize a value to [0, 1]."""
    lo, hi = RANGES.get(key, (0, 1))
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def compute_valence_arousal(features):
    """Compute V-A from normalized features. Returns (V, A) in [0,1]."""
    bpm_n = normalize(features['tempo'], 'tempo')
    rms_n = normalize(features['rms_mean'], 'rms_mean')
    sc_n = normalize(features['sc_mean'], 'sc_mean')
    mfcc1_n = normalize(features['mfcc1_mean'], 'mfcc1_mean')
    onset_n = normalize(features['onset_rate'], 'onset_rate')
    chroma_n = features['chroma_major']  # already 0-1

    # Arousal
    A = 0.40 * bpm_n + 0.35 * rms_n + 0.25 * onset_n

    # Valence
    V = 0.50 * chroma_n + 0.30 * sc_n + 0.20 * (1.0 - abs(mfcc1_n - 0.5) * 2)

    return round(float(V), 4), round(float(A), 4)


def va_to_hsv(V, A, chroma_peak=6, rms_norm=0.5):
    """Map Valence-Arousal to HSV color space."""
    # Hue
    if V > 0.5 and A > 0.5:
        H_base = 30 + (V - 0.5) * 60
    elif V <= 0.5 and A > 0.5:
        H_base = 270 + (0.5 - V) * 120
    elif V <= 0.5 and A <= 0.5:
        H_base = 200 + (0.5 - V) * 120
    else:
        H_base = 150 + (V - 0.5) * 100

    H = (H_base + (chroma_peak - 6) * 5) % 360

    # Saturation
    S = 0.6 * A + 0.4 * abs(2 * V - 1)
    S = max(0.1, min(1.0, S))

    # Value (brightness)
    Vhsv = 0.5 * rms_norm + 0.5 * A
    Vhsv = max(0.10, min(1.0, Vhsv))

    return round(H, 1), round(S, 4), round(Vhsv, 4)


def hsv_to_rgb(H, S, V):
    """Standard HSV to RGB conversion (Foley & van Dam). Returns (R,G,B) in [0,1]."""
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

    return R1 + m, G1 + m, B1 + m


def rgb_to_rgbw(R, G, B):
    """Extract white channel from RGB. Returns (R', G', B', W) in [0,1]."""
    W = min(R, G, B)
    return R - W, G - W, B - W, W


def full_pipeline(features):
    """Run full audio→RGBW pipeline. Returns dict with all intermediate values."""
    V, A = compute_valence_arousal(features)
    rms_n = normalize(features['rms_mean'], 'rms_mean')
    H, S, Vhsv = va_to_hsv(V, A, features.get('chroma_peak', 6), rms_n)
    R, G, B = hsv_to_rgb(H, S, Vhsv)
    Rp, Gp, Bp, W = rgb_to_rgbw(R, G, B)

    D = int(round(Vhsv * 255))
    R_out = int(round(Rp * 255))
    G_out = int(round(Gp * 255))
    B_out = int(round(Bp * 255))
    W_out = int(round(W * 255))

    return {
        'valence': V,
        'arousal': A,
        'hue': H,
        'saturation': S,
        'value': Vhsv,
        'rgb': [round(R, 4), round(G, 4), round(B, 4)],
        'rgbw': [R_out, G_out, B_out, W_out],
        'dimmer': D,
        'drgbw': [D, R_out, G_out, B_out, W_out],
        'hex': f'#{int(R*255):02x}{int(G*255):02x}{int(B*255):02x}',
    }
