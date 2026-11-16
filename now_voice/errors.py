class VoiceError(Exception):
    code = "VOICE_ERROR"


class PermissionRequired(VoiceError):
    code = "PERMISSION_REQUIRED"


class CapabilityUnavailable(VoiceError):
    code = "CAPABILITY_UNAVAILABLE"


class VoiceCancelled(VoiceError):
    code = "CANCELLED"


class VoiceBusy(VoiceError):
    code = "BUSY"


class ProviderUnavailable(VoiceError):
    code = "PROVIDER_UNAVAILABLE"


class ProviderFailure(VoiceError):
    code = "PROVIDER_FAILURE"
