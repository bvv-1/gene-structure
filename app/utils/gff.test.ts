import fs from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import { parseGff, getmRNAs } from "./gff";

describe("GFFユーティリティ関数のテスト", () => {
  let gffFile: File;

  // テスト前にGFFファイルを読み込む
  beforeAll(() => {
    const filePath = path.resolve(__dirname, "./transcripts.gff");
    const gffContent = fs.readFileSync(filePath, "utf-8");
    const blob = new Blob([gffContent], { type: "text/plain" });
    gffFile = new File([blob], "transcripts.gff");
  });

  describe("parseGff", () => {
    test("GFFファイルをパースできる", async () => {
      const gff = await parseGff(gffFile);
      expect(gff.length).toBe(15);
    });
  });

  describe("getmRNAs", () => {
    test("mRNAsを取得できる", async () => {
      const gff = await parseGff(gffFile);
      const mRNAs = getmRNAs(gff);
      for (const mRNA of mRNAs) {
        expect(mRNA.type).toBe("mRNA");
        console.log(mRNA.attributes?.ID?.[0]);
      }
    });
  });
});
