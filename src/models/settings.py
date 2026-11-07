from dataclasses import dataclass


@dataclass
class Settings:
    language: str = "Português"
    format: str = "mp3"
    channel: str = "Estéreo"
    sample_rate: str = "44100"
    echo_delay: int = 300
    echo_percent: int = 75
    reverb_percent: int = 80
    reverb_delay: int = 200
    memory_mb: int = 0
    play_buffers: int = 4
    record_buffers: int = 4
    disable_sounds: bool = False
    disable_tips: bool = False
