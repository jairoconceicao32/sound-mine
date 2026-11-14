import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import wx

from src.models import audio_player
from src.models.audio_output import OutputCoordinator, output_message
from src.models.audio_player import AudioLoadError, AudioPlayer, PlaybackError
from src.models.errors import PLAY, SoundMineError
from src.models.screen_manager import ScreenManager
from src.view.interface_sounds import InterfaceSounds
from src.view.player_screen import WAITING_TEXT, PlayerScreen
from tests.test_audio_output import HEADSET, OTHER_RATE, SPEAKERS, Clock, FakeBackend, FakeClient
from tests.test_exit_flow import FakeAnnouncer, FakeSettings, FakeSounds, FakeSpeaker, ScreenFlowCase, flush

RATE = 48000

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def fake_load(path, memory_mb, rate):
    return np.zeros((rate * 10, 2), dtype=np.float32), rate


class PlayerCase(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend([HEADSET, SPEAKERS], HEADSET)
        self.clock = Clock()
        self.outputs = OutputCoordinator(self.backend, self.clock)
        self.messages: list[str] = []
        self.outputs.set_listener(self.messages.append)
        self.sounds = FakeClient()
        self.outputs.register(self.sounds)
        patcher = mock.patch.object(audio_player, "load_audio", side_effect=fake_load)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.player = AudioPlayer(Path("musica.wav"), 0, self.outputs)

    def player_output(self):
        return self.outputs._outputs[self.player]

    def disconnect_headset(self) -> None:
        self.backend.disconnect(HEADSET, SPEAKERS)
        self.player_output().on_failure()
        self.outputs.check()


class PlayerOutputTests(PlayerCase):
    def test_player_opens_output_at_its_rate(self):
        self.assertTrue(self.player.has_output)
        self.assertEqual(self.player_output().device, HEADSET)
        self.assertEqual(self.player_output().rate, RATE)

    def test_no_output_when_opening_raises_load_error(self):
        self.backend.fail_open = True
        with self.assertRaises(AudioLoadError):
            AudioPlayer(Path("outro.wav"), 0, self.outputs)
        self.assertEqual(len(self.outputs._clients), 2)

    def test_playback_error_is_a_sound_mine_error(self):
        self.assertTrue(issubclass(PlaybackError, SoundMineError))

    def test_playing_keeps_playing_from_same_position_after_switch(self):
        self.player.seek(3)
        self.player.play()
        frame = self.player._frame
        self.disconnect_headset()
        self.assertTrue(self.player.playing)
        self.assertFalse(self.player.waiting)
        self.assertEqual(self.player._frame, frame)
        self.assertEqual(self.player_output().device, SPEAKERS)
        self.assertEqual(self.messages, [output_message(SPEAKERS)])

    def test_paused_stays_paused_after_switch(self):
        self.player.seek(3)
        self.disconnect_headset()
        self.assertFalse(self.player.playing)
        self.assertAlmostEqual(self.player.position(), 3)

    def test_player_keeps_its_rate_on_device_with_other_rate(self):
        self.backend.devices.append(OTHER_RATE)
        self.backend.disconnect(HEADSET, OTHER_RATE)
        self.backend.devices.remove(SPEAKERS)
        self.player_output().on_failure()
        self.outputs.check()
        self.assertEqual(self.player_output().device, OTHER_RATE)
        self.assertEqual(self.player_output().rate, RATE)
        self.assertEqual(self.outputs._outputs[self.sounds].rate, 44100)

    def test_without_any_output_play_intention_is_kept(self):
        self.player.play()
        self.backend.devices.clear()
        self.backend.default = None
        self.player_output().on_failure()
        self.outputs.check()
        self.assertTrue(self.player.playing)
        self.assertTrue(self.player.waiting)
        self.backend.connect(SPEAKERS, new_default=SPEAKERS)
        self.clock.now += 2
        self.outputs.check()
        self.assertTrue(self.player.playing)
        self.assertFalse(self.player.waiting)

    def test_paused_without_output_stays_paused_when_output_returns(self):
        self.backend.devices.clear()
        self.backend.default = None
        self.player_output().on_failure()
        self.outputs.check()
        self.backend.connect(SPEAKERS, new_default=SPEAKERS)
        self.clock.now += 2
        self.outputs.check()
        self.assertFalse(self.player.playing)

    def test_play_without_any_device_waits_instead_of_failing(self):
        self.player_output().alive = False
        self.backend.devices.clear()
        self.backend.default = None
        self.player.play()
        self.assertTrue(self.player.playing)
        self.assertTrue(self.player.waiting)

    def test_play_when_output_cannot_start_raises_and_pauses(self):
        self.player_output().alive = False
        self.backend.fail_open = True
        with self.assertRaises(PlaybackError):
            self.player.play()
        self.assertFalse(self.player.playing)

    def test_play_recovers_stopped_output_before_playing(self):
        self.player_output().alive = False
        self.player.play()
        self.assertTrue(self.player.playing)
        self.assertTrue(self.player.has_output)
        self.assertEqual(self.backend.restarts, 1)

    def test_play_with_healthy_output_does_not_restart(self):
        self.player.play()
        self.assertTrue(self.player.playing)
        self.assertEqual(self.backend.restarts, 0)

    def test_edit_after_switch_still_works(self):
        self.disconnect_headset()
        self.player.edit(lambda data, cursor, marked: (data[RATE:], 0))
        self.assertTrue(self.player.has_changes)
        self.player.undo()
        self.assertFalse(self.player.has_changes)

    def test_close_releases_only_player_output(self):
        output = self.player_output()
        self.player.close()
        self.assertTrue(output.closed)
        self.assertFalse(self.outputs._outputs[self.sounds].closed)


class InterfaceSoundsOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend([HEADSET, OTHER_RATE], HEADSET)
        self.outputs = OutputCoordinator(self.backend, Clock())

    def test_sounds_are_loaded_at_device_rate_and_reloaded_when_it_changes(self):
        sounds = InterfaceSounds(outputs=self.outputs)
        self.assertTrue(sounds.has_output)
        self.assertEqual(sounds._rate, HEADSET.rate)
        duration = sounds.duration_ms("navigation")
        self.assertGreater(duration, 0)
        self.backend.disconnect(HEADSET, OTHER_RATE)
        self.outputs._outputs[sounds].on_failure()
        self.outputs.check()
        self.assertEqual(sounds._rate, OTHER_RATE.rate)
        self.assertEqual(self.outputs._outputs[sounds].rate, OTHER_RATE.rate)
        self.assertAlmostEqual(sounds.duration_ms("navigation"), duration, delta=2)

    def test_play_and_wait_does_not_block_without_output(self):
        self.backend.fail_open = True
        sounds = InterfaceSounds(outputs=self.outputs)
        self.assertFalse(sounds.has_output)
        with mock.patch("src.view.interface_sounds.time.sleep") as sleep:
            sounds.play_and_wait("close")
        sleep.assert_not_called()

    def test_close_unregisters(self):
        sounds = InterfaceSounds(outputs=self.outputs)
        sounds.close()
        self.assertNotIn(sounds, self.outputs._clients)


class ManagerOutputTests(ScreenFlowCase):
    def setUp(self) -> None:
        self.backend = FakeBackend([HEADSET, SPEAKERS], HEADSET)
        self.outputs = OutputCoordinator(self.backend, Clock())
        self.log = []
        self.frame = wx.Frame(None)
        self.manager = ScreenManager(self.frame, FakeAnnouncer(self.log), FakeSpeaker(self.log),
                                     FakeSounds(self.log), "Sound Mine", FakeSettings(), self.outputs)
        self.sounds = FakeClient()
        self.outputs.register(self.sounds)

    def test_initial_status_names_current_output(self):
        self.assertEqual(self.manager.output_status, output_message(HEADSET))

    def test_switch_updates_status_and_announces_without_interrupting(self):
        self.backend.disconnect(HEADSET, SPEAKERS)
        self.outputs._outputs[self.sounds].on_failure()
        self.manager._on_output_timer(None)
        self.assertEqual(self.manager.output_status, output_message(SPEAKERS))
        self.manager._announce_output(self.manager.output_status)
        self.assertIn(f"fala: {output_message(SPEAKERS)}", self.log)

    def test_close_stops_timer_and_releases_outputs(self):
        output = self.outputs._outputs[self.sounds]
        self.frame.Close()
        flush()
        self.assertTrue(output.closed)
        self.assertEqual(self.outputs._clients, [])


class FakeScreenPlayer:
    file_name = "musica.wav"
    duration = 10.0
    volume = 100

    def __init__(self) -> None:
        self.playing = False
        self.waiting = False
        self.error = None

    def position(self) -> float:
        return 0.0

    def play(self) -> None:
        if self.error is not None:
            raise self.error
        self.playing = True

    def pause(self) -> None:
        self.playing = False
        self.waiting = False


class PlayerScreenTests(ScreenFlowCase):
    def open_player(self, player: FakeScreenPlayer) -> PlayerScreen:
        screen = PlayerScreen(self.manager.parent, self.manager, player)
        self.manager.push(screen)
        flush()
        return screen

    def test_playback_error_shows_dialog_and_never_says_playing(self):
        player = FakeScreenPlayer()
        player.error = PlaybackError(audio_player.PLAYBACK_MESSAGE)
        self.open_player(player)
        self.assertIn(f"erro [{PLAY}]: {audio_player.PLAYBACK_MESSAGE}", self.log)
        self.log.clear()
        self.press(wx.WXK_SPACE)
        self.assertIn(f"erro [{PLAY}]: {audio_player.PLAYBACK_MESSAGE}", self.log)
        self.assertNotIn("fala: Reproduzindo", self.log)
        self.assertFalse(player.playing)

    def test_space_while_waiting_announces_waiting(self):
        player = FakeScreenPlayer()
        self.open_player(player)
        self.press(wx.WXK_SPACE)
        self.assertIn("fala: Pausado", self.log)
        player.waiting = True
        self.press(wx.WXK_SPACE)
        self.assertIn(f"fala: Reproduzindo. {WAITING_TEXT}", self.log)

    def test_status_shows_waiting_state(self):
        player = FakeScreenPlayer()
        screen = self.open_player(player)
        player.waiting = True
        screen.output_changed()
        self.assertIn(WAITING_TEXT, screen._status.GetLabel())


if __name__ == "__main__":
    unittest.main()
