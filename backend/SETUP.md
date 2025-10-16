# 開発環境セットアップガイド

## Pythonバージョン管理

このプロジェクトは **Python 3.12** を使用します。

### なぜバージョン管理が重要か

- Lambda関数は Python 3.12 で動作
- ローカル環境も同じバージョンを使わないと動作が異なる可能性
- 依存関係の互換性を保証

---

## 方法1: uv を使う（推奨・最新）

**uvとは:**
- Rustで書かれた超高速なPythonパッケージマネージャー
- pip, venv, pyenv の代替
- 最新のPythonツール

### インストール

#### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### セットアップ

```bash
# プロジェクトルートに移動
cd /path/to/jigsaw-puzzle

# Python 3.12 をインストール（自動）
uv python install 3.12

# 依存関係をインストール
uv sync

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows
```

### 開発サーバーの起動

```bash
# uvを使って直接実行（仮想環境の有効化不要）
uv run uvicorn backend.app:app --reload

# または、仮想環境を有効化してから
source .venv/bin/activate
uvicorn backend.app:app --reload
```

### パッケージの追加

```bash
# 依存関係を追加
uv add requests

# 開発用依存関係を追加
uv add --dev pytest
```

---

## 方法2: pyenv + venv（従来型）

### pyenv のインストール

#### macOS
```bash
brew install pyenv
```

#### Linux
```bash
curl https://pyenv.run | bash
```

### Python 3.12 のインストール

```bash
# Python 3.12 をインストール
pyenv install 3.12

# プロジェクトで使用するバージョンを設定
pyenv local 3.12
```

### 仮想環境の作成

```bash
# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r backend/requirements.txt
```

### 開発サーバーの起動

```bash
cd backend
uvicorn app:app --reload
```

---

## 方法3: システムのPython（非推奨）

システムにインストールされているPythonを使う方法ですが、推奨しません。

```bash
# Pythonバージョンを確認
python --version  # 3.12であることを確認

# 依存関係をインストール
pip install -r backend/requirements.txt

# 開発サーバーの起動
cd backend
uvicorn app:app --reload
```

**デメリット:**
- システムのPythonを汚染する
- プロジェクトごとの依存関係管理ができない
- 他のプロジェクトと競合する可能性

---

## バージョンの確認

### Pythonバージョン

```bash
python --version
# Python 3.12.x と表示されればOK
```

### uvのバージョン（uvを使う場合）

```bash
uv --version
```

### インストール済みパッケージの確認

```bash
# uvの場合
uv pip list

# pipの場合
pip list
```

---

## トラブルシューティング

### エラー: Python 3.12 が見つからない

**uv の場合:**
```bash
uv python install 3.12
```

**pyenv の場合:**
```bash
pyenv install 3.12
pyenv local 3.12
```

### エラー: boto3 がインポートできない

```bash
# 依存関係を再インストール
uv sync  # uvの場合
pip install -r backend/requirements.txt  # pipの場合
```

### エラー: AWS認証情報が設定されていない

```bash
aws configure
```

---

## 推奨される開発フロー

### uvを使う場合（推奨）

```bash
# 1. プロジェクトをクローン
git clone <repo-url>
cd jigsaw-puzzle

# 2. uvで環境をセットアップ（一度だけ）
uv sync

# 3. 開発サーバーを起動
uv run uvicorn backend.app:app --reload

# 4. ブラウザで開く
# http://localhost:8000/docs
```

### pyenv + venv を使う場合

```bash
# 1. プロジェクトをクローン
git clone <repo-url>
cd jigsaw-puzzle

# 2. Python 3.12 をインストール（一度だけ）
pyenv install 3.12
pyenv local 3.12

# 3. 仮想環境を作成（一度だけ）
python -m venv .venv
source .venv/bin/activate

# 4. 依存関係をインストール
pip install -r backend/requirements.txt

# 5. 開発サーバーを起動
cd backend
uvicorn app:app --reload
```

---

## IDEの設定

### VSCode

`.vscode/settings.json` に以下を追加:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black"
}
```

### PyCharm

1. Settings → Project → Python Interpreter
2. Add Interpreter → Existing
3. `.venv/bin/python` を選択

---

## まとめ

| 方法 | 推奨度 | 学習効果 | セットアップ時間 |
|------|-------|---------|----------------|
| **uv** | ★★★★★ | ★★★★★ | 1分 |
| **pyenv + venv** | ★★★★☆ | ★★★☆☆ | 5分 |
| **システムPython** | ★☆☆☆☆ | ★☆☆☆☆ | 1分 |

**学習重視なら uv を使いましょう！**
