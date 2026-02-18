import readline from "node:readline";
import type { Readable } from "node:stream";
import GTF from "@gmod/gtf";
import type { GeneStructureInfo } from "./gff";

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

interface TranscriptAccumulator {
  seq_name: string;
  source: string;
  strand: string | null;
  cds: Position[];
  exons: Position[];
  five_prime_utrs: Position[];
  three_prime_utrs: Position[];
}

function cleanAttributeValue(value: string): string {
  return value.replace(/^"(.*)"$/, "$1");
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

/**
 * Node.jsストリーム用GTFパーサー（サーバーサイド専用）
 * クライアントサイドでは使用不可（node:readlineはブラウザで動作しない）
 */
export async function* parseGtfStreamGenerator(
  stream: Readable,
): AsyncGenerator<GeneStructureInfo, void, unknown> {
  const rl = readline.createInterface({
    input: stream,
    crlfDelay: Number.POSITIVE_INFINITY,
  });

  const transcripts = new Map<string, TranscriptAccumulator>();

  for await (const line of rl) {
    processGtfLine(line, transcripts);
  }

  yield* yieldTranscripts(transcripts);
}
