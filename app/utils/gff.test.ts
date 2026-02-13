import fs from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";
import { parseGff3String } from "./gff";

describe("GFFユーティリティ関数のテスト", () => {
  describe("parseGff3String", () => {
    test("イネでmRNAsを取得できる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gff");
      const gffContent = fs.readFileSync(filePath, "utf-8");
      const geneStructures = parseGff3String(gffContent);
      expect(geneStructures.length).toBe(15);
      for (const gene of geneStructures) {
        expect(gene.type).toBe("mRNA");
      }
    });

    test("ソルガムでmRNAsを取得できる", async () => {
      const filePath = path.resolve(
        __dirname,
        "./Sorghum_bicolor.Sorghum_bicolor_NCBIv3.51.gff3",
      );
      const gffContent = fs.readFileSync(filePath, "utf-8");
      const geneStructures = parseGff3String(gffContent);
      expect(geneStructures.length).toBe(2);
      for (const gene of geneStructures) {
        expect(gene.type).toBe("mRNA");
      }
    });
  });
});
