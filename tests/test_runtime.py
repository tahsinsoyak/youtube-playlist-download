from unittest.mock import patch

from playlist_audio.runtime import find_javascript_runtime, js_runtime_options


@patch("playlist_audio.runtime.shutil.which")
def test_returns_no_runtime_when_executables_are_missing(mocked_which) -> None:
    mocked_which.return_value = None

    assert find_javascript_runtime() is None
    assert js_runtime_options() == {}


@patch("playlist_audio.runtime.subprocess.run")
@patch("playlist_audio.runtime.shutil.which")
def test_selects_supported_node(mocked_which, mocked_run) -> None:
    mocked_which.side_effect = lambda name: "node.exe" if name == "node" else None
    mocked_run.return_value.returncode = 0
    mocked_run.return_value.stdout = "v24.13.1\n"
    mocked_run.return_value.stderr = ""

    runtime = find_javascript_runtime()

    assert runtime is not None
    assert runtime.name == "node"
    assert js_runtime_options() == {"node": {}}


@patch("playlist_audio.runtime.subprocess.run")
@patch("playlist_audio.runtime.shutil.which")
def test_accepts_version_with_fewer_components_than_minimum(mocked_which, mocked_run) -> None:
    mocked_which.side_effect = lambda name: "deno.exe" if name == "deno" else None
    mocked_run.return_value.returncode = 0
    mocked_run.return_value.stdout = "deno 2.3\n"
    mocked_run.return_value.stderr = ""

    runtime = find_javascript_runtime()

    assert runtime is not None
    assert runtime.name == "deno"
