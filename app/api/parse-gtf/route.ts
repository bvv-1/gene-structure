import GTF from "@gmod/gtf";
import { NextResponse } from "next/server";
import type { GeneStructureInfo } from "../../utils/gff";

type Position = {
  start: number;
  end: number;
};

interface GtfFeature {
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

function parseGtfString(content: string): GeneStructureInfo[] {
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

export async function POST(request: Request): Promise<NextResponse> {
  try {
    const { content } = (await request.json()) as { content: string };

    if (!content?.trim()) {
      return NextResponse.json(
        { error: "ファイルが空です。" },
        { status: 400 },
      );
    }

    const result = parseGtfString(content);

    if (result.length === 0) {
      return NextResponse.json(
        {
          error:
            "mRNA/トランスクリプトが見つかりませんでした。ファイルにmRNAフィーチャーが含まれていることを確認してください。",
        },
        { status: 400 },
      );
    }

    return NextResponse.json({ data: result });
  } catch (e) {
    return NextResponse.json(
      {
        error:
          "GTFファイルの解析に失敗しました。ファイルがGTF形式であることを確認してください。",
      },
      { status: 400 },
    );
  }
}
