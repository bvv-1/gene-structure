import GTF from "@gmod/gtf";
import { parseStringSync } from "gff-nostream";
import { type GeneStructureInfo, getGeneStructureInfo, getmRNAs } from "./gff";

// @gmod/gtfのutil関数を取得（ESM互換）
const gtfModule = (GTF as { default?: typeof GTF }).default || GTF;
const gtfUtil = gtfModule.util as unknown as {
  parseFeature: (line: string) => GtfParsedFeature | null;
};

type Position = {
  start: number;
  end: number;
};

interface GtfParsedFeature {
  seq_name: string;
  source: string;
  featureType: string;
  start: number;
  end: number;
  score: number | null;
  strand: string | null;
  frame: string | null;
  attributes: Record<string, string[]>;
}

interface GtfFeature extends GtfParsedFeature {
  seq_name: string;
  source: string;
  featureType: string;
  start: number;
  end: number;
  score: number | null;
  strand: string | null;
  frame: string | null;
  attributes: Record<string, string[]>;
  child_features: GtfFeature[][];
  derived_features: unknown[];
}

function cleanAttributeValue(value: string): string {
  return value.replace(/^"(.*)"$/, "$1");
}

export function detectFileFormat(fileName: string): "gff3" | "gtf" {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "gtf") {
    return "gtf";
  }
  return "gff3";
}

export function parseFileContent(
  content: string,
  fileName: string,
): GeneStructureInfo[] {
  if (!content.trim()) {
    throw new Error(
      "ファイルが空です。GFF3またはGTF形式のファイルを選択してください。",
    );
  }

  const format = detectFileFormat(fileName);

  let result: GeneStructureInfo[];
  if (format === "gtf") {
    result = parseGtfString(content);
  } else {
    try {
      const gff = parseStringSync(content);
      const mRNAs = getmRNAs(gff);
      result = getGeneStructureInfo(mRNAs);
    } catch (e) {
      throw new Error(
        "GFF3ファイルの解析に失敗しました。ファイルがGFF3形式であることを確認してください。",
      );
    }
  }

  if (result.length === 0) {
    throw new Error(
      "mRNA/トランスクリプトが見つかりませんでした。ファイルにmRNAフィーチャーが含まれていることを確認してください。",
    );
  }

  return result;
}

interface TranscriptAccumulator {
  seq_name: string;
  source: string;
  strand: string | null;
  cds: Position[];
  exons: Position[];
  five_prime_utrs: Position[];
  three_prime_utrs: Position[];
}

function processGtfLine(
  line: string,
  transcripts: Map<string, TranscriptAccumulator>,
): void {
  // コメント行と空行をスキップ
  if (line.startsWith("#") || !line.trim()) return;

  try {
    const feature = gtfUtil.parseFeature(line);
    if (!feature?.attributes) return;

    const transcriptIdAttr = feature.attributes.transcript_id;
    const transcriptIdRaw = Array.isArray(transcriptIdAttr)
      ? transcriptIdAttr[0]
      : transcriptIdAttr;

    if (!transcriptIdRaw) return;

    const transcriptId = cleanAttributeValue(transcriptIdRaw);
    const featureType = feature.featureType?.toLowerCase();

    // トランスクリプトが存在しない場合は新規作成
    if (!transcripts.has(transcriptId)) {
      transcripts.set(transcriptId, {
        seq_name: feature.seq_name,
        source: feature.source,
        strand: feature.strand,
        cds: [],
        exons: [],
        five_prime_utrs: [],
        three_prime_utrs: [],
      });
    }

    const t = transcripts.get(transcriptId);
    if (!t) return;

    const pos: Position = { start: feature.start, end: feature.end };

    switch (featureType) {
      case "cds":
        t.cds.push(pos);
        break;
      case "exon":
        t.exons.push(pos);
        break;
      case "five_prime_utr":
      case "5utr":
        t.five_prime_utrs.push(pos);
        break;
      case "three_prime_utr":
      case "3utr":
        t.three_prime_utrs.push(pos);
        break;
    }
  } catch {
    // パースエラーは無視
  }
}

function* yieldTranscripts(
  transcripts: Map<string, TranscriptAccumulator>,
): Generator<GeneStructureInfo, void, unknown> {
  for (const [transcriptId, t] of transcripts) {
    const allPositions = [
      ...t.cds,
      ...t.exons,
      ...t.five_prime_utrs,
      ...t.three_prime_utrs,
    ];
    if (allPositions.length === 0) continue;

    const start = Math.min(...allPositions.map((p) => p.start));
    const end = Math.max(...allPositions.map((p) => p.end));

    yield {
      seq_id: t.seq_name,
      source: t.source,
      type: "mRNA",
      start,
      end,
      score: null,
      strand: t.strand as "+" | "-" | "?" | "." | null,
      phase: null,
      attributes: {
        ID: [transcriptId],
      },
      transcript_id: transcriptId,
      total_length: end - start,
      cds: t.cds,
      exons: t.exons,
      five_prime_utrs: t.five_prime_utrs,
      three_prime_utrs: t.three_prime_utrs,
    };
  }
}

export async function* parseGtfFileGenerator(
  file: File,
): AsyncGenerator<GeneStructureInfo, void, unknown> {
  const transcripts = new Map<string, TranscriptAccumulator>();
  const stream = file.stream();
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader();

  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += value;
    const lines = buffer.split("\n");
    // 最後の不完全な行をバッファに残す
    buffer = lines.pop() || "";

    for (const line of lines) {
      processGtfLine(line, transcripts);
    }
  }

  // 残りのバッファを処理
  if (buffer.trim()) {
    processGtfLine(buffer, transcripts);
  }

  yield* yieldTranscripts(transcripts);
}

// ブラウザ用：Fileオブジェクトから直接GTFをパース（常にストリーミング）
export async function parseGtfFile(file: File): Promise<GeneStructureInfo[]> {
  const results: GeneStructureInfo[] = [];
  for await (const info of parseGtfFileGenerator(file)) {
    results.push(info);
  }
  return results;
}

// ブラウザ用：GFF3/GTF対応の統合関数（Fileオブジェクト用）
export async function parseFile(file: File): Promise<GeneStructureInfo[]> {
  const format = detectFileFormat(file.name);

  if (format === "gtf") {
    // GTF: 常にストリーミング処理
    return parseGtfFile(file);
  }

  // GFF3: gff-nostreamがストリーミング非対応のため文字列ベース
  const content = await file.text();
  return parseGff3String(content);
}

// GFF3パース関数（parseFileContentから分離）
function parseGff3String(content: string): GeneStructureInfo[] {
  if (!content.trim()) {
    throw new Error(
      "ファイルが空です。GFF3またはGTF形式のファイルを選択してください。",
    );
  }

  try {
    const gff = parseStringSync(content);
    const mRNAs = getmRNAs(gff);
    const result = getGeneStructureInfo(mRNAs);

    if (result.length === 0) {
      throw new Error(
        "mRNA/トランスクリプトが見つかりませんでした。ファイルにmRNAフィーチャーが含まれていることを確認してください。",
      );
    }

    return result;
  } catch (e) {
    if (e instanceof Error && e.message.includes("mRNA/トランスクリプト")) {
      throw e;
    }
    throw new Error(
      "GFF3ファイルの解析に失敗しました。ファイルがGFF3形式であることを確認してください。",
    );
  }
}

export function parseGtfString(content: string): GeneStructureInfo[] {
  const parsed = GTF.parseStringSync(content) as GtfFeature[][];

  const result: GeneStructureInfo[] = [];

  for (const transcriptGroup of parsed) {
    const transcript = transcriptGroup[0];
    if (!transcript) continue;

    const attributes = transcript.attributes || {};
    const transcriptIdAttr = attributes.transcript_id;
    const transcriptIdRaw = Array.isArray(transcriptIdAttr)
      ? transcriptIdAttr[0]
      : transcriptIdAttr;

    if (!transcriptIdRaw) continue;

    const transcriptId = cleanAttributeValue(transcriptIdRaw);

    const cds: Position[] = [];
    const exons: Position[] = [];
    const five_prime_utrs: Position[] = [];
    const three_prime_utrs: Position[] = [];

    const childFeatures = transcript.child_features || [];
    for (const featureGroup of childFeatures) {
      for (const feature of featureGroup) {
        const type = feature.featureType?.toLowerCase();
        const pos: Position = { start: feature.start, end: feature.end };

        switch (type) {
          case "cds":
            cds.push(pos);
            break;
          case "exon":
            exons.push(pos);
            break;
          case "five_prime_utr":
          case "5utr":
            five_prime_utrs.push(pos);
            break;
          case "three_prime_utr":
          case "3utr":
            three_prime_utrs.push(pos);
            break;
        }
      }
    }

    const allPositions = [
      ...cds,
      ...exons,
      ...five_prime_utrs,
      ...three_prime_utrs,
    ];

    if (allPositions.length === 0) continue;

    const start = Math.min(...allPositions.map((p) => p.start));
    const end = Math.max(...allPositions.map((p) => p.end));

    result.push({
      seq_id: transcript.seq_name,
      source: transcript.source,
      type: "mRNA",
      start,
      end,
      score: null,
      strand: transcript.strand as "+" | "-" | "?" | "." | null,
      phase: null,
      attributes: {
        ID: [transcriptId],
      },
      transcript_id: transcriptId,
      total_length: end - start,
      cds,
      exons,
      five_prime_utrs,
      three_prime_utrs,
    });
  }

  return result;
}
