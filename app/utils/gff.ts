import { type GFF3FeatureLine, util as gffUtil } from "@gmod/gff";

type Position = {
  start: number;
  end: number;
};

export type GeneStructureInfo = GFF3FeatureLine & {
  transcript_id: string;
  total_length: number;
  exons: Position[];
  cds: Position[];
  five_prime_utrs: Position[];
  three_prime_utrs: Position[];
};

/**
 * mRNA情報を蓄積するための型
 */
interface MRNAAccumulator {
  seq_id: string | null;
  source: string | null;
  strand: string | null;
  start: number | null;
  end: number | null;
  score: number | null;
  phase: string | null;
  attributes: Record<string, string[]> | null;
  cds: Position[];
  exons: Position[];
  five_prime_utrs: Position[];
  three_prime_utrs: Position[];
}

/**
 * GFF3行をパースしてmRNAとその子featureを蓄積
 */
function processGff3Line(
  line: string,
  mRNAs: Map<string, MRNAAccumulator>,
  childFeatures: Map<string, GFF3FeatureLine[]>,
): void {
  // コメント行と空行をスキップ
  if (line.startsWith("#") || !line.trim()) return;

  try {
    const feature = gffUtil.parseFeature(line);
    if (!feature?.attributes) return;

    const featureType = feature.type?.toLowerCase();

    // mRNAの場合
    if (featureType === "mrna") {
      const id = feature.attributes.ID?.[0];
      if (!id) return;

      if (!mRNAs.has(id)) {
        mRNAs.set(id, {
          seq_id: feature.seq_id,
          source: feature.source,
          strand: feature.strand,
          start: feature.start,
          end: feature.end,
          score: feature.score,
          phase: feature.phase,
          attributes: feature.attributes,
          cds: [],
          exons: [],
          five_prime_utrs: [],
          three_prime_utrs: [],
        });
      }

      // 先に子featureが来ていた場合に処理
      const pendingChildren = childFeatures.get(id);
      if (pendingChildren) {
        const mrna = mRNAs.get(id);
        if (mrna) {
          for (const child of pendingChildren) {
            addChildFeature(mrna, child);
          }
        }
        childFeatures.delete(id);
      }
      return;
    }

    // 子feature (exon, CDS, UTR) の場合
    if (
      ["exon", "cds", "five_prime_utr", "three_prime_utr"].includes(
        featureType || "",
      )
    ) {
      const parents = feature.attributes.Parent;
      if (!parents) return;

      for (const parentId of parents) {
        const mrna = mRNAs.get(parentId);
        if (mrna) {
          // 親mRNAが既に存在する場合
          addChildFeature(mrna, feature);
        } else {
          // 親mRNAがまだ来ていない場合（稀だが対応）
          if (!childFeatures.has(parentId)) {
            childFeatures.set(parentId, []);
          }
          childFeatures.get(parentId)?.push(feature);
        }
      }
    }
  } catch {
    // パースエラーは無視
  }
}

/**
 * 子featureをmRNAに追加
 */
function addChildFeature(
  mrna: MRNAAccumulator,
  feature: GFF3FeatureLine,
): void {
  const type = feature.type?.toLowerCase();
  const pos: Position = {
    start: feature.start ?? Number.NaN,
    end: feature.end ?? Number.NaN,
  };

  switch (type) {
    case "cds":
      mrna.cds.push(pos);
      break;
    case "exon":
      mrna.exons.push(pos);
      break;
    case "five_prime_utr":
      mrna.five_prime_utrs.push(pos);
      break;
    case "three_prime_utr":
      mrna.three_prime_utrs.push(pos);
      break;
  }
}

/**
 * mRNAマップからGeneStructureInfo配列を生成
 */
function* yieldGeneStructures(
  mRNAs: Map<string, MRNAAccumulator>,
): Generator<GeneStructureInfo, void, unknown> {
  for (const [transcriptId, mrna] of mRNAs) {
    // exon/CDS/UTRがないmRNAはスキップ
    const allPositions = [
      ...mrna.cds,
      ...mrna.exons,
      ...mrna.five_prime_utrs,
      ...mrna.three_prime_utrs,
    ];
    if (allPositions.length === 0) continue;

    // start/endの計算（mRNA自身のstart/endがあればそれを使用）
    const start = mrna.start ?? Math.min(...allPositions.map((p) => p.start));
    const end = mrna.end ?? Math.max(...allPositions.map((p) => p.end));

    yield {
      seq_id: mrna.seq_id,
      source: mrna.source,
      type: "mRNA",
      start,
      end,
      score: mrna.score,
      strand: mrna.strand as "+" | "-" | "?" | "." | null,
      phase: mrna.phase,
      attributes: mrna.attributes,
      transcript_id: transcriptId,
      total_length: end - start,
      cds: mrna.cds,
      exons: mrna.exons,
      five_prime_utrs: mrna.five_prime_utrs,
      three_prime_utrs: mrna.three_prime_utrs,
    };
  }
}

/**
 * ブラウザ用: FileオブジェクトからGFF3をストリーミングパース
 */
export async function* parseGff3FileGenerator(
  file: File,
): AsyncGenerator<GeneStructureInfo, void, unknown> {
  const mRNAs = new Map<string, MRNAAccumulator>();
  const childFeatures = new Map<string, GFF3FeatureLine[]>();

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
      processGff3Line(line, mRNAs, childFeatures);
    }
  }

  // 残りのバッファを処理
  if (buffer.trim()) {
    processGff3Line(buffer, mRNAs, childFeatures);
  }

  yield* yieldGeneStructures(mRNAs);
}

/**
 * ブラウザ用: FileオブジェクトからGFF3をパース（配列で返す）
 */
export async function parseGff3File(file: File): Promise<GeneStructureInfo[]> {
  if (file.size === 0) {
    throw new Error("ファイルが空です。GFF3形式のファイルを選択してください。");
  }

  const results: GeneStructureInfo[] = [];
  for await (const info of parseGff3FileGenerator(file)) {
    results.push(info);
  }

  if (results.length === 0) {
    throw new Error(
      "mRNA/トランスクリプトが見つかりませんでした。ファイルにmRNAフィーチャーが含まれていることを確認してください。",
    );
  }

  return results;
}

/**
 * 文字列からGFF3をパース（ストリーミング方式）
 */
export function parseGff3String(content: string): GeneStructureInfo[] {
  if (!content.trim()) {
    throw new Error("ファイルが空です。GFF3形式のファイルを選択してください。");
  }

  const mRNAs = new Map<string, MRNAAccumulator>();
  const childFeatures = new Map<string, GFF3FeatureLine[]>();

  const lines = content.split("\n");
  for (const line of lines) {
    processGff3Line(line, mRNAs, childFeatures);
  }

  const results = Array.from(yieldGeneStructures(mRNAs));

  if (results.length === 0) {
    throw new Error(
      "mRNA/トランスクリプトが見つかりませんでした。ファイルにmRNAフィーチャーが含まれていることを確認してください。",
    );
  }

  return results;
}

/**
 * GeneStructureInfoの配列から一意のseq_idリストを取得
 */
export function getSeqIds(geneStructures: GeneStructureInfo[]): string[] {
  const seqIds = new Set(
    geneStructures.map((g) => g.seq_id).filter((id): id is string => !!id),
  );
  return Array.from(seqIds).sort();
}

/**
 * 指定した領域と重なるトランスクリプトをフィルタリング
 * 部分的に重なる場合も含む
 */
export function filterByRegion(
  geneStructures: GeneStructureInfo[],
  seqId: string,
  start: number,
  end: number,
): GeneStructureInfo[] {
  return geneStructures
    .filter(
      (g) =>
        g.seq_id === seqId &&
        g.start != null &&
        g.end != null &&
        g.start <= end &&
        g.end >= start,
    )
    .sort((a, b) => (a.start ?? 0) - (b.start ?? 0));
}
