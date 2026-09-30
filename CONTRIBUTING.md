# Contributing to Auto Answer

Thank you for your interest in improving Auto Answer!

## Development Setup

1. Fork and clone the repository.
2. Ensure you have Python 3.10+ installed.
3. Install development dependencies:
   ```powershell
   py -3 -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and supply a test Gemini API key.

## Code Standards

- Follow PEP 8 style guidelines.
- Use explicit type annotations on public functions and methods.
- Write unit tests under `tests/` for any new functionality.
- Verify tests pass before opening a PR:
  ```powershell
  py -3 -m unittest discover tests
  ```

## Pull Request Guidelines

1. Create a descriptive branch name (e.g. `feat/ocr-fallback` or `fix/dpi-scaling`).
2. Include a summary of changes and test steps in your PR description.

