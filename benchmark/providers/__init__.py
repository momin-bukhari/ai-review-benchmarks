"""Provider package for AI review benchmark."""

from benchmark.providers.base import Provider
from benchmark.providers.command_code import CommandCodeProvider

PROVIDERS: dict[str, type[Provider]] = {
    "command-code": CommandCodeProvider,
}


def get_provider(name: str, **kwargs) -> Provider:
    if name not in PROVIDERS:
        raise KeyError(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS)}")
    return PROVIDERS[name](**kwargs)
