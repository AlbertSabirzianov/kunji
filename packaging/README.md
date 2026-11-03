# Packaging

| Channel | How | Users install with |
| --- | --- | --- |
| PyPI | Automatic: `.github/workflows/release.yml` on a `v*` tag | `pip install kunji` |
| GitHub Releases | Automatic: Windows + Linux binaries + `SHA256SUMS.txt` (macOS: set repo variable `BUILD_MACOS=true`) | download |
| winget | `wingetcreate` with the release `.exe` (see `winget/`) | `winget install testwithsuraj.kunji` |
| Scoop | Copy `scoop/kunji.json` into a `scoop-bucket` repo | `scoop bucket add kunji https://github.com/testwithsuraj/scoop-bucket` then `scoop install kunji` |
| Homebrew | Copy `homebrew/kunji.rb` into a `homebrew-tap` repo | `brew install testwithsuraj/tap/kunji` |

Build a binary locally:

```bash
python -m pip install -e ".[dev]"
pyinstaller packaging/kunji.spec --noconfirm --clean
./dist/kunji --version
```

## Releasing a new version

1. Set the new version in `src/kunji/__init__.py` (e.g. `__version__ = "0.2.0"`).
2. Add `## [0.2.0] - YYYY-MM-DD` to `CHANGELOG.md` — that section becomes the release notes.
3. Commit and push to `main`.
4. GitHub → Actions → **Release** → **Review deployments** → `pypi` → **Approve and deploy**.

The workflow then publishes to PyPI, creates the `v0.2.0` tag and the GitHub Release with
the downloads. Pushing to `main` without changing the version never releases anything.

### Turning on the macOS download later

GitHub → Settings → Secrets and variables → Actions → **Variables** → New repository
variable: `BUILD_MACOS` = `true`. Nothing else to change; if a Mac build ever fails, the
release still goes out without it.
