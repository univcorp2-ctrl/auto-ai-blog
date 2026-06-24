from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from generator.models import CliResult

CLI_COMMANDS = {
    "claude": ["claude.cmd" if os.name == "nt" else "claude", "-p"],
    "gemini": ["gemini.cmd" if os.name == "nt" else "gemini", "-p"],
    "codex": ["codex.cmd" if os.name == "nt" else "codex", "exec"],
}


def run_ai_cli(cli_name: str, prompt: str, timeout: int) -> CliResult:
    if cli_name not in CLI_COMMANDS:
        return CliResult(False, cli_name, "", f"Unsupported CLI: {cli_name}")

    use_stdin = cli_name == "codex"
    output_path: Path | None = None
    if use_stdin:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as output_file:
            output_path = Path(output_file.name)
        command = [*CLI_COMMANDS[cli_name], "--output-last-message", str(output_path), "-"]
    else:
        command = [*CLI_COMMANDS[cli_name], prompt]

    try:
        completed = subprocess.run(
            command,
            input=prompt if use_stdin else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return CliResult(False, cli_name, "", f"CLI not found: {exc}")
    except subprocess.TimeoutExpired as exc:
        return CliResult(False, cli_name, exc.stdout or "", f"CLI timeout after {timeout}s: {exc}")
    except OSError as exc:
        return CliResult(False, cli_name, "", f"CLI execution error: {exc}")

    output = (completed.stdout or "").strip()
    if output_path is not None:
        if output_path.exists():
            output = output_path.read_text(encoding="utf-8", errors="replace").strip()
            output_path.unlink(missing_ok=True)
        else:
            logging.warning("codex output file was not created: %s", output_path)

    error = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return CliResult(False, cli_name, output, error or f"returncode={completed.returncode}")
    if not output:
        return CliResult(False, cli_name, "", "CLI returned empty output")
    return CliResult(True, cli_name, output)


def call_with_fallback(cli_names: list[str], prompt: str, timeout: int, stage: str) -> CliResult:
    errors: list[str] = []
    for cli_name in cli_names:
        logging.info("%s: calling %s CLI", stage, cli_name)
        result = run_ai_cli(cli_name, prompt, timeout)
        if result.ok:
            logging.info("%s: %s CLI succeeded", stage, cli_name)
            return result
        errors.append(f"{cli_name}: {result.error}")
        logging.warning("%s: %s CLI failed: %s", stage, cli_name, result.error)
    return CliResult(False, ",".join(cli_names), "", " | ".join(errors))

