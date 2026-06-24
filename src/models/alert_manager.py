"""
Falcon — Alert Manager
Debounced alert system: only fires after sustained distraction.
Never beeps constantly — requires N consecutive seconds before alerting,
then enforces a cooldown before it can alert again.

Usage:
    from src.models.alert_manager import AlertManager
    alerts = AlertManager(sustain_sec=1.5, cooldown_sec=4.0)
    alerts.update(label, timestamp=time.time())  # call every frame
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable

try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False

try:
    import sounddevice as sd
    import numpy as np as _np
    _HAS_SD = True
except Exception:
    _HAS_SD = False


# Alert messages per label
ALERT_MESSAGES = {
    "distracted_left":  "Eyes on the road!",
    "distracted_right": "Eyes on the road!",
    "distracted_down":  "Watch ahead!",
    "distracted_up":    "Watch ahead!",
    "drowsy":           "Stay awake! Pull over if tired.",
}

SAFE_LABELS = {"attentive", "no_face"}


@dataclass
class AlertEvent:
    label:     str
    message:   str
    timestamp: float


class AlertManager:
    """
    Temporal debounce + cooldown alert engine.

    sustain_sec  : seconds of *continuous* distraction before alerting
    cooldown_sec : minimum gap between consecutive alerts
    on_alert     : optional callback(AlertEvent) for custom handling
    """

    def __init__(
        self,
        sustain_sec:  float = 1.5,
        cooldown_sec: float = 4.0,
        on_alert: Optional[Callable[[AlertEvent], None]] = None,
        beep: bool = True,
    ):
        self.sustain_sec  = sustain_sec
        self.cooldown_sec = cooldown_sec
        self.on_alert     = on_alert
        self.beep         = beep

        self._distract_start: Optional[float] = None  # when current distraction started
        self._last_alert:     Optional[float] = None  # when last alert fired
        self._current_label:  str = "attentive"
        self.last_event: Optional[AlertEvent] = None

    def update(self, label: str, timestamp: Optional[float] = None) -> Optional[AlertEvent]:
        """
        Call once per frame with the current label.
        Returns an AlertEvent if an alert fired, else None.
        """
        now = timestamp or time.time()

        if label in SAFE_LABELS:
            self._distract_start = None
            self._current_label  = label
            return None

        # Start / reset distraction timer when label changes
        if label != self._current_label:
            self._distract_start = now
            self._current_label  = label
        elif self._distract_start is None:
            self._distract_start = now

        sustained = now - self._distract_start

        # Not yet sustained long enough
        if sustained < self.sustain_sec:
            return None

        # In cooldown from last alert
        if self._last_alert and (now - self._last_alert) < self.cooldown_sec:
            return None

        # ── FIRE ──
        self._last_alert = now
        event = AlertEvent(
            label=label,
            message=ALERT_MESSAGES.get(label, "Pay attention!"),
            timestamp=now,
        )
        self.last_event = event

        if self.on_alert:
            self.on_alert(event)

        if self.beep:
            threading.Thread(target=self._play_beep, daemon=True).start()

        return event

    def sustain_progress(self) -> float:
        """0.0 → 1.0 progress bar toward triggering an alert (for UI overlay)."""
        if self._distract_start is None or self._current_label in SAFE_LABELS:
            return 0.0
        elapsed = time.time() - self._distract_start
        return min(elapsed / self.sustain_sec, 1.0)

    def in_cooldown(self) -> bool:
        if self._last_alert is None:
            return False
        return (time.time() - self._last_alert) < self.cooldown_sec

    @staticmethod
    def _play_beep():
        """Cross-platform beep: winsound on Windows, generated tone elsewhere."""
        try:
            if _HAS_WINSOUND:
                winsound.Beep(880, 400)  # 880 Hz, 400 ms
            elif _HAS_SD:
                t = _np.linspace(0, 0.4, int(44100 * 0.4), endpoint=False)
                wave = 0.3 * _np.sin(2 * _np.pi * 880 * t).astype(_np.float32)
                sd.play(wave, samplerate=44100)
                sd.wait()
        except Exception:
            pass  # silent fallback — never crash on beep
