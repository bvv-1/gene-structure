import {
  parseStringSync,
  type GFF3Feature,
  type GFF3FeatureLine,
} from "gff-nostream";

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

export async function parseGff(file: File): Promise<GFF3Feature[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (!event.target || typeof event.target.result !== "string") {
        reject(new Error("ファイルの読み込みに失敗しました"));
        return;
      }

      try {
        const fileContent = event.target.result;
        const result = parseStringSync(fileContent);
        resolve(result);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error("ファイルの読み込み中にエラーが発生しました"));
    };

    reader.readAsText(file);
  });
}

export function getmRNAs(gff: GFF3Feature[]): GFF3Feature {
  const mRNAs: GFF3Feature = [];
  const seen = new Set<string>();
  for (const features of gff) {
    for (const feature of features) {
      const stack: GFF3Feature = [feature];
      while (stack.length > 0) {
        const current = stack.pop();
        if (!current) {
          continue;
        }
        if (current.attributes?.ID && current.attributes?.ID.length > 0) {
          if (seen.has(current.attributes.ID[0])) {
            continue;
          }
          seen.add(current.attributes.ID[0]);
        }

        if (current.type?.toLowerCase() === "mrna") {
          mRNAs.push(current);
        }
        for (const child_features of current.child_features) {
          for (const child of child_features) {
            stack.push(child);
          }
        }
      }
    }
  }
  return mRNAs;
}

export function getGeneStructureInfo(mRNAs: GFF3Feature): GeneStructureInfo[] {
  const geneStructureInfo: GeneStructureInfo[] = [];
  for (const mRNA of mRNAs) {
    const cds: Position[] = [];
    const exons: Position[] = [];
    const five_prime_utrs: Position[] = [];
    const three_prime_utrs: Position[] = [];
    for (const features of mRNA.child_features) {
      for (const feature of features) {
        const feature_type = feature.type?.toLowerCase();
        switch (feature_type) {
          case "cds":
            cds.push({
              start: feature.start ?? Number.NaN,
              end: feature.end ?? Number.NaN,
            });
            break;
          case "exon":
            exons.push({
              start: feature.start ?? Number.NaN,
              end: feature.end ?? Number.NaN,
            });
            break;
          case "five_prime_utr":
            five_prime_utrs.push({
              start: feature.start ?? Number.NaN,
              end: feature.end ?? Number.NaN,
            });
            break;
          case "three_prime_utr":
            three_prime_utrs.push({
              start: feature.start ?? Number.NaN,
              end: feature.end ?? Number.NaN,
            });
            break;
        }
      }
    }
    geneStructureInfo.push({
      seq_id: mRNA.seq_id,
      source: mRNA.source,
      type: mRNA.type,
      start: mRNA.start,
      end: mRNA.end,
      score: mRNA.score,
      strand: mRNA.strand,
      phase: mRNA.phase,
      attributes: mRNA.attributes,
      transcript_id: mRNA.attributes?.ID?.[0] ?? "",
      total_length: mRNA.end && mRNA.start ? mRNA.end - mRNA.start : Number.NaN,
      cds,
      exons,
      five_prime_utrs,
      three_prime_utrs,
    });
  }
  return geneStructureInfo;
}
