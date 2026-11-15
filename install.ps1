# kunji installer for Windows (PowerShell).
#
#   irm https://kunji.iamsuraj.me/install.ps1 | iex
#
# From cmd.exe:
#   powershell -ExecutionPolicy ByPass -c "irm https://kunji.iamsuraj.me/install.ps1 | iex"
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
    $ProgressPreference = "SilentlyContinue"  # the progress bar makes downloads very slow in 5.1
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
        # Not `throw`: that prints a scary stack trace, and `exit` would close the user's window.
        Write-Host "kunji installer: $message" -ForegroundColor Red
        $global:LASTEXITCODE = 1
    }

    # Runs a program quietly with a one-line progress display: "[2/3] Installing kunji  / 12s".
    # Its own output goes to log files that are shown only if it fails.
    function Invoke-Step($label, $file, [string[]]$arguments) {
        $out = [System.IO.Path]::GetTempFileName()
        $errLog = [System.IO.Path]::GetTempFileName()
        # Quote each argument for the command line (Start-Process joins them with spaces).
        $argLine = ($arguments | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join " "
        $proc = Start-Process -FilePath $file -ArgumentList $argLine -NoNewWindow -PassThru `
            -RedirectStandardOutput $out -RedirectStandardError $errLog
        $null = $proc.Handle  # makes ExitCode available after exit in Windows PowerShell 5.1
        $spin = "|/-\"
        $secs = 0
        while (-not $proc.HasExited) {
            Write-Host -NoNewline ("`r$label  " + $spin[$secs % 4] + " ${secs}s ")
            Start-Sleep -Seconds 1
            $secs++
        }
        $proc.WaitForExit()
        Write-Host -NoNewline ("`r" + (" " * ($label.Length + 12)) + "`r")
        $ok = $proc.ExitCode -eq 0
        if ($ok) {
            Write-Host "$label  done"
        } else {
            Write-Host "$label  failed:" -ForegroundColor Red
            Get-Content $out, $errLog -ErrorAction SilentlyContinue | Write-Host
        }
        Remove-Item $out, $errLog -ErrorAction SilentlyContinue
        return $ok
    }

    Write-Host "Installing kunji"
    Write-Host ""

    $uv = Find-Uv
    if (-not $uv) {
        # Run uv's installer as a file in its own PowerShell process, not with `iex` here: it has
        # a param() block, refuses some execution policies, and calls `exit 1` on failure, which
        # would close this window.
        $uvInstaller = Join-Path ([System.IO.Path]::GetTempPath()) "uv-installer-$([guid]::NewGuid()).ps1"
        try {
            Invoke-WebRequest https://astral.sh/uv/install.ps1 -OutFile $uvInstaller -UseBasicParsing -ErrorAction Stop
        } catch {
            Fail "couldn't download uv from astral.sh: $($_.Exception.Message)"
            return
        }
        $shell = (Get-Process -Id $PID).Path
        $uvArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $uvInstaller)
        if ($noModifyPath) { $uvArgs += "-NoModifyPath" }
        $ok = Invoke-Step "[1/3] Getting uv (manages Python for kunji)" $shell $uvArgs
        Remove-Item $uvInstaller -ErrorAction SilentlyContinue
        if (-not $ok) { Fail "uv's installer failed (the reason is above)."; return }
        $uv = Find-Uv
        if (-not $uv) { Fail "uv was installed but can't be found. Open a new terminal and run this again."; return }
    } else {
        Write-Host "[1/3] Getting uv (manages Python for kunji)  already installed"
    }

    $package = "kunji"
    if ($env:KUNJI_VERSION) { $package = "kunji==$($env:KUNJI_VERSION)" }

    # --upgrade: running the installer again updates kunji. --python: uv downloads one if needed.
    $ok = Invoke-Step "[2/3] Installing kunji (the first time takes a minute)" $uv @("tool", "install", "--upgrade", "--python", ">=3.11", $package)
    if (-not $ok) {
        Fail "uv couldn't install kunji (the reason is above). If kunji is open, close it first. Then run this again."
        return
    }

    $binDir = (& $uv tool dir --bin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $binDir) { $binDir = Join-Path $HOME ".local\bin" }
    $binDir = "$binDir".Trim()

    if (-not $noModifyPath) {
        & $uv tool update-shell *> $null
        # Make `kunji` work in this window too, not only in new ones.
        $inPath = ($env:Path -split ";") | Where-Object { $_.TrimEnd("\") -ieq $binDir.TrimEnd("\") }
        if (-not $inPath) { $env:Path = "$binDir;$env:Path" }
        Write-Host "[3/3] Adding kunji to your PATH  done"
    } else {
        Write-Host "[3/3] Adding kunji to your PATH  skipped (KUNJI_NO_MODIFY_PATH=1)"
    }

    $exe = Join-Path $binDir "kunji.exe"
    $version = (& $exe --version 2>$null)
    if ($LASTEXITCODE -ne 0) { Fail "kunji was installed but doesn't start. Try: & `"$exe`" --version"; return }

    Write-Host ""
    Write-Host "$version is installed." -ForegroundColor Green
    if ($noModifyPath) {
        Write-Host "Run: & `"$exe`""
    } else {
        Write-Host "Run: kunji"
        Write-Host "(In Command Prompt or other open terminals, open a new window first.)"
    }
    Write-Host "Update later with: kunji upgrade"
}
