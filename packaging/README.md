# Packaging

| Channel | How | Users install with |
| --- | --- | --- |
| PyPI | Automatic: `.github/workflows/release.yml` on a `v*` tag | `pipx install kunji` |
| GitHub Releases | Automatic: binaries + `SHA256SUMS.txt` | download |
| winget | `wingetcreate` with the release `.exe` (see `winget/`) | `winget install testwithsuraj.kunji` |
| Scoop | Copy `scoop/kunji.json` into a `scoop-bucket` repo | `scoop bucket add kunji https://github.com/testwithsuraj/scoop-bucket` then `scoop install kunji` |
| Homebrew | Copy `homebrew/kunji.rb` into a `homebrew-tap` repo | `brew install testwithsuraj/tap/kunji` |

Build a binary locally:

```bash
python -m pip install -e ".[dev]"
pyinstaller packaging/kunji.spec --noconfirm --clean
./dist/kunji --version
```
