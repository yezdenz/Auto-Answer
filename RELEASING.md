# Releasing Endependenz

The supported public artifact is a portable, zipped Windows x64 folder built by GitHub Actions. Users do not need Python.

## Before tagging

1. Rotate any API key that has ever been pasted into chat, logs, screenshots, or issue text. Never use a maintainer key in a release artifact.
2. Confirm `git status --short` is clean and `config.json`, `.env`, debug screenshots, and PDFs are not tracked.
3. Run:

   ```powershell
   py -3 scripts/check_secrets.py --history
   py -3 -m pip_audit -r requirements.txt
   py -3 -m unittest discover -s tests -v
   py -3 scripts/verify_release_version.py v2.0.0
   ```

4. Review `CHANGELOG.md`, `SECURITY.md`, and the version in `pyproject.toml` and `src/auto_answer/__init__.py`.
5. Install `requirements-build.txt`, build locally with `py -3 -m PyInstaller --clean --noconfirm packaging/Endependenz.spec`, and launch `dist/Endependenz/Endependenz.exe` on a clean Windows account if possible.

## Publish

Create and push an annotated tag only after CI is green:

```powershell
git tag -a v2.0.0 -m "Endependenz 2.0.0"
git push origin v2.0.0
```

The release workflow re-runs tests, history-aware secret scanning, and `pip-audit`; builds the portable application; publishes a SHA-256 checksum, CycloneDX SBOM, and provenance attestation; then creates the GitHub Release.

## Signing limitation

The workflow does not Authenticode-sign `Endependenz.exe` because no code-signing certificate is configured. GitHub provenance and SHA-256 checksums protect artifact integrity, but they do not prevent Windows SmartScreen warnings. Add certificate-based signing before the packaging step when a trusted signing certificate is available.
