import unittest

from src.models.audio_output import (
    MIN_SWITCH_SECONDS,
    STABLE_SECONDS,
    OutputCoordinator,
    OutputDevice,
    OutputStatus,
    PortAudioOutput,
    matches_windows_name,
    output_message,
)

HEADSET = OutputDevice("Fone de ouvido do headset (JBL Quantum 400 Chat)", 48000)
SPEAKERS = OutputDevice("Alto-falantes (High Definition Audio Device)", 48000)
OTHER_RATE = OutputDevice("Alto-falantes (USB)", 44100)


def windows_name(device: OutputDevice) -> str:
    return device.name[:31]


class FakeOutput:
    def __init__(self, device, rate, on_failure) -> None:
        self.device = device
        self.rate = rate
        self.on_failure = on_failure
        self.alive = True
        self.closed = False

    def healthy(self) -> bool:
        return self.alive and not self.closed

    def close(self) -> None:
        self.closed = True


class FakeBackend:
    def __init__(self, devices, default) -> None:
        self.devices = list(devices)
        self.default = default
        self.restarts = 0
        self.fail_open = False
        self.opened: list[FakeOutput] = []

    def available(self):
        return list(self.devices)

    def default_device(self):
        return self.default

    def windows_snapshot(self):
        default = windows_name(self.default) if self.default is not None else None
        return default, tuple(windows_name(device) for device in self.devices)

    def restart(self) -> None:
        self.restarts += 1

    def open(self, device, rate, callback, on_failure):
        if self.fail_open or device not in self.devices:
            return None
        output = FakeOutput(device, rate, on_failure)
        self.opened.append(output)
        return output

    def disconnect(self, device, new_default) -> None:
        self.devices.remove(device)
        self.default = new_default

    def connect(self, device, new_default=None) -> None:
        self.devices.append(device)
        if new_default is not None:
            self.default = new_default


class FakeClient:
    def __init__(self, rate=None) -> None:
        self.fixed_rate = rate
        self.prepared: list = []

    def prepare_output(self, device):
        self.prepared.append(device)
        return self.fixed_rate or device.rate

    def audio_callback(self, outdata, frames, time_info, status) -> None:
        pass


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class CoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend([HEADSET, SPEAKERS], HEADSET)
        self.clock = Clock()
        self.coordinator = OutputCoordinator(self.backend, self.clock)
        self.messages: list[str] = []
        self.coordinator.set_listener(self.messages.append)
        self.player = FakeClient(rate=48000)
        self.sounds = FakeClient()
        self.assertTrue(self.coordinator.register(self.sounds))
        self.assertTrue(self.coordinator.register(self.player))

    def output(self, client):
        return self.coordinator._outputs[client]

    def disconnect_headset(self) -> None:
        self.backend.disconnect(HEADSET, SPEAKERS)
        self.output(self.player).alive = False
        self.output(self.player).on_failure()

    def wait(self, seconds: float) -> None:
        self.clock.now += seconds
        self.coordinator.check()

    def test_starts_on_default_device_as_preferred(self):
        self.assertEqual(self.coordinator.current, HEADSET)
        self.assertEqual(self.coordinator.preferred, HEADSET.name)
        self.assertEqual(self.output(self.player).device, HEADSET)
        self.assertEqual(self.messages, [])

    def test_failure_signal_switches_both_outputs_and_keeps_preferred(self):
        old_player, old_sounds = self.output(self.player), self.output(self.sounds)
        self.disconnect_headset()
        self.coordinator.check()
        self.assertTrue(old_player.closed and old_sounds.closed)
        self.assertEqual(self.backend.restarts, 1)
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.assertEqual(self.output(self.player).device, SPEAKERS)
        self.assertEqual(self.output(self.sounds).device, SPEAKERS)
        self.assertEqual(self.coordinator.preferred, HEADSET.name)
        self.assertEqual(self.messages, [output_message(SPEAKERS)])

    def test_unhealthy_output_is_detected_without_signal(self):
        self.backend.disconnect(HEADSET, SPEAKERS)
        self.output(self.sounds).alive = False
        self.coordinator.check()
        self.assertEqual(self.coordinator.current, SPEAKERS)

    def test_healthy_outputs_do_not_switch(self):
        self.wait(10)
        self.assertEqual(self.backend.restarts, 0)
        self.assertEqual(self.messages, [])

    def test_returns_to_preferred_only_after_it_is_stable(self):
        self.disconnect_headset()
        self.coordinator.check()
        self.clock.now += MIN_SWITCH_SECONDS
        self.backend.connect(HEADSET, new_default=HEADSET)
        self.coordinator.check()
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.wait(STABLE_SECONDS / 2)
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.wait(STABLE_SECONDS)
        self.assertEqual(self.coordinator.current, HEADSET)
        self.assertEqual(self.output(self.player).device, HEADSET)
        self.assertEqual(self.messages[-1], output_message(HEADSET, returned=True))

    def test_reconnection_is_not_taken_as_deliberate_change(self):
        self.disconnect_headset()
        self.coordinator.check()
        self.backend.connect(HEADSET, new_default=HEADSET)
        self.coordinator.check()
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.assertEqual(self.coordinator.preferred, HEADSET.name)

    def test_unstable_reconnection_does_not_switch(self):
        self.disconnect_headset()
        self.coordinator.check()
        restarts = self.backend.restarts
        for _ in range(5):
            self.backend.connect(HEADSET)
            self.wait(STABLE_SECONDS / 2)
            self.backend.devices.remove(HEADSET)
            self.wait(STABLE_SECONDS / 2)
        self.assertEqual(self.backend.restarts, restarts)
        self.assertEqual(self.coordinator.current, SPEAKERS)

    def test_return_respects_minimum_interval_between_switches(self):
        self.disconnect_headset()
        self.coordinator.check()
        self.backend.connect(HEADSET)
        self.wait(0.5)
        self.wait(STABLE_SECONDS)
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.wait(MIN_SWITCH_SECONDS)
        self.assertEqual(self.coordinator.current, HEADSET)

    def test_deliberate_default_change_updates_preferred(self):
        self.backend.default = SPEAKERS
        self.coordinator.check()
        self.assertEqual(self.coordinator.preferred, SPEAKERS.name)
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.assertEqual(self.messages, [output_message(SPEAKERS)])
        self.wait(30)
        self.assertEqual(self.coordinator.current, SPEAKERS)

    def test_no_output_keeps_retrying_with_growing_delay(self):
        self.backend.disconnect(HEADSET, None)
        self.backend.devices.clear()
        self.output(self.player).on_failure()
        self.coordinator.check()
        self.assertIsNone(self.coordinator.current)
        self.assertEqual(self.messages, [output_message(None)])
        restarts = self.backend.restarts
        self.wait(1)
        self.assertEqual(self.backend.restarts, restarts)
        self.wait(1)
        self.assertEqual(self.backend.restarts, restarts + 1)
        self.wait(2)
        self.assertEqual(self.backend.restarts, restarts + 1)
        self.wait(2)
        self.assertEqual(self.backend.restarts, restarts + 2)
        self.backend.connect(SPEAKERS, new_default=SPEAKERS)
        self.wait(8)
        self.assertEqual(self.coordinator.current, SPEAKERS)
        self.assertEqual(self.messages[-1], output_message(SPEAKERS))

    def test_ensure_reports_ready_waiting_or_failed(self):
        self.assertIs(self.coordinator.ensure(self.player), OutputStatus.READY)
        self.backend.devices.clear()
        self.backend.default = None
        self.output(self.player).alive = False
        self.assertIs(self.coordinator.ensure(self.player), OutputStatus.WAITING)
        self.backend.connect(SPEAKERS, new_default=SPEAKERS)
        self.backend.fail_open = True
        self.assertIs(self.coordinator.ensure(self.player), OutputStatus.FAILED)
        self.backend.fail_open = False
        self.assertIs(self.coordinator.ensure(self.player), OutputStatus.READY)

    def test_client_rate_is_respected(self):
        self.disconnect_headset()
        self.backend.devices.append(OTHER_RATE)
        self.backend.devices.remove(SPEAKERS)
        self.backend.default = OTHER_RATE
        self.coordinator.check()
        self.assertEqual(self.output(self.player).rate, 48000)
        self.assertEqual(self.output(self.sounds).rate, 44100)

    def test_unregister_closes_only_that_output(self):
        player_output, sounds_output = self.output(self.player), self.output(self.sounds)
        self.coordinator.unregister(self.player)
        self.assertTrue(player_output.closed)
        self.assertFalse(sounds_output.closed)
        self.assertFalse(self.coordinator.has_output(self.player))

    def test_failure_signal_only_sets_a_flag(self):
        self.output(self.player).on_failure()
        self.assertEqual(self.backend.restarts, 0)
        self.coordinator.check()
        self.assertEqual(self.backend.restarts, 1)


class PortAudioOutputTests(unittest.TestCase):
    def test_finished_after_close_is_not_a_failure(self):
        failures = []
        output = PortAudioOutput(lambda *args: None, lambda: failures.append(1), wasapi=True)
        output.close()
        output.finished()
        output.state_changed(None, 1, 0, None)
        self.assertEqual(failures, [])

    def test_state_error_is_a_failure(self):
        failures = []
        output = PortAudioOutput(lambda *args: None, lambda: failures.append(1), wasapi=True)
        output.state_changed(None, 4, 0, None)
        self.assertEqual(failures, [])
        output.state_changed(None, 1 | 8, 0x88890004, None)
        self.assertEqual(failures, [1])

    def test_stalled_callback_is_unhealthy_when_watching_beats(self):
        class Stream:
            active = True

        output = PortAudioOutput(lambda *args: None, lambda: None, wasapi=False)
        output.stream = Stream()
        self.assertTrue(output.healthy())
        self.assertTrue(output.healthy())
        self.assertFalse(output.healthy())
        output.callback(None, 0, None, None)
        self.assertTrue(output.healthy())

    def test_inactive_or_unreadable_stream_is_unhealthy(self):
        class Inactive:
            active = False

        class Broken:
            @property
            def active(self):
                raise RuntimeError("falha")

        output = PortAudioOutput(lambda *args: None, lambda: None, wasapi=True)
        output.stream = Inactive()
        self.assertFalse(output.healthy())
        output.stream = Broken()
        with self.assertLogs("src.models.audio_output", level="WARNING"):
            self.assertFalse(output.healthy())


class NameTests(unittest.TestCase):
    def test_windows_names_are_truncated_prefixes(self):
        self.assertTrue(matches_windows_name(HEADSET.name, "Fone de ouvido do headset (JBL "))
        self.assertFalse(matches_windows_name(SPEAKERS.name, "Fone de ouvido do headset (JBL "))
        self.assertFalse(matches_windows_name(HEADSET.name, None))

    def test_messages(self):
        self.assertEqual(output_message(SPEAKERS), f"Saída de som: {SPEAKERS.name}.")
        self.assertEqual(output_message(HEADSET, returned=True), f"Saída de som de volta: {HEADSET.name}.")
        self.assertEqual(output_message(None), "Nenhuma saída de som disponível.")


if __name__ == "__main__":
    unittest.main()
