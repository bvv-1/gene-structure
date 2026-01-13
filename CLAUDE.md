# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

geneSTRUCTURE - GFF3ファイルから遺伝子構造（エクソン、CDS、UTR、イントロン、ドメイン）を視覚化するWebアプリケーション。Next.js（フロントエンド）とFastAPI（バックエンド）のハイブリッド構成。

## 開発コマンド

```bash
# 開発サーバー起動（Next.js + FastAPI同時起動）
npm run dev

# フロントエンドのみ
npm run next-dev

# バックエンドのみ（要venv有効化）
source venv/bin/activate
npm run fastapi-dev

# ビルド・テスト・リント
npm run build
npm run test          # Vitest
npm run lint          # Next.js ESLint
npm run fmt           # Biome (./app配下のフォーマット)
npm run ts            # TypeScript型チェック
```

## アーキテクチャ

### フロントエンド (Next.js 15 + React 19)
- `app/page.tsx`: メインUI（GFFアップロード、トランスクリプト選択、SVGプレビュー）
- `app/utils/gff.ts`: GFF3パーサー（gff-nostreamを使用）、mRNA抽出、GeneStructureInfo生成
- `app/components/SvgViewer.tsx`: react-svg-pan-zoomによるSVG表示
- UIコンポーネント: Mantine v8

### バックエンド (FastAPI)
- `api/index.py`: REST APIエンドポイント、SVG生成ロジック
  - `POST /api/py/generate-gene-structure-svg`: GeneStructureInfoからSVG生成
  - クラス: `GeneFeature`（個別feature）、`GeneStructure`（遺伝子全体）
  - 機能: イントロン自動追加、プロテインドメイン座標変換（アミノ酸→ゲノム）、削除領域処理
- `api/original.py`: CLIツール

### API通信
- Next.js rewrites設定により `/api/py/*` をFastAPIにプロキシ
- 開発時: `http://127.0.0.1:8000`、本番: Vercel Functions

## データフロー

1. フロントエンド: GFF3ファイル解析 → mRNA抽出 → `GeneStructureInfo`生成
2. バックエンド: `GeneStructureInfo` → `GeneStructure`オブジェクト構築 → SVG描画

## 環境設定

- Node.js: 22.14.0（mise管理）
- Python: 3.12+（venv使用）
- フォーマッター: Biome（インデント: スペース2、クォート: ダブル）
- APIドキュメント: http://127.0.0.1:8000/api/py/docs
