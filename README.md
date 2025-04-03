# geneSTRUCTURE

https://vercel.com/bvv1s-projects/gene-structure

## 開発環境

### 必要条件

- Node.js 22.14.0 [mise](https://github.com/jdx/mise)でバージョンを管理
- Python 3.8以上?

### セットアップ

まず、仮想環境を作成してアクティベートします：

```bash
python3 -m venv venv
source venv/bin/activate
```

次に、依存関係をインストールします：

```bash
npm install
```

その後、開発サーバーを起動します（Pythonの依存関係は自動的にインストールされます）：

```bash
npm run dev
```

ブラウザで[http://localhost:3000](http://localhost:3000)を開くと、アプリケーションが表示されます。

## プロジェクト構成

.
├── app/ # フロントエンド (Next.js)
│ ├── components/ # 共通コンポーネント
│ ├── docs/ # ドキュメントページ
│ ├── faq/ # FAQページ
│ ├── page.tsx # メインページ
│ └── layout.tsx # レイアウトコンポーネント
├── api/ # バックエンド (FastAPI)
├── .gitignore # Gitの除外設定
├── .next/ # Next.jsのビルド出力
├── package.json # パッケージマネージャーの設定
├── tsconfig.json # TypeScriptの設定
├── next.config.js # Next.jsの設定
├── README.md # プロジェクトの説明
