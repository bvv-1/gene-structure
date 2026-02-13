import fs from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";
import {
  detectFileFormat,
  parseFile,
  parseFileContent,
  parseGtfFile,
  parseGtfFileGenerator,
  parseGtfString,
} from "./gtf";
import { parseGtfStreamGenerator } from "./gtf-server";

describe("GTFパーサーのテスト", () => {
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

  describe("parseGtfStreamGenerator", () => {
    test("ストリームでGTFをパースできる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const stream = fs.createReadStream(filePath);
      const results = [];
      for await (const info of parseGtfStreamGenerator(stream)) {
        results.push(info);
      }

      expect(results.length).toBe(3);
    });

    test("ストリームでCDS座標が正しく抽出される", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const stream = fs.createReadStream(filePath);
      const results = [];
      for await (const info of parseGtfStreamGenerator(stream)) {
        results.push(info);
      }

      const transcript1 = results.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      expect(transcript1).toBeDefined();
      expect(transcript1?.cds.length).toBe(10);
      expect(transcript1?.cds[0]).toEqual({ start: 3449, end: 3616 });
    });

    test("ストリームでstrandが正しく設定される", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const stream = fs.createReadStream(filePath);
      const results = [];
      for await (const info of parseGtfStreamGenerator(stream)) {
        results.push(info);
      }

      const minus = results.find((r) => r.transcript_id === "Os01t0100300-00");
      expect(minus?.strand).toBe("-");
      expect(minus?.cds.length).toBe(2);
    });
  });

  describe("parseGtfStream - 大きなファイル", () => {
    test.skipIf(!fs.existsSync("./app/utils/gtf/Homo_sapiens.GRCh38.114.gtf"))(
      "1.6GBのGTFファイルをOOMなしでパースできる (Generator)",
      async () => {
        const filePath = "./app/utils/gtf/Homo_sapiens.GRCh38.114.gtf";
        const stream = fs.createReadStream(filePath);

        let count = 0;
        // AsyncGeneratorを使用してメモリ効率よく処理
        for await (const _ of parseGtfStreamGenerator(stream)) {
          count++;
          // 進捗表示（10万件ごと）
          if (count % 100000 === 0) {
            console.log(`処理中: ${count} トランスクリプト`);
          }
        }

        expect(count).toBeGreaterThan(0);
        console.log(`パースしたトランスクリプト数: ${count}`);
      },
      300000, // 5分タイムアウト
    );

    test.skipIf(
      !fs.existsSync(
        "./app/utils/gtf/Saccharomyces_cerevisiae.R64-1-1.114.gtf",
      ),
    )(
      "小さなファイル(酵母)でGeneratorが正しく動作する",
      async () => {
        const filePath =
          "./app/utils/gtf/Saccharomyces_cerevisiae.R64-1-1.114.gtf";
        const stream = fs.createReadStream(filePath);

        let count = 0;
        for await (const _ of parseGtfStreamGenerator(stream)) {
          count++;
        }

        expect(count).toBeGreaterThan(0);
        console.log(`酵母のトランスクリプト数: ${count}`);
      },
      60000,
    );
  });

  describe("parseGtfFileGenerator (File API)", () => {
    test("File APIでGTFをパースできる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gtf");

      const results = [];
      for await (const info of parseGtfFileGenerator(file)) {
        results.push(info);
      }

      expect(results.length).toBe(3);
    });

    test("File APIでCDS座標が正しく抽出される", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gtf");

      const results = [];
      for await (const info of parseGtfFileGenerator(file)) {
        results.push(info);
      }

      const transcript1 = results.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      expect(transcript1).toBeDefined();
      expect(transcript1?.cds.length).toBe(10);
    });

    test.skipIf(
      !fs.existsSync(
        "./app/utils/gtf/Saccharomyces_cerevisiae.R64-1-1.114.gtf",
      ),
    )(
      "File APIで酵母GTFファイルをパースできる (Generator)",
      async () => {
        // 注: 1.6GBのヒトGTFはfs.readFileSyncからFileへの変換時にメモリ問題が発生するため、
        // 酵母ファイルで動作確認。ブラウザ環境では大ファイルもストリーミングで処理可能。
        const filePath =
          "./app/utils/gtf/Saccharomyces_cerevisiae.R64-1-1.114.gtf";
        const content = fs.readFileSync(filePath);
        const file = new File(
          [content],
          "Saccharomyces_cerevisiae.R64-1-1.114.gtf",
        );

        let count = 0;
        for await (const _ of parseGtfFileGenerator(file)) {
          count++;
        }

        expect(count).toBeGreaterThan(0);
        console.log(`File APIでパースした酵母トランスクリプト数: ${count}`);
      },
      60000,
    );
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

  describe("parseFile (統合関数)", () => {
    test("GTFファイルをFileオブジェクトからパースできる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gtf");

      const result = await parseFile(file);
      expect(result.length).toBe(3);
      expect(result[0].transcript_id).toBeDefined();
    });

    test("GFF3ファイルをFileオブジェクトからパースできる", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gff");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gff");

      const result = await parseFile(file);
      expect(result.length).toBe(15);
      expect(result[0].transcript_id).toBeDefined();
    });

    test("GTFファイルでCDS座標が正しく抽出される", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gtf");

      const result = await parseFile(file);
      const transcript1 = result.find(
        (r) => r.transcript_id === "Os01t0100100-01",
      );
      expect(transcript1).toBeDefined();
      expect(transcript1?.cds.length).toBe(10);
      expect(transcript1?.cds[0]).toEqual({ start: 3449, end: 3616 });
    });
  });

  describe("parseGtfFile", () => {
    test("GTFファイルを配列として返す", async () => {
      const filePath = path.resolve(__dirname, "./transcripts.gtf");
      const content = fs.readFileSync(filePath);
      const file = new File([content], "transcripts.gtf");

      const result = await parseGtfFile(file);
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(3);
    });
  });
});
