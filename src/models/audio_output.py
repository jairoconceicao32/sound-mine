import ctypes
import logging
import threading
import time
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

CHANNELS = 2
FALLBACK_RATE = 44100
WASAPI = "WASAPI"
DIRECTSOUND = "DirectSound"
STATE_ERROR = 1
STALL_CHECKS = 2
STABLE_SECONDS = 2.0
MIN_SWITCH_SECONDS = 5.0
RETRY_SECONDS = (2.0, 4.0, 8.0, 16.0, 30.0)
WAVE_MAPPER = 0xFFFFFFFF
DRVM_MAPPER_PREFERRED_GET = 0x2015
MAX_WINDOWS_NAME = 31


@dataclass(frozen=True)
class OutputDevice:
    name: str
    rate: int


class OutputStatus(Enum):
    READY = "ready"
    WAITING = "waiting"
    FAILED = "failed"


class Reason(Enum):
    FAILURE = "failure"
    DEFAULT_CHANGED = "default_changed"
    RETURN = "return"
    RETRY = "retry"


def matches_windows_name(full_name: str, windows_name: str | None) -> bool:
    if not windows_name:
        return False
    return full_name == windows_name or full_name.startswith(windows_name[:MAX_WINDOWS_NAME])


def output_message(device: OutputDevice | None, returned: bool = False) -> str:
    if device is None:
        return "Nenhuma saída de som disponível."
    if returned:
        return f"Saída de som de volta: {device.name}."
    return f"Saída de som: {device.name}."


class PortAudioOutput:
    def __init__(self, callback: Callable, on_failure: Callable[[], None], wasapi: bool) -> None:
        self._client_callback = callback
        self._on_failure = on_failure
        self.wasapi = wasapi
        self.stream = None
        self.beats = 0
        self._last_beats = -1
        self._stalls = 0
        self._closing = False
        self._state_handler = None
        self.watch_beats = not wasapi

    def callback(self, outdata, frames, time_info, status) -> None:
        self.beats += 1
        self._client_callback(outdata, frames, time_info, status)

    def finished(self) -> None:
        if not self._closing:
            self._on_failure()

    def state_changed(self, stream, flags, error_id, user_data) -> None:
        if flags & STATE_ERROR and not self._closing:
            self._on_failure()

    def attach_state_handler(self, sounddevice) -> None:
        try:
            library = ctypes.CDLL(sounddevice._libname)
            handler_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p)
            handler = handler_type(self.state_changed)
            setter = library.PaWasapi_SetStreamStateHandler
            setter.argtypes = [ctypes.c_void_p, handler_type, ctypes.c_void_p]
            setter.restype = ctypes.c_int
            pointer = int(sounddevice._ffi.cast("uintptr_t", self.stream._ptr))
            if setter(pointer, handler, None) == 0:
                self._state_handler = handler
                return
        except Exception:
            logger.warning("Aviso de estado do WASAPI indisponível.", exc_info=True)
        self.watch_beats = True

    def healthy(self) -> bool:
        if self.stream is None:
            return False
        try:
            if not self.stream.active:
                return False
        except Exception:
            logger.warning("Falha ao consultar o estado da saída de áudio.", exc_info=True)
            return False
        if not self.watch_beats:
            return True
        if self.beats == self._last_beats:
            self._stalls += 1
        else:
            self._stalls = 0
        self._last_beats = self.beats
        return self._stalls < STALL_CHECKS

    def close(self) -> None:
        self._closing = True
        stream, self.stream = self.stream, None
        if stream is None:
            return
        for action in ("abort", "close"):
            try:
                getattr(stream, action)()
            except Exception:
                logger.warning("Falha ao liberar a saída de áudio (%s).", action, exc_info=True)
        self._state_handler = None


class PortAudioBackend:
    def _sounddevice(self):
        try:
            import sounddevice
            return sounddevice
        except Exception:
            logger.exception("Biblioteca de reprodução indisponível.")
            return None

    def available(self) -> list[OutputDevice]:
        sounddevice = self._sounddevice()
        if sounddevice is None:
            return []
        try:
            apis = sounddevice.query_hostapis()
            return [
                OutputDevice(device["name"], int(device["default_samplerate"]))
                for device in sounddevice.query_devices()
                if device["max_output_channels"] > 0 and WASAPI in apis[device["hostapi"]]["name"]
            ]
        except Exception:
            logger.warning("Não foi possível listar as saídas de áudio.", exc_info=True)
            return []

    def default_device(self) -> OutputDevice | None:
        sounddevice = self._sounddevice()
        if sounddevice is None:
            return None
        try:
            for api in sounddevice.query_hostapis():
                index = api["default_output_device"]
                if WASAPI in api["name"] and index >= 0:
                    device = sounddevice.query_devices(index)
                    return OutputDevice(device["name"], int(device["default_samplerate"]))
            device = sounddevice.query_devices(kind="output")
            return OutputDevice(device["name"], int(device["default_samplerate"]))
        except Exception:
            logger.warning("Não foi possível consultar a saída de áudio padrão.", exc_info=True)
            return None

    def windows_snapshot(self) -> tuple[str | None, tuple[str, ...]] | None:
        try:
            winmm = ctypes.WinDLL("winmm")
            winmm.waveOutMessage.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p]
            names = tuple(name for name in (_wave_out_name(winmm, device)
                                            for device in range(winmm.waveOutGetNumDevs())) if name)
            preferred = wintypes.UINT()
            status = wintypes.DWORD()
            result = winmm.waveOutMessage(ctypes.c_void_p(WAVE_MAPPER), DRVM_MAPPER_PREFERRED_GET,
                                          ctypes.byref(preferred), ctypes.byref(status))
            default = _wave_out_name(winmm, preferred.value) if result == 0 else None
            return default, names
        except Exception:
            logger.warning("Não foi possível consultar as saídas de áudio do Windows.", exc_info=True)
            return None

    def restart(self) -> None:
        sounddevice = self._sounddevice()
        if sounddevice is None:
            return
        sounddevice._terminate()
        sounddevice._initialize()

    def open(self, device: OutputDevice | None, rate: int, callback: Callable,
             on_failure: Callable[[], None]) -> PortAudioOutput | None:
        sounddevice = self._sounddevice()
        if sounddevice is None:
            return None
        attempts = []
        if device is not None:
            if device.rate == rate:
                attempts.append((self._index(sounddevice, device.name, WASAPI), WASAPI))
            attempts.append((self._index(sounddevice, device.name, DIRECTSOUND), DIRECTSOUND))
        attempts.append((None, "padrão"))
        for index, api in attempts:
            if index is None and api != "padrão":
                continue
            output = PortAudioOutput(callback, on_failure, api == WASAPI)
            try:
                output.stream = sounddevice.OutputStream(
                    device=index,
                    samplerate=rate,
                    channels=CHANNELS,
                    dtype="float32",
                    latency="low",
                    extra_settings=sounddevice.WasapiSettings() if api == WASAPI else None,
                    callback=output.callback,
                    finished_callback=output.finished,
                )
                if api == WASAPI:
                    output.attach_state_handler(sounddevice)
                output.stream.start()
                return output
            except Exception:
                logger.warning("Saída de áudio indisponível (%s, %s Hz).", api, rate, exc_info=True)
                output.close()
        return None

    @staticmethod
    def _index(sounddevice, name: str, api_name: str) -> int | None:
        try:
            apis = sounddevice.query_hostapis()
            for index, device in enumerate(sounddevice.query_devices()):
                if (device["max_output_channels"] > 0 and device["name"] == name
                        and api_name in apis[device["hostapi"]]["name"]):
                    return index
        except Exception:
            logger.warning("Não foi possível localizar a saída de áudio.", exc_info=True)
        return None


class _WaveOutCaps(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("dwFormats", wintypes.DWORD),
        ("wChannels", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]


def _wave_out_name(winmm, device: int) -> str | None:
    caps = _WaveOutCaps()
    if winmm.waveOutGetDevCapsW(device, ctypes.byref(caps), ctypes.sizeof(caps)) != 0:
        return None
    return caps.szPname


class OutputCoordinator:
    def __init__(self, backend=None, clock: Callable[[], float] = time.monotonic) -> None:
        self._backend = backend or PortAudioBackend()
        self._clock = clock
        self._clients: list = []
        self._outputs: dict = {}
        self._failure = threading.Event()
        self._listener: Callable[[str], None] | None = None
        self._last_switch = float("-inf")
        self._seen_since: float | None = None
        self._retry_at: float | None = None
        self._retry_step = 0
        self._devices_found = False
        self.current = self._backend.default_device()
        self.preferred = self.current.name if self.current is not None else None
        self._snapshot = self._backend.windows_snapshot()

    def set_listener(self, listener: Callable[[str], None] | None) -> None:
        self._listener = listener

    def status_text(self) -> str:
        return output_message(self.current)

    def rate(self) -> int:
        return self.current.rate if self.current is not None else FALLBACK_RATE

    def has_output(self, client) -> bool:
        return self._outputs.get(client) is not None

    def register(self, client) -> bool:
        if client not in self._clients:
            self._clients.append(client)
        if self.current is not None:
            self._outputs[client] = self._open(client, self.current)
        if self._outputs.get(client) is None:
            self._switch(Reason.FAILURE, announce=False)
        return self.has_output(client)

    def unregister(self, client) -> None:
        output = self._outputs.pop(client, None)
        if output is not None:
            output.close()
        if client in self._clients:
            self._clients.remove(client)

    def close(self) -> None:
        for client in list(self._clients):
            self.unregister(client)

    def ensure(self, client) -> OutputStatus:
        output = self._outputs.get(client)
        if output is not None and output.healthy():
            return OutputStatus.READY
        self._switch(Reason.FAILURE)
        if self.has_output(client):
            return OutputStatus.READY
        return OutputStatus.FAILED if self._devices_found else OutputStatus.WAITING

    def signal_failure(self) -> None:
        self._failure.set()

    def check(self) -> None:
        now = self._clock()
        if self._failure.is_set() or any(output is not None and not output.healthy()
                                         for output in self._outputs.values()):
            self._failure.clear()
            self._switch(Reason.FAILURE)
            return
        snapshot = self._backend.windows_snapshot()
        previous, self._snapshot = self._snapshot, snapshot if snapshot is not None else self._snapshot
        if self._is_deliberate_change(previous, snapshot):
            self._switch(Reason.DEFAULT_CHANGED)
            return
        if self.current is None:
            if self._retry_at is not None and now >= self._retry_at:
                self._switch(Reason.RETRY)
            return
        if self.preferred is None or self.current.name == self.preferred:
            self._seen_since = None
            return
        if snapshot is None or not any(matches_windows_name(self.preferred, name) for name in snapshot[1]):
            self._seen_since = None
            return
        if self._seen_since is None:
            self._seen_since = now
            return
        if now - self._seen_since >= STABLE_SECONDS and now - self._last_switch >= MIN_SWITCH_SECONDS:
            self._seen_since = None
            self._switch(Reason.RETURN)

    @staticmethod
    def _is_deliberate_change(previous, snapshot) -> bool:
        if previous is None or snapshot is None:
            return False
        old_default, old_names = previous
        new_default, new_names = snapshot
        if not new_default or new_default == old_default:
            return False
        return new_default in old_names and (old_default is None or old_default in new_names)

    def _switch(self, reason: Reason, announce: bool = True) -> None:
        previous = self.current
        for client in self._clients:
            output = self._outputs.pop(client, None)
            if output is not None:
                output.close()
        self._failure.clear()
        try:
            self._backend.restart()
        except Exception:
            logger.exception("Falha ao reiniciar a biblioteca de áudio.")
        devices = self._backend.available()
        self._devices_found = bool(devices)
        default = self._backend.default_device()
        if reason is Reason.DEFAULT_CHANGED and default is not None:
            self.preferred = default.name
        target = self._choose(devices, default, reason, previous)
        opened = False
        if target is not None:
            for client in self._clients:
                self._outputs[client] = self._open(client, target)
                opened = opened or self._outputs[client] is not None
        self.current = target if opened or not self._clients else None
        self._snapshot = self._backend.windows_snapshot() or self._snapshot
        now = self._clock()
        self._last_switch = now
        if self.current is None:
            delay = RETRY_SECONDS[min(self._retry_step, len(RETRY_SECONDS) - 1)]
            self._retry_step += 1
            self._retry_at = now + delay
        else:
            self._retry_step = 0
            self._retry_at = None
        changed = (previous is None) != (self.current is None) or (
            previous is not None and self.current is not None and previous.name != self.current.name)
        if announce and changed and self._listener is not None:
            returned = reason is Reason.RETURN and self.current is not None and self.current.name == self.preferred
            self._listener(output_message(self.current, returned))

    def _choose(self, devices: list[OutputDevice], default: OutputDevice | None, reason: Reason,
                previous: OutputDevice | None) -> OutputDevice | None:
        by_name = {device.name: device for device in devices}
        if reason is Reason.DEFAULT_CHANGED and default is not None:
            return by_name.get(default.name, default)
        if self.preferred in by_name:
            return by_name[self.preferred]
        if reason is Reason.RETURN and previous is not None and previous.name in by_name:
            return by_name[previous.name]
        if default is not None:
            return by_name.get(default.name, default)
        return devices[0] if devices else None

    def _open(self, client, device: OutputDevice):
        try:
            rate = client.prepare_output(device)
            return self._backend.open(device, rate, client.audio_callback, self.signal_failure)
        except Exception:
            logger.exception("Falha ao abrir a saída de áudio.")
            return None
