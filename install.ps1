# kunji installer for Windows (PowerShell).
#
#   irm https://github.com/testwithsuraj/kunji/releases/latest/download/install.ps1 | iex
#
# From cmd.exe:
#   powershell -ExecutionPolicy ByPass -c "irm https://github.com/testwithsuraj/kunji/releases/latest/download/install.ps1 | iex"
#
# What it does:
#   1. Installs uv (https://docs.astral.sh/uv/) if you don't have it. uv is a single file.
#   2. Runs `uv tool install kunji`. uv downloads Python 3.11+ by itself if you don't have it,
#      and keeps kunji in its own environment, so it never clashes with your other Python apps.
#   3. Adds the folder with the `kunji` command to your PATH (and to this window).
#
# Options (environment variables):
#   $env:KUNJI_VERSION = "0.1.2"     install that version instead of the newest
#   $env:KUNJI_NO_MODIFY_PATH = "1"  don't change your PATH
#
# Uninstall: uv tool uninstall kunji

& {
    # Not "Stop": uv prints progress on stderr, which Windows PowerShell 5.1 would treat as an
    # error. Every step checks its own result instead.
    $ErrorActionPreference = "Continue"
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $noModifyPath = $env:KUNJI_NO_MODIFY_PATH -eq "1"

    function Find-Uv {
        $cmd = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
        $dirs = @($env:XDG_BIN_HOME, (Join-Path $HOME ".local\bin"), (Join-Path $HOME ".cargo\bin"))
        foreach ($dir in $dirs) {
            if ($dir -and (Test-Path (Join-Path $dir "uv.exe"))) { return (Join-Path $dir "uv.exe") }
        }
        return $null
    }

    function Fail($message) {
        Write-Host "kunji installer: $message" -ForegroundColor Red
        throw "kunji install failed"
    }

    Write-Host "Installing kunji..."

    $uv = Find-Uv
    if (-not $uv) {
        Write-Host "Installing uv (kunji uses it to manage Python for you)..."
        if ($noModifyPath) { $env:UV_NO_MODIFY_PATH = "1" }
        try {
            Invoke-RestMethod https://astral.sh/uv/install.ps1 -ErrorAction Stop | Invoke-Expression
        } catch {
            Fail "couldn't install uv. Check your internet connection and run this again."
        }
        $uv = Find-Uv
        if (-not $uv) { Fail "uv was installed but can't be found. Open a new terminal and run this again." }
    }

    $package = "kunji"
    if ($env:KUNJI_VERSION) { $package = "kunji==$($env:KUNJI_VERSION)" }

    # --upgrade: running the installer again updates kunji. --python: uv downloads one if needed.
    & $uv tool install --upgrade --python ">=3.11" $package
    if ($LASTEXITCODE -ne 0) {
        Fail "uv couldn't install kunji. If kunji is open, close it first. Then run this again."
    }

    $binDir = (& $uv tool dir --bin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $binDir) { $binDir = Join-Path $HOME ".local\bin" }
    $binDir = "$binDir".Trim()

    if (-not $noModifyPath) {
        & $uv tool update-shell *> $null
        # Make `kunji` work in this window too, not only in new ones.
        $inPath = ($env:Path -split ";") | Where-Object { $_.TrimEnd("\") -ieq $binDir.TrimEnd("\") }
        if (-not $inPath) { $env:Path = "$binDir;$env:Path" }
    }

    $exe = Join-Path $binDir "kunji.exe"
    $version = (& $exe --version 2>$null)
    if ($LASTEXITCODE -ne 0) { Fail "kunji was installed but doesn't start. Try: & `"$exe`" --version" }

    Write-Host ""
    Write-Host "kunji is installed: $version" -ForegroundColor Green
    if ($noModifyPath) {
        Write-Host "Run: & `"$exe`""
    } else {
        Write-Host "Run: kunji"
        Write-Host "(In Command Prompt or other open terminals, open a new window first.)"
    }
    Write-Host "Update later with: kunji upgrade"
}
