"""Tests for Terraform configuration validity."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

LAB_DIR = Path(__file__).parent


def _has_terraform() -> bool:
    return shutil.which("terraform") is not None


@pytest.fixture
def _skip_if_no_terraform() -> None:
    if not _has_terraform():
        pytest.skip("Terraform not installed")


@pytest.fixture
def _terraform_init(_skip_if_no_terraform: None) -> None:  # noqa: PT019
    subprocess.run(
        ["terraform", "init", "-backend=false"],
        cwd=LAB_DIR,
        capture_output=True,
        check=True,
    )


@pytest.mark.usefixtures("_terraform_init")
def test_terraform_validate() -> None:
    result = subprocess.run(
        ["terraform", "validate"],
        cwd=LAB_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Validation failed: {result.stderr}"


@pytest.mark.usefixtures("_terraform_init")
def test_terraform_fmt() -> None:
    result = subprocess.run(
        ["terraform", "fmt", "-check", "-diff"],
        cwd=LAB_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Formatting issues:\n{result.stdout}"


def test_tf_files_exist() -> None:
    """Verify all expected .tf files are present."""
    assert (LAB_DIR / "main.tf").exists()
    assert (LAB_DIR / "variables.tf").exists()
    assert (LAB_DIR / "outputs.tf").exists()
