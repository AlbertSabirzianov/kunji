# PyInstaller spec — build with:  pyinstaller packaging/kunji.spec --noconfirm --clean
# Output: dist/kunji (or dist/kunji.exe on Windows), a single self-contained file.
# ruff: noqa
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

hidden = (
    collect_submodules("keyring.backends")
    + collect_submodules("rich")
    + collect_submodules("pygments.lexers")
    + collect_submodules("pygments.styles")
    + collect_submodules("pygments.formatters")
    + collect_submodules("questionary")
    + collect_submodules("prompt_toolkit")
)
datas = copy_metadata("keyring") + copy_metadata("kunji")

a = Analysis(
    ["entry.py"],
    pathex=["../src"],
    hiddenimports=hidden,
    datas=datas,
    excludes=["tkinter", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="kunji",
    console=True,
    strip=False,
    upx=False,
)
