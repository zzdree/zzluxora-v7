"""
zzluxora — Art-Net Sender
Wraps stupidArtnet for sending DMX data via Art-Net UDP.
"""

import threading
import time

try:
    from stupidArtnet import StupidArtnet
    HAS_ARTNET = True
except ImportError:
    HAS_ARTNET = False


class ArtNetController:
    """Controls Art-Net output to a target IP (QLC+ virtual adapter or ESP32)."""

    def __init__(self):
        self.artnet = None
        self.target_ip = '127.0.0.1'
        self.universe = 0
        self.fps = 30
        self.is_running = False
        self.is_playing = False
        self.play_thread = None
        self.current_dmx = [0] * 512
        self.chase_frames = []
        self.chase_index = 0
        self.stop_event = threading.Event()
        self.frames_sent = 0

    def connect(self, target_ip='127.0.0.1', universe=0, fps=30):
        """Initialize Art-Net connection."""
        if not HAS_ARTNET:
            return {'ok': False, 'error': 'stupidArtnet not installed'}

        self.target_ip = target_ip
        self.universe = universe
        self.fps = fps

        try:
            if self.artnet:
                self.artnet.stop()
            self.artnet = StupidArtnet(target_ip, universe, 512, fps, True, True)
            self.artnet.start()
            self.is_running = True
            return {'ok': True, 'ip': target_ip, 'universe': universe}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def send_frame(self, dmx_data):
        """Send a single DMX frame (list of 512 ints)."""
        if not self.artnet or not self.is_running:
            return False
        self.current_dmx = list(dmx_data[:512])
        packet = bytearray(self.current_dmx)
        self.artnet.set(packet)
        self.frames_sent += 1
        return True

    def blackout(self):
        """Send all zeros."""
        self.send_frame([0] * 512)

    def play_chase(self, frames):
        """Play a chase sequence in a background thread.

        Args:
            frames: list of dicts with 'dmx' (list), 'hold_ms' (int), 'fade_ms' (int)
        """
        self.stop_chase()
        self.chase_frames = frames
        self.chase_index = 0
        self.stop_event.clear()
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._chase_loop, daemon=True)
        self.play_thread.start()

    def _chase_loop(self):
        """Internal chase playback loop."""
        while not self.stop_event.is_set() and self.chase_frames:
            frame = self.chase_frames[self.chase_index]
            dmx = frame['dmx']
            hold_ms = frame.get('hold_ms', 1000)
            fade_ms = frame.get('fade_ms', 500)

            # Simple fade: interpolate from current to target
            start_dmx = list(self.current_dmx)
            target_dmx = list(dmx)
            fade_steps = max(1, fade_ms // 33)  # ~30fps fade

            for step in range(fade_steps):
                if self.stop_event.is_set():
                    return
                t = (step + 1) / fade_steps
                interp = [int(start_dmx[i] + (target_dmx[i] - start_dmx[i]) * t) for i in range(512)]
                self.send_frame(interp)
                time.sleep(0.033)

            # Hold
            self.send_frame(target_dmx)
            hold_elapsed = 0
            while hold_elapsed < hold_ms and not self.stop_event.is_set():
                time.sleep(0.05)
                hold_elapsed += 50

            # Next frame
            self.chase_index = (self.chase_index + 1) % len(self.chase_frames)

        self.is_playing = False

    def stop_chase(self):
        """Stop chase playback."""
        self.stop_event.set()
        self.is_playing = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=2)
        self.play_thread = None

    def disconnect(self):
        """Stop Art-Net and cleanup."""
        self.stop_chase()
        if self.artnet:
            self.blackout()
            time.sleep(0.1)
            self.artnet.stop()
            self.artnet = None
        self.is_running = False

    def get_status(self):
        """Return current status dict."""
        return {
            'connected': self.is_running,
            'playing': self.is_playing,
            'target_ip': self.target_ip,
            'universe': self.universe,
            'fps': self.fps,
            'frames_sent': self.frames_sent,
            'chase_index': self.chase_index,
            'chase_total': len(self.chase_frames),
        }

    def scan(self, timeout_s: float = 3.0) -> list:
        """Phase 12: ArtPoll broadcast scan. Returns list of {ip, name} dicts.

        Sends ArtPoll packet (OpPoll = 0x2000) to UDP broadcast :6454,
        collects ArtPollReply packets (OpPollReply = 0x2100) for up to
        `timeout_s` seconds. Returns de-duped list of nodes (keeps first
        reply per IP).
        """
        import socket
        import struct
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.3)
            # ArtPoll packet: ID(8) + OpCode(2) + ProtVer(1) + TalkToMe(1) + Priority(1) + pad(4)
            poll = struct.pack('<8sHBB', b'Art-Net\x00', 0x2000, 0, 0) + b'\x00' * 6
            try:
                sock.sendto(poll, ('<broadcast>', 6454))
            except OSError:
                return []
            nodes: dict = {}
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                try:
                    data, _addr = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if len(data) < 18:
                    continue
                if data[:8] != b'Art-Net\x00' or data[8:10] != b'\x00\x21':
                    continue  # not an ArtPollReply
                ip = f"{data[10]}.{data[11]}.{data[12]}.{data[13]}"
                # ShortName bytes 18-33 (16 bytes), null-terminated
                try:
                    name = data[18:34].split(b'\x00', 1)[0].decode('ascii', 'ignore') or ip
                except UnicodeDecodeError:
                    name = ip
                if ip not in nodes:
                    nodes[ip] = {'ip': ip, 'name': name}
            return list(nodes.values())
        except Exception:
            return []
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def reset_counter(self):
        """Reset the frames_sent counter (e.g., on connect)."""
        self.frames_sent = 0
