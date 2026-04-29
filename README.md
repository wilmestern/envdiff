# envdiff

> Utility to compare environment variable sets across staging and production configs with redaction support.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourname/envdiff.git && cd envdiff && pip install .
```

---

## Usage

Compare two `.env` files and highlight differences:

```bash
envdiff staging.env production.env
```

Redact sensitive values (e.g. keys containing `SECRET`, `PASSWORD`, `TOKEN`):

```bash
envdiff staging.env production.env --redact
```

Use it as a Python library:

```python
from envdiff import compare

diff = compare("staging.env", "production.env", redact=True)
for key, (staging_val, prod_val) in diff.items():
    print(f"{key}: {staging_val} → {prod_val}")
```

### Example Output

```
KEY              STAGING         PRODUCTION
─────────────────────────────────────────────
API_URL          https://stg     https://prod
DB_PASSWORD      [REDACTED]      [REDACTED]
CACHE_TTL        300             600
NEW_RELIC_KEY    ✗ missing       [REDACTED]
```

---

## Options

| Flag | Description |
|------|-------------|
| `--redact` | Mask sensitive values in output |
| `--only-diff` | Show only keys that differ |
| `--format json` | Output results as JSON |

---

## License

[MIT](LICENSE) © 2024 Your Name