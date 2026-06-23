from __future__ import annotations

import logging
import subprocess

from generator.models import CliResult

CLI_COMMANDS = {
    "claude": ["claude", "-p"],
    "gemini": ["gemini", "-p"],
    "codex": ["codex", "-q"],
}


def run_ai_cli(cli_name: str, prompt: str, timeout: int) -> CliResult:
    if cli_name not in CLI_COMMANDS:
        return CliResult(False, cli_name, "", f"Unsupported CLI: {cli_name}")

    command = [*CLI_COMMANDS[cli_name], prompt]
    try:
        completed = subprocess.run(
            command,
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
