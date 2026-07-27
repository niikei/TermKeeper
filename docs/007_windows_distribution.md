# GitHubへ接続できないWindows環境への配布

GitHubへ接続できないWindows環境には、ソースディレクトリを`PATH`へ追加せず、
TermKeeperのwheelを検証して`uv tool`の隔離環境へインストールする。

## GitHub Releaseの位置づけ

GitHub Releaseはインストール自体には必須ではないが、バージョン付きのwheel、sdist、
Windows用オフラインbundle、SHA-256を同じtagから再現可能に生成するため、標準の配布経路とする。
Release workflowは`v<version>` tagをpushしたときだけ実行され、tagと
`src/termkeeper/_version.py`の値が一致しなければ失敗する。

GitHubへ接続できる環境でRelease assetsを取得し、接続できない環境へ必要なファイルを配布する。
Releaseを使わず手動でwheelを作る場合も、以下と同じ検証手順を使用する。

[TermKeeper Latest Release](https://github.com/niikei/TermKeeper/releases/latest)では、
Windows用オフラインZIP、wheel、source distribution、`SHA256SUMS.txt`を配布する。
GitHubが自動生成する`Source code (zip)`ではなく、用途に合うRelease assetを選択する。

## 推奨する配布物

信頼できる開発環境で、リリース対象のcommitからwheelを作成する。

```bash
uv lock --check
uv run pytest
uv build
shasum -a 256 dist/termkeeper-*.whl
```

配布するものは原則として次の2点だけとする。

```text
termkeeper-<version>-py3-none-any.whl
SHA-256の値
```

`.git/`、`.venv/`、SQLite DB、CSV export、`.env`、ログなどのローカルデータは
配布物へ含めない。SHA-256は可能ならwheelとは別の信頼できる経路で共有する。
同じ媒体に置いたハッシュだけでは、悪意ある差し替えに対する真正性は証明できない。
利用可能なArtifact Repositoryやコード署名の仕組みがある場合は、それを使用する。

## PyPIへ接続できる環境

受け取ったファイルだけが置かれたディレクトリで、PowerShellを開く。
最初にSHA-256を確認する。

```powershell
$wheel = Get-Item .\termkeeper-*.whl
Get-FileHash $wheel.FullName -Algorithm SHA256
```

確認済みの値と完全に一致した場合だけ、TermKeeperをインストールする。
Python 3.12がなければuvは通常Pythonを取得するため、ネットワーク接続が必要になる。

```powershell
uv tool install --python 3.12 $wheel.FullName
uv tool update-shell
```

PowerShellを開き直して動作確認する。

```powershell
tk --version
tk doctor
Get-Command tk
```

`uv tool install`はTermKeeper専用の隔離環境を作成する。環境内部へ`pip`などで直接変更を
加えず、更新時も`uv tool`を使用する。実行ファイルの保存先は次で確認できる。

```powershell
uv tool dir --bin
```

現在のPowerShellだけで直ちに試す場合は、一時的に`PATH`へ追加できる。

```powershell
$env:Path = "$(uv tool dir --bin);$env:Path"
```

## 完全オフライン環境

PyPI、Python配布元、GitHubのすべてへ接続できない場合は、wheelだけでは不足する。
次の配布物を用意する。

- TermKeeperのwheel
- Python 3.12のWindows環境
- Python 3.12と対象CPUに対応する全依存wheel
- 各ファイルのハッシュまたは署名

GitHub Releaseには、これらのPython依存をまとめた
`termkeeper-<version>-windows-x64-offline.zip`を添付する。Pythonとuv自体は含まれないため、
対象環境へPython 3.12とuvを事前に導入する。

ZIPを展開し、PowerShellで同梱installerを実行する。

```powershell
Expand-Archive .\termkeeper-*-windows-x64-offline.zip .\termkeeper-offline
Set-Location .\termkeeper-offline
.\install.ps1
```

手動で同等のbundleを用意する場合は、以下の構造にする。
依存wheelはWindowsの対象アーキテクチャ向けに準備し、`wheelhouse/`直下へ置く。
macOSやLinux向けのwheelを流用しない。

```text
termkeeper-offline/
├── install.ps1
└── wheelhouse/
    ├── termkeeper-<version>-py3-none-any.whl
    ├── alembic-....whl
    ├── sqlmodel-....whl
    ├── sqlalchemy-....whl
    └── その他の実行時依存wheel
```

インストール時はネットワークとパッケージIndexを明示的に無効化する。

```powershell
$wheel = Get-Item .\wheelhouse\termkeeper-*.whl
uv tool install `
  --python 3.12 `
  --offline `
  --no-index `
  --find-links .\wheelhouse `
  $wheel.FullName
uv tool update-shell
```

この手順はuvのローカルcacheへ偶然残っている依存へ頼らない状態でも検証する。
オフライン配布物は、対象と同等のWindows環境でインストールから主要CLI操作までテストしてから
配布する。

## ソースZIPを使う場合

wheelを作れない場合に限り、特定commitまたはtagのソースZIPを使用する。
ZIPを展開したソースディレクトリ自体は`PATH`へ追加しない。

```powershell
Expand-Archive .\TermKeeper.zip .\TermKeeper
Set-Location .\TermKeeper
uv tool install .
uv tool update-shell
```

通常利用では`--editable`を付けない。editable installは移動・削除され得る
ソースディレクトリへ実行環境が依存するため、開発用途に限定する。

## 更新と削除

更新前に新しいwheelのハッシュを同じ手順で検証する。使用中のSQLite DBはOS標準の
ユーザーデータ領域にあり、Tool環境とは分離されているが、重要な更新前にはバックアップする。

```powershell
uv tool uninstall termkeeper
uv tool install --python 3.12 $wheel.FullName
```

TermKeeperの削除は次で行う。

```powershell
uv tool uninstall termkeeper
```

Toolを削除しても利用者のDBは自動削除しない。DBやbackupの削除は、保存先と保持要件を
確認したうえで別途行う。

## 運用上の禁止事項

- ソース、`.venv`、DBをまとめたZIPを配布しない
- 展開したソースディレクトリを直接`PATH`へ追加しない
- セキュリティソフトの除外をTermKeeperの導入手順にしない
- ハッシュ不一致のファイルをインストールしない
- Tool環境を手作業で変更しない

uvのTool環境、`PATH`、オフラインおよび`--find-links`の仕様は、以下の公式文書を参照する。

- [uv: Using tools](https://docs.astral.sh/uv/guides/tools/)
- [uv: Tools](https://docs.astral.sh/uv/concepts/tools/)
- [uv: CLI reference](https://docs.astral.sh/uv/reference/cli/)
