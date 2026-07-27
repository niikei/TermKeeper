# TermKeeper offline installer

This bundle contains TermKeeper and its runtime dependencies for Windows x64 and Python 3.12.
It does not contain Python or uv.

Prerequisites:

1. Install Python 3.12.
2. Install uv.
3. Open PowerShell in this directory.
4. Run `.\install.ps1`.
5. Reopen PowerShell and run `tk --version` and `tk doctor`.

The installer disables network and package-index access. Keep the `wheelhouse` directory beside
`install.ps1` until installation finishes.
