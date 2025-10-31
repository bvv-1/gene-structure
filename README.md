# geneSTRUCTURE

遺伝子構造を視覚化するためのWebアプリケーションとCLIツール

https://gene-structure.vercel.app/

https://github.com/user-attachments/assets/dea4a1d2-b128-43b8-bd30-643a94cdee6c

https://github.com/user-attachments/assets/1559326f-ecc5-4355-9e0d-131ee74db1f2

## 機能

- GFF3ファイルから遺伝子構造を読み込み
- エクソン、CDS、UTR、イントロン、ドメインの視覚化
- プロテインドメインのアミノ酸座標からゲノム座標への変換
- 削除領域(deletion)のサポート
- SVG形式での出力
- Web UI、REST API、CLIの3つのインターフェース

## 開発環境

### 必要条件

- Node.js 22.14.0 [mise](https://github.com/jdx/mise)でバージョンを管理
- Python 3.12以上

### セットアップ

まず、仮想環境を作成してアクティベートします：

```bash
python3 -m venv venv
source venv/bin/activate
```

次に、依存関係をインストールします：

```bash
npm install
pip install -r requirements.txt
```

その後、開発サーバーを起動します：

```bash
npm run dev
```

ブラウザで[http://localhost:3000](http://localhost:3000)を開くと、アプリケーションが表示されます。

### FastAPI サーバーのみ起動する場合

```bash
source venv/bin/activate
python3 -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
```

API ドキュメントは [http://127.0.0.1:8000/api/py/docs](http://127.0.0.1:8000/api/py/docs) で確認できます。

## 使い方

### Web UI

ブラウザで [https://gene-structure.vercel.app/](https://gene-structure.vercel.app/) にアクセスして、GUIから遺伝子構造を視覚化できます。

### REST API

FastAPIサーバーを起動後、以下のようにAPIを使用できます：

```bash
curl -X POST "http://127.0.0.1:8000/api/py/draw-gene" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_id": "Os06t0160700-01",
    "gff_file_path": "./geneSTRUCTURE_v2/gff3/IRGSP-1.0_representative/transcripts.gff",
    "deletion_regions": [],
    "domains": [],
    "protein_domain_start": 1,
    "protein_domain_end": 120,
    "protein_domain_name": "domain1"
  }' \
  -o output.svg
```

#### APIパラメータ

- `transcript_id` (required): トランスクリプトID
- `gff_file_path` (optional): GFF3ファイルのパス（デフォルト: `./gff3/IRGSP-1.0_representative/transcripts.gff`）
- `deletion_regions` (optional): 削除領域のリスト `[[start, end], ...]`
- `domains` (optional): ドメイン領域のリスト `[{"start": 200, "end": 500, "name": "Kinase", "color": "red"}, ...]`
- `protein_domain_start` (optional): プロテインドメインの開始位置（アミノ酸座標）
- `protein_domain_end` (optional): プロテインドメインの終了位置（アミノ酸座標）
- `protein_domain_name` (optional): プロテインドメインの名前

### CLI ツール

`api/original.py`を直接実行することで、コマンドラインから遺伝子構造を描画できます：

```bash
source venv/bin/activate
python3 api/original.py
```

パラメータは `api/original.py` の397行目以降で設定できます：

```python
gff_file = './geneSTRUCTURE_v2/gff3/IRGSP-1.0_representative/transcripts.gff'
transcript_id = 'Os06t0160700-01'
deletion_regions_relative = []
domains = [
    {'start': 200, 'end': 500, 'name': 'Kinase', 'color': 'red'},
    {'start': 600, 'end': 800, 'name': 'ATPase', 'color': 'blue'}
]
```

実行すると、`{transcript_id}_with_relative_deletions.svg` というファイルが生成されます。

## プロジェクト構成

```
.
├── app/                      # フロントエンド (Next.js)
│   ├── components/          # 共通コンポーネント
│   ├── docs/                # ドキュメントページ
│   ├── faq/                 # FAQページ
│   ├── page.tsx             # メインページ
│   └── layout.tsx           # レイアウトコンポーネント
├── api/                      # バックエンド (FastAPI)
│   ├── index.py             # FastAPI エンドポイント
│   └── original.py          # CLIツール
├── geneSTRUCTURE_v2/        # GFF3データ
│   └── gff3/
│       └── IRGSP-1.0_representative/
│           └── transcripts.gff
├── requirements.txt         # Python依存関係
├── package.json             # Node.js依存関係
├── tsconfig.json            # TypeScript設定
├── next.config.js           # Next.js設定
└── README.md                # プロジェクト説明
```

## 技術スタック

### フロントエンド
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

### バックエンド
- FastAPI
- Python 3.12
- svgwrite (SVG生成)
- reportlab (PDF生成)

## ライセンス

このプロジェクトはオープンソースです。
