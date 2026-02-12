import fs from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";
import {
  type GtfLine,
  detectFileFormat,
  parseFileContent,
  parseGtfAttributes,
  parseGtfLine,
  parseGtfString,
} from "./gtf";

describe("GTFパーサーのテスト", () => {
  describe("parseGtfAttributes", () => {
    test("gene_idとtranscript_idをパースできる", () => {
      const attr = 'gene_id "Os01g0100100"; transcript_id "Os01t0100100-01";';
      const result = parseGtfAttributes(attr);
      expect(result.gene_id).toBe("Os01g0100100");
      expect(result.transcript_id).toBe("Os01t0100100-01");
    });

    test("追加属性もパースできる", () => {
      const attr =
        'gene_id "ENSG00000223972"; transcript_id "ENST00000456328"; gene_name "DDX11L1"; gene_biotype "transcribed_unprocessed_pseudogene";';
      const result = parseGtfAttributes(attr);
      expect(result.gene_id).toBe("ENSG00000223972");
      expect(result.transcript_id).toBe("ENST00000456328");
      expect(result.gene_name).toBe("DDX11L1");
      expect(result.gene_biotype).toBe("transcribed_unprocessed_pseudogene");
    });

    test("空文字列は空オブジェクトを返す", () => {
      const result = parseGtfAttributes("");
      expect(result).toEqual({});
    });
  });

  describe("parseGtfLine", () => {
    test("CDS行をパースできる", () => {
      const line =
        'chr01\tirgsp1_rep\tCDS\t3449\t3616\t.\t+\t0\tgene_id "Os01g0100100"; transcript_id "Os01t0100100-01";';
      const result = parseGtfLine(line);
      expect(result).toEqual({
        seq_id: "chr01",
        source: "irgsp1_rep",
        type: "CDS",
        start: 3449,
        end: 3616,
        score: null,
        strand: "+",
        phase: "0",
        attributes: {
          gene_id: "Os01g0100100",
          transcript_id: "Os01t0100100-01",
        },
      } satisfies GtfLine);
    });

    test("five_prime_utr行をパースできる", () => {
      const line =
        'chr01\tirgsp1_rep\tfive_prime_utr\t2983\t3268\t.\t+\t.\tgene_id "Os01g0100100"; transcript_id "Os01t0100100-01";';
      const result = parseGtfLine(line);
      expect(result?.type).toBe("five_prime_utr");
      expect(result?.start).toBe(2983);
      expect(result?.end).toBe(3268);
      expect(result?.phase).toBeNull();
    });

    test("コメント行はnullを返す", () => {
      const result = parseGtfLine("# this is a comment");
      expect(result).toBeNull();
    });

    test("空行はnullを返す", () => {
      const result = parseGtfLine("");
      expect(result).toBeNull();
    });
  });

  describe("parseGtfString", () => {
    test("GTFからGeneStructureInfoを生成できる", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      expect(result.length).toBe(3);
    });

    test("transcript_idが正しく設定される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      const ids = result.map((r) => r.transcript_id);
      expect(ids).toContain("Os01t0100100-01");
      expect(ids).toContain("Os01t0100200-01");
      expect(ids).toContain("Os01t0100300-00");
    });

    test("CDS座標が正しく抽出される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      const transcript1 = result.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      expect(transcript1).toBeDefined();
      expect(transcript1?.cds.length).toBe(10);
      expect(transcript1?.cds[0]).toEqual({ start: 3449, end: 3616 });
    });

    test("UTR座標が正しく抽出される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      const transcript1 = result.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      expect(transcript1?.five_prime_utrs.length).toBe(2);
      expect(transcript1?.three_prime_utrs.length).toBe(2);
    });

    test("strandが正しく設定される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      const minus = result.find((r) => r.transcript_id === "Os01t0100300-00");
      expect(minus?.strand).toBe("-");
      expect(minus?.cds.length).toBe(2);
    });

    test("total_lengthが正しく計算される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      const transcript1 = result.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      // start=2983, end=10815 → total_length = 10815 - 2983 = 7832
      expect(transcript1?.total_length).toBe(10815 - 2983);
    });

    test("seq_idが正しく設定される", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseGtfString(content);
      for (const r of result) {
        expect(r.seq_id).toBe("chr01");
      }
    });
  });

  describe("detectFileFormat", () => {
    test(".gtf拡張子はgtfを返す", () => {
      expect(detectFileFormat("genes.gtf")).toBe("gtf");
    });

    test(".gff拡張子はgff3を返す", () => {
      expect(detectFileFormat("genes.gff")).toBe("gff3");
    });

    test(".gff3拡張子はgff3を返す", () => {
      expect(detectFileFormat("genes.gff3")).toBe("gff3");
    });

    test("大文字拡張子も正しく判別される", () => {
      expect(detectFileFormat("genes.GTF")).toBe("gtf");
      expect(detectFileFormat("genes.GFF3")).toBe("gff3");
    });

    test("不明な拡張子はgff3をデフォルトとする", () => {
      expect(detectFileFormat("genes.txt")).toBe("gff3");
    });
  });

  describe("parseFileContent", () => {
    test("GTFファイルをGeneStructureInfoに変換できる", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseFileContent(content, "transcripts.gtf");
      expect(result.length).toBe(3);
      expect(result[0].transcript_id).toBeDefined();
    });

    test("GFF3ファイルをGeneStructureInfoに変換できる", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gff");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseFileContent(content, "transcripts.gff");
      expect(result.length).toBe(15);
      expect(result[0].transcript_id).toBeDefined();
    });

    test("GFF3ファイルのCDS座標が正しい", () => {
      const filePath = path.resolve(__dirname, "./transcripts.gff");
      const content = fs.readFileSync(filePath, "utf-8");
      const result = parseFileContent(content, "transcripts.gff");
      const first = result.find((r) => r.transcript_id === "Os01t0100100-01");
      expect(first).toBeDefined();
      expect(first?.cds.length).toBe(10);
      expect(first?.cds[0]).toEqual({ start: 3449, end: 3616 });
    });
  });
});
