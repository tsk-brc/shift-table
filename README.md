# Shift Table Management System

シフト管理システム - Django ベースの従業員シフト管理ツール

## 開発環境

このプロジェクトは [Cursor](https://cursor.sh/) を使用して開発されています。Cursorは、AIを活用した次世代のコードエディタで、以下の機能により開発効率を大幅に向上させています：

- 🤖 **AI アシスタント**: コードの生成、修正、リファクタリングをAIがサポート
- 🔍 **インテリジェント検索**: セマンティック検索による高速なコード検索
- 🧪 **テスト自動化**: テストケースの自動生成と実行
- 🐛 **デバッグ支援**: AIによるエラー解析と修正提案
- 📚 **コンテキスト理解**: プロジェクト全体の構造を理解した的確な提案

### Cursorでの開発の利点

- **高速な開発**: AIアシスタントによるコード生成で開発速度が向上
- **品質向上**: 自動的なテスト生成とリファクタリング提案
- **学習効果**: AIとの対話を通じたコーディングスキルの向上
- **チーム協力**: 統一された開発環境での効率的なコラボレーション

## 機能

- 📅 月間シフト表の表示
- 👥 従業員管理
- 🏢 シフト種別管理（出勤、休み、早番、遅番など）
- 🎨 シフト種別の色分け表示
- 📊 労働法規制チェック（連続勤務日数、最低労働者数）
- 🏖️ 会社休日管理（一括登録機能付き）
- 🤖 自動シフト作成機能
- 🔧 Django管理画面での完全な管理機能

## 技術スタック

- **Backend**: Django 4.2+
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Testing**: pytest, Selenium (E2E)
- **CI/CD**: CircleCI
- **Container**: Docker

## セットアップ

### 前提条件

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL

### 開発環境のセットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd shift-table
```

2. 依存関係をインストール
```bash
make install
# または
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. 環境変数を設定
```bash
export DJANGO_DB_NAME=shift_db
export DJANGO_DB_USER=shift_user
export DJANGO_DB_PASSWORD=shift_pass
export DJANGO_DB_HOST=localhost
```

4. データベースをセットアップ
```bash
make migrate
```

5. スーパーユーザーを作成
```bash
make superuser
```

6. 開発サーバーを起動
```bash
make runserver
```

### Docker環境でのセットアップ

1. Dockerコンテナを起動
```bash
make docker-run
```

2. マイグレーションを実行
```bash
docker-compose exec web python manage.py migrate
```

3. スーパーユーザーを作成
```bash
docker-compose exec web python manage.py createsuperuser
```

## テスト

### テストの実行

```bash
# 全テストを実行
make test

# カバレッジ付きテスト
make test-coverage

# E2Eテスト
make test-e2e

# 全チェック（lint、test、security）
make all
```

### テストカバレッジ

テストカバレッジは100%を目標としています。

```bash
# カバレッジレポートを生成
pytest --cov=shift --cov=shift_table --cov-report=html
```

## CI/CD

CircleCIを使用して以下のワークフローを実行しています：

1. **Lint**: コードの品質チェック
2. **Test**: ユニットテストとカバレッジ
3. **Security**: セキュリティチェック
4. **E2E**: エンドツーエンドテスト
5. **Build**: Dockerイメージのビルド

## 使用方法

### シフト表の表示

1. ブラウザで `http://localhost:8000/shift/` にアクセス
2. 年月を選択してシフト表を表示
3. セルをクリックしてシフトを編集

### 管理画面

1. `http://localhost:8000/admin/` にアクセス
2. スーパーユーザーでログイン
3. 各モデルを管理

### 会社休日の一括登録

1. 管理画面で「会社休日」→「一括追加」をクリック
2. 休日タイプを選択（週次、月次、範囲、単発）
3. 必要項目を入力して登録

### 自動シフト作成

1. 管理画面で「シフト」→「自動シフト作成」をクリック
2. 年月と作成モードを選択
3. 実行してシフトを自動生成

### パスワードリセット・変更

#### メールベースのパスワードリセット

パスワードを忘れた場合のリセット手順：

1. 管理画面のログインページ（`http://localhost:8000/admin/`）で「パスワードを忘れた場合」をクリック
2. 登録されているメールアドレスを入力
3. パスワードリセット用のリンクがメールで送信されます
4. メール内のリンクをクリックして新しいパスワードを設定

**注意**: 開発環境では、メールはコンソールに出力されます。本番環境では適切なSMTP設定が必要です。

#### 直接パスワード変更

メール送信が不要な、より簡単なパスワード変更方法：

1. 管理画面のログインページ（`http://localhost:8000/admin/`）で「直接パスワード変更」をクリック
2. ユーザー名と新しいパスワードを入力
3. パスワードを確認入力
4. 送信ボタンをクリックしてパスワードを変更

**特徴**:
- メール送信が不要
- 管理者権限を持つユーザーも変更可能
- パスワードは8文字以上が必要
- ユーザー名の存在確認あり

**セキュリティ**:
- CSRF保護が有効
- パスワード強度チェック
- 存在しないユーザー名のエラー処理

## プロジェクト構造

```
shift-table/
├── shift/                    # メインアプリケーション
│   ├── models.py            # データモデル
│   ├── views.py             # ビュー
│   ├── admin.py             # 管理画面設定
│   ├── forms.py             # フォーム
│   ├── tests/               # テスト
│   │   ├── test_models.py   # モデルテスト
│   │   ├── test_views.py    # ビューテスト
│   │   ├── test_admin.py    # 管理画面テスト
│   │   ├── test_forms.py    # フォームテスト
│   │   └── test_e2e.py      # E2Eテスト
│   └── templates/           # テンプレート
├── shift_table/             # プロジェクト設定
├── requirements.txt         # 本番依存関係
├── requirements-dev.txt     # 開発依存関係
├── docker-compose.yml       # Docker設定
├── Dockerfile              # Dockerイメージ
├── pytest.ini             # pytest設定
├── Makefile               # 開発コマンド
└── .circleci/             # CI/CD設定
```

## データモデル

### Employee（従業員）
- 名前

### ShiftType（シフト種別）
- 名前
- 勤務日フラグ
- 色

### Shift（シフト）
- 従業員
- 日付
- シフト種別

### CompanyHoliday（会社休日）
- 日付
- 名前
- 説明

### LaborLawSettings（労働設定）
- 最大連続勤務日数
- 最低労働者数

## 開発ガイドライン

### コードスタイル

- Black を使用したコードフォーマット
- Flake8 を使用したリンティング
- 最大行長: 120文字

### テスト

- 新機能には必ずテストを追加
- カバレッジ100%を維持
- ユニットテスト、統合テスト、E2Eテストを適切に使い分け

### コミットメッセージ

```
feat: 新機能の追加
fix: バグ修正
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
test: テスト追加・修正
chore: その他の変更
```

## ライセンス

MIT License

## 貢献

1. フォークを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。 