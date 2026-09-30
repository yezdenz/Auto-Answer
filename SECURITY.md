# 🔒 Security Policy (`SECURITY.md`)

Endependenz takes security, privacy, and sensitive credential protection seriously.

---

## 🛡️ Credential Safety

- **API Keys**: Endependenz never commits secrets to source control. Prompted keys are masked and stored in the operating system credential vault. Environment variables (`GEMINI_API_KEY`) and untracked `.env` files remain available for development, but `.env` is plaintext: do not place it in a shared or cloud-synced directory for production use.
- **Config Sanitization**: The configuration manager automatically scrubs all credential fields before writing `config.json` to disk.
- **Git Protection**: `.gitignore` strictly ignores `.env`, `*.log`, debug screen dumps, and temporary tokens.

---

## 📸 Screen Data Handling

- Captured frames remain in memory by default and requested scans are converted to byte streams transmitted over HTTPS/TLS to Google Gemini's official API endpoints.
- Debug screenshots (`debug_output/`) are saved locally only if `"save_debug_screenshots": true` is configured. The default is `false`; retained images are excluded from Git but may still be synchronized by OneDrive or other backup software.
- Opening the program without a command enters interactive mode and does not capture or upload until the user requests a scan.

## PDF Reference Handling

- Selected PDFs are read locally and only extracted text is added to a Gemini question request after Start/Scan is used.
- Limits are eight PDFs, 25 MB and 500 pages per file, and 80,000 extracted characters total.
- PDF text is treated as untrusted factual material and cannot override the solver's security instructions.
- Password-protected and non-PDF files are rejected. Image-only scanned PDFs require OCR and currently report that no readable text was found.

## Automation Controls

- Mouse automation is disabled and dry-run mode is enabled by default.
- Invalid questions, low-confidence answers, out-of-range model indices, and multi-select answers are blocked from clicking unless the relevant control is explicitly enabled.
- Treat model output as untrusted. Keep automation disabled for high-impact software or any workflow where a wrong click could cause loss, submission, purchase, or disclosure.

## Release Checklist

1. Rotate development credentials and confirm `.env` and debug images are absent from the artifact.
2. Run unit tests, a dependency vulnerability audit, and secret scanning.
3. Build from a clean commit; publish checksums/SBOM and sign the installer or executable.
4. Document the Gemini data flow, screenshot retention toggle, supported Windows versions, and update channel.
5. Never auto-update from an unsigned or unverified download.

---

## 📬 Reporting Vulnerabilities

If you discover any security vulnerabilities or privacy concerns, please open a private security advisory on GitHub or email the repository maintainers directly.
