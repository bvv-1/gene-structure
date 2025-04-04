import fs from "fs";
import path from "path";
import { beforeAll, describe, expect, test } from "vitest";
import { getStructure, getTranscriptId } from "./gff";

describe("GFFユーティリティ関数のテスト", () => {
  let gffContent: string;

  // テスト前にGFFファイルを読み込む
  beforeAll(() => {
    const filePath = path.resolve(
      __dirname,
      "./Sorghum_bicolor.Sorghum_bicolor_NCBIv3.51.gff3",
    );
    gffContent = fs.readFileSync(filePath, "utf-8");
  });

  describe("getTranscriptId関数", () => {
    test("有効な遺伝子IDからトランスクリプトIDとストランドを取得する", () => {
      // 実際のSorghum bicolorのGFFファイルに存在する遺伝子IDを使用
      const geneId = "SORBI_3001G000100";
      const { transcriptId, strand } = getTranscriptId(gffContent, geneId);

      expect(transcriptId).not.toBe("");
      expect(["+", "-"]).toContain(strand);
    });

    test("存在しない遺伝子IDの場合は空の結果を返す", () => {
      const geneId = "存在しない遺伝子ID";
      const { transcriptId, strand } = getTranscriptId(gffContent, geneId);

      expect(transcriptId).toBe("");
      expect(strand).toBe("");
    });
  });

  describe("getStructure関数", () => {
    test("有効なトランスクリプトIDから構造情報を取得する", () => {
      // 最初に遺伝子IDからトランスクリプトIDを取得
      const geneId = "SORBI_3001G000100";
      const { transcriptId } = getTranscriptId(gffContent, geneId);

      // トランスクリプトIDから構造情報を取得
      const { totalLength, exonPositions, fivePrimeUTR, threePrimeUTR } =
        getStructure(gffContent, transcriptId);

      expect(totalLength).toBeGreaterThan(0);
      expect(exonPositions.length).toBeGreaterThan(0);
      expect(exonPositions.length % 2).toBe(0); // エクソン位置は開始と終了のペアなので常に偶数

      // UTRは存在しない場合もあるため、値が0以上であることを確認
      expect(fivePrimeUTR).toBeGreaterThanOrEqual(0);
      expect(threePrimeUTR).toBeGreaterThanOrEqual(0);
    });

    test("存在しないトランスクリプトIDの場合はデフォルト値を返す", () => {
      const transcriptId = "存在しないトランスクリプトID";
      const { totalLength, exonPositions, fivePrimeUTR, threePrimeUTR } =
        getStructure(gffContent, transcriptId);

      expect(totalLength).toBe(0);
      expect(exonPositions).toEqual([]);
      expect(fivePrimeUTR).toBe(0);
      expect(threePrimeUTR).toBe(0);
    });
  });
});
