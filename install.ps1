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

    # Always on uv's own Python 3.12, never a Python already on this computer: a broken or odd
    # system Python would make kunji fail to start. --reinstall rebuilds an older install that
    # used one; --force replaces a stray kunji.exe in uv's folder. (--python-preference
    # only-managed is the older spelling of --managed-python, so older uv versions accept it.)
    $installArgs = @("tool", "install", "--upgrade", "--reinstall", "--force",
        "--python-preference", "only-managed", "--python", "3.12", $package)
    $ok = Invoke-Step "[2/3] Installing kunji (the first time takes a minute)" $uv $installArgs
    if (-not $ok) {
        Fail "uv couldn't install kunji (the reason is above). If kunji is open, close it first. Then run this again."
        return
    }

    $binDir = (& $uv tool dir --bin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $binDir) { $binDir = Join-Path $HOME ".local\bin" }
    $binDir = "$binDir".Trim()

    function Same-Dir($a, $b) {
        $a = [Environment]::ExpandEnvironmentVariables("$a").Trim().TrimEnd("\")
        $b = [Environment]::ExpandEnvironmentVariables("$b").Trim().TrimEnd("\")
        return $a -ieq $b
    }

    if (-not $noModifyPath) {
        # Put kunji's folder FIRST in the user PATH. An older kunji.exe (from `pip install kunji`,
        # in a Python "Scripts" folder that's also on PATH) would otherwise run instead of this one.
        # Read and write the raw registry value so entries like %USERPROFILE%\... stay as they are.
        $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment", $true)
        $raw = [string]$key.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $rest = @($raw -split ";" | Where-Object { $_ -and -not (Same-Dir $_ $binDir) })
        $key.SetValue("Path", (@($binDir) + $rest) -join ";", [Microsoft.Win32.RegistryValueKind]::ExpandString)
        $key.Close()
        # Tell Windows the environment changed, so new terminals see it (setting any user
        # variable through .NET broadcasts the change; this one is removed straight away).
        $dummy = "kunji-installer-" + [guid]::NewGuid().ToString()
        [Environment]::SetEnvironmentVariable($dummy, "1", "User")
        [Environment]::SetEnvironmentVariable($dummy, $null, "User")
        # Same for this window.
        $env:Path = (@($binDir) + @($env:Path -split ";" | Where-Object { $_ -and -not (Same-Dir $_ $binDir) })) -join ";"
        Write-Host "[3/3] Adding kunji to your PATH  done"
    } else {
        Write-Host "[3/3] Adding kunji to your PATH  skipped (KUNJI_NO_MODIFY_PATH=1)"
    }

    $exe = Join-Path $binDir "kunji.exe"
    $version = (& $exe --version 2>$null)
    if ($LASTEXITCODE -ne 0) { Fail "kunji was installed but doesn't start. Try: & `"$exe`" --version"; return }

    # Other kunji commands on PATH (usually from an earlier `pip install kunji`). Windows reads the
    # system PATH before the user PATH, so one in a system PATH folder still runs instead of ours.
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $shadowing = @()
    $others = @()
    foreach ($entry in @(($machinePath -split ";") | ForEach-Object { @{ Dir = $_; System = $true } }) +
                       @(($userPath + ";" + $env:Path) -split ";" | ForEach-Object { @{ Dir = $_; System = $false } })) {
        $dir = [Environment]::ExpandEnvironmentVariables("$($entry.Dir)").Trim()
        if (-not $dir -or (Same-Dir $dir $binDir)) { continue }
        foreach ($name in @("kunji.exe", "kunji.cmd", "kunji.bat")) {
            $candidate = Join-Path $dir $name
            if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and ($others -notcontains $candidate) -and ($shadowing -notcontains $candidate)) {
                if ($entry.System) { $shadowing += $candidate } else { $others += $candidate }
            }
        }
    }

    Write-Host ""
    Write-Host "$version is installed." -ForegroundColor Green
    if ($shadowing.Count -gt 0) {
        Write-Host ""
        Write-Host "Warning: an older kunji is on the system PATH and will run instead of this one." -ForegroundColor Yellow
        Write-Host "Delete it (it's left over from an earlier pip install):" -ForegroundColor Yellow
        foreach ($f in $shadowing) { Write-Host "  del `"$f`"" }
    }
    if ($others.Count -gt 0) {
        Write-Host ""
        Write-Host "Note: older kunji copies were found (from an earlier pip install). This install now"
        Write-Host "comes first on your PATH, but you can delete them:"
        foreach ($f in $others) { Write-Host "  del `"$f`"" }
    }
    if ($noModifyPath) {
        Write-Host "Run: & `"$exe`""
    } else {
        Write-Host "Run: kunji"
        Write-Host "(In Command Prompt or other open terminals, open a new window first.)"
    }
    Write-Host "Update later with: kunji upgrade"
}
