# 🔒 Security Policy (`SECURITY.md`)

Auto Answer takes security, privacy, and sensitive credential protection seriously.

---

## 🛡️ Credential Safety

- **API Keys**: Auto Answer never commits secrets to source control. API keys are loaded via environment variables (`GEMINI_API_KEY`) or from untracked `.env` files.
- **Config Sanitization**: The configuration manager automatically scrubs all credential fields before writing `config.json` to disk.
- **Git Protection**: `.gitignore` strictly ignores `.env`, `*.log`, debug screen dumps, and temporary tokens.

---

## 📸 Screen Data Handling

- Captured frames are stored exclusively in memory and converted directly to byte streams transmitted over HTTPS/TLS to Google Gemini's official API endpoints.
- Debug screenshots (`debug_output/`) are saved locally only if `"save_debug_screenshots": true` is configured in `config.json`. These images are excluded from Git commits.

---

## 📬 Reporting Vulnerabilities

If you discover any security vulnerabilities or privacy concerns, please open a private security advisory on GitHub or email the repository maintainers directly.
