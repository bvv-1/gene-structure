import { parseStringSync } from "gff-nostream";
import { type GeneStructureInfo, getGeneStructureInfo, getmRNAs } from "./gff";

type Position = {
  start: number;
  end: number;
};

export type GtfLine = {
  seq_id: string;
  source: string;
  type: string;
  start: number;
  end: number;
  score: number | null;
  strand: string | null;
  phase: string | null;
  attributes: Record<string, string>;
};

export function parseGtfLine(line: string): GtfLine | null {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) {
    return null;
  }
  const fields = trimmed.split("\t");
  if (fields.length < 9) {
    return null;
  }
  return {
    seq_id: fields[0],
    source: fields[1],
    type: fields[2],
    start: Number.parseInt(fields[3], 10),
    end: Number.parseInt(fields[4], 10),
    score: fields[5] === "." ? null : Number.parseFloat(fields[5]),
    strand: fields[6] === "." ? null : fields[6],
    phase: fields[7] === "." ? null : fields[7],
    attributes: parseGtfAttributes(fields[8]),
  };
}

export function parseGtfAttributes(
  attributeString: string,
): Record<string, string> {
  const attributes: Record<string, string> = {};
  if (!attributeString.trim()) {
    return attributes;
  }
  const pairs = attributeString.split(";");
  for (const pair of pairs) {
    const trimmed = pair.trim();
    if (!trimmed) continue;
    const match = trimmed.match(/^(\S+)\s+"([^"]*)"/);
    if (match) {
      attributes[match[1]] = match[2];
    }
  }
  return attributes;
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
  const format = detectFileFormat(fileName);
  if (format === "gtf") {
    return parseGtfString(content);
  }
  const gff = parseStringSync(content);
  const mRNAs = getmRNAs(gff);
  return getGeneStructureInfo(mRNAs);
}

export function parseGtfString(content: string): GeneStructureInfo[] {
  const lines = content.split("\n");
  const transcripts = new Map<
    string,
    {
      seq_id: string;
      source: string;
      strand: string | null;
      cds: Position[];
      exons: Position[];
      five_prime_utrs: Position[];
      three_prime_utrs: Position[];
    }
  >();

  for (const line of lines) {
    const parsed = parseGtfLine(line);
    if (!parsed) continue;

    const transcriptId = parsed.attributes.transcript_id;
    if (!transcriptId) continue;

    if (!transcripts.has(transcriptId)) {
      transcripts.set(transcriptId, {
        seq_id: parsed.seq_id,
        source: parsed.source,
        strand: parsed.strand,
        cds: [],
        exons: [],
        five_prime_utrs: [],
        three_prime_utrs: [],
      });
    }

    const transcript = transcripts.get(transcriptId);
    if (!transcript) continue;
    const featureType = parsed.type.toLowerCase();
    const pos: Position = { start: parsed.start, end: parsed.end };

    switch (featureType) {
      case "cds":
        transcript.cds.push(pos);
        break;
      case "exon":
        transcript.exons.push(pos);
        break;
      case "five_prime_utr":
        transcript.five_prime_utrs.push(pos);
        break;
      case "three_prime_utr":
        transcript.three_prime_utrs.push(pos);
        break;
    }
  }

  const result: GeneStructureInfo[] = [];
  for (const [transcriptId, t] of transcripts) {
    const allPositions = [
      ...t.cds,
      ...t.exons,
      ...t.five_prime_utrs,
      ...t.three_prime_utrs,
    ];
    const start = Math.min(...allPositions.map((p) => p.start));
    const end = Math.max(...allPositions.map((p) => p.end));

    result.push({
      seq_id: t.seq_id,
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
    });
  }

  return result;
}
