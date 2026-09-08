"""The language registry, the runner Dockerfiles and docker-compose must agree.

The sandbox launches `docker run <image>` by name. If a language is added to the
registry without a matching image, every submission in that language fails at
runtime with an opaque Docker error, so this drift is worth failing the build on.
Deliberately dependency-free: it reads the compose file as text rather than
requiring a YAML parser the backend does not otherwise need.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core import languages

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
RUNNERS_DIR = REPO_ROOT / "docker" / "runners"


@pytest.fixture(scope="module")
def compose_text() -> str:
    assert COMPOSE_FILE.is_file(), f"missing {COMPOSE_FILE}"
    return COMPOSE_FILE.read_text(encoding="utf-8")


@pytest.mark.parametrize("language", languages.LANGUAGES.values(), ids=lambda lang: lang.id)
def test_every_language_has_a_runner_dockerfile(language):
    dockerfile = RUNNERS_DIR / f"{language.id}.Dockerfile"
    assert dockerfile.is_file(), f"no runner image definition for {language.id}"


@pytest.mark.parametrize("language", languages.LANGUAGES.values(), ids=lambda lang: lang.id)
def test_every_runner_image_is_built_by_compose(language, compose_text):
    assert language.image in compose_text, (
        f"docker-compose.yml never builds {language.image}; "
        f"{language.id} submissions would fail at runtime"
    )
    assert f"docker/runners/{language.id}.Dockerfile" in compose_text


@pytest.mark.parametrize("language", languages.LANGUAGES.values(), ids=lambda lang: lang.id)
def test_runner_images_drop_privileges(language):
    """Untrusted code must never execute as root inside the runner."""
    dockerfile = (RUNNERS_DIR / f"{language.id}.Dockerfile").read_text(encoding="utf-8")
    assert "USER runner" in dockerfile
    assert "-u 10001" in dockerfile, "runner UID must match the sandbox's --user flag"


def test_c_runner_provides_a_c_compiler():
    dockerfile = (RUNNERS_DIR / "c.Dockerfile").read_text(encoding="utf-8")
    assert "gcc" in dockerfile


def test_cpp_runner_provides_a_cpp_compiler():
    dockerfile = (RUNNERS_DIR / "cpp.Dockerfile").read_text(encoding="utf-8")
    assert "g++" in dockerfile
