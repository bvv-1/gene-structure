import fs from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import { getmRNAs } from "./gff";
import { parseStringSync } from "gff-nostream";

describe("GFFユーティリティ関数のテスト", () => {
  describe("getmRNAs", () => {
    test("イネでmRNAsを取得できる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gff");
      const gffContent = fs.readFileSync(filePath, "utf-8");
      const gff = parseStringSync(gffContent);
      const mRNAs = getmRNAs(gff);
      expect(mRNAs.length).toBe(15);
      for (const mRNA of mRNAs) {
        expect(mRNA.type).toBe("mRNA");
      }
    });

    test("ソルガムでmRNAsを取得できる", async () => {
      const filePath = path.resolve(
        __dirname,
        "./Sorghum_bicolor.Sorghum_bicolor_NCBIv3.51.gff3",
      );
      const gffContent = fs.readFileSync(filePath, "utf-8");
      const gff = parseStringSync(gffContent);
      const mRNAs = getmRNAs(gff);
      expect(mRNAs.length).toBe(2);
      for (const mRNA of mRNAs) {
        expect(mRNA.type).toBe("mRNA");
      }
    });
  });
});
