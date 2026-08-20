"""
zzluxora — Scene & Chase Generator
Generates DRGBW scenes and chases from audio analysis results.
"""

import numpy as np
from .audio_engine import full_pipeline, normalize, compute_valence_arousal, extract_features


def generate_scenes(segments, global_features, fixture_count=4):
    """Generate DRGBW scenes for each segment.

    Args:
        segments: list of segment dicts from segment_song()
        global_features: dict from extract_features()
        fixture_count: number of PAR LED fixtures

    Returns:
        list of scene dicts with DRGBW values per fixture
    """
    scenes = []
    global_rms = global_features['rms_mean']

    for seg in segments:
        # Build per-segment feature dict
        seg_features = {
            'tempo': global_features['tempo'],
            'rms_mean': seg['rms'],
            'sc_mean': seg['sc'],
            'mfcc1_mean': global_features['mfcc1_mean'],
            'onset_rate': global_features['onset_rate'],
            'chroma_major': global_features['chroma_major'],
            'chroma_peak': global_features.get('chroma_peak', 6),
        }

        result = full_pipeline(seg_features)
        D, R, G, B, W = result['drgbw']
        label = seg['label']
        bpm = global_features['tempo']

        # Determine pattern based on segment label
        fixtures = []
        if label == 'chorus':
            # All fixtures on, full brightness
            for f in range(fixture_count):
                fixtures.append({'fixture': f + 1, 'd': D, 'r': R, 'g': G, 'b': B, 'w': W})
        elif label == 'verse':
            # 1-2 fixtures, dimmer
            active = max(1, fixture_count // 3)
            for f in range(fixture_count):
                if f < active:
                    d_adj = max(30, int(D * 0.6))
                    fixtures.append({'fixture': f + 1, 'd': d_adj, 'r': R, 'g': G, 'b': B, 'w': W})
                else:
                    fixtures.append({'fixture': f + 1, 'd': 0, 'r': 0, 'g': 0, 'b': 0, 'w': 0})
        elif label == 'bridge':
            # Gradient pattern
            for f in range(fixture_count):
                factor = 1.0 - (f / max(fixture_count - 1, 1)) * 0.5
                d_adj = max(20, int(D * factor))
                fixtures.append({'fixture': f + 1, 'd': d_adj, 'r': R, 'g': G, 'b': B, 'w': W})
        elif label == 'intro':
            # Only first fixture, low brightness
            for f in range(fixture_count):
                if f == 0:
                    d_adj = max(20, int(D * 0.4))
                    fixtures.append({'fixture': f + 1, 'd': d_adj, 'r': R, 'g': G, 'b': B, 'w': W})
                else:
                    fixtures.append({'fixture': f + 1, 'd': 0, 'r': 0, 'g': 0, 'b': 0, 'w': 0})
        elif label == 'outro':
            # Fade out - one fixture dimly
            for f in range(fixture_count):
                if f == 0:
                    d_adj = max(10, int(D * 0.25))
                    fixtures.append({'fixture': f + 1, 'd': d_adj, 'r': R, 'g': G, 'b': B, 'w': W})
                else:
                    fixtures.append({'fixture': f + 1, 'd': 0, 'r': 0, 'g': 0, 'b': 0, 'w': 0})
        else:
            for f in range(fixture_count):
                fixtures.append({'fixture': f + 1, 'd': D, 'r': R, 'g': G, 'b': B, 'w': W})

        # Determine fade time based on BPM and segment
        if label == 'chorus' and bpm > 120:
            fade_ms = 300
        elif label == 'chorus':
            fade_ms = 500
        elif label in ('intro', 'outro'):
            fade_ms = 3000
        elif label == 'bridge':
            fade_ms = 2000
        elif bpm > 120:
            fade_ms = 500
        elif bpm < 90:
            fade_ms = 2000
        else:
            fade_ms = 1000

        scenes.append({
            'index': seg['index'],
            'label': label,
            'start': seg['start'],
            'end': seg['end'],
            'duration': seg['duration'],
            'fade_ms': fade_ms,
            'color': result['hex'],
            'valence': result['valence'],
            'arousal': result['arousal'],
            'hue': result['hue'],
            'fixtures': fixtures,
        })

    return scenes


def generate_running_chase(base_drgbw, fixture_count=4, bpm=120):
    """Generate a running chase (one fixture at a time, rotating)."""
    D, R, G, B, W = base_drgbw
    chase_scenes = []
    beat_ms = int(60000 / max(bpm, 60))

    for active in range(fixture_count):
        fixtures = []
        for f in range(fixture_count):
            if f == active:
                fixtures.append({'fixture': f + 1, 'd': D, 'r': R, 'g': G, 'b': B, 'w': W})
            else:
                fixtures.append({'fixture': f + 1, 'd': 0, 'r': 0, 'g': 0, 'b': 0, 'w': 0})
        chase_scenes.append({
            'fixtures': fixtures,
            'hold_ms': beat_ms,
            'fade_ms': min(100, beat_ms // 4),
        })

    return chase_scenes


def scenes_to_dmx(scenes, channels_per_fixture=8):
    """Convert scenes to flat DMX channel arrays (512 channels max).

    Fixture channel mapping: ch1=dimmer, ch2=red, ch3=green, ch4=blue,
    ch5=0, ch6=0, ch7=0, ch8=0  (white goes to ch5 if available)
    """
    dmx_frames = []
    for scene in scenes:
        dmx = [0] * 512
        for fix in scene.get('fixtures', []):
            base_ch = (fix['fixture'] - 1) * channels_per_fixture
            if base_ch + channels_per_fixture <= 512:
                dmx[base_ch + 0] = fix['d']     # CH1 Dimmer
                dmx[base_ch + 1] = fix['r']     # CH2 Red
                dmx[base_ch + 2] = fix['g']     # CH3 Green
                dmx[base_ch + 3] = fix['b']     # CH4 Blue
                dmx[base_ch + 4] = fix.get('w', 0)  # CH5 White
                # CH6-CH8 remain 0
        dmx_frames.append({
            'dmx': dmx,
            'fade_ms': scene.get('fade_ms', 1000),
            'hold_ms': int(scene.get('duration', 5) * 1000) if 'duration' in scene else 5000,
            'label': scene.get('label', ''),
        })
    return dmx_frames
