"""Small, explicit preference schema; microphone consent is never a stored preference."""
import math

CHOICES = {
    "language": {"pt-BR", "en-US"},
    "persona": {"classic", "casual", "gamer", "focus", "creative"},
    "reply_length": {"short", "balanced", "detailed"},
    "voice_style": {"neutral", "expressive"},
}
NAMES = set(CHOICES) | {"display_name", "humor", "voice_rate", "proactive_comments"}


def validate_name(name):
    if not isinstance(name, str) or name not in NAMES:
        raise ValueError("unsupported preference name")


def validate_preferences(values):
    if not isinstance(values, dict):
        raise ValueError("preferences must be an object")
    for name, value in values.items():
        validate_name(name)
        if name in CHOICES:
            if not isinstance(value, str) or value not in CHOICES[name]:
                raise ValueError(f"invalid {name} preference")
        elif name == "display_name":
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 80:
                raise ValueError("display_name must contain 1 to 80 characters")
        elif name == "humor":
            if type(value) is not int or not 0 <= value <= 3:
                raise ValueError("humor must be an integer between 0 and 3")
        elif name == "voice_rate":
            if type(value) not in (int, float) or not math.isfinite(value) or not 0.5 <= value <= 2.0:
                raise ValueError("voice_rate must be between 0.5 and 2.0")
        elif name == "proactive_comments":
            if type(value) is not bool:
                raise ValueError("proactive_comments must be a boolean")
        else:
            raise ValueError(f"unsupported preference: {name}")
