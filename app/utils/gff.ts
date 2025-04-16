import {
  parseStringSync,
  type GFF3Feature,
  type GFF3FeatureLine,
} from "gff-nostream";
import fs from "node:fs";

export type GeneStructureInfo = GFF3FeatureLine & {
  transcript_id: string;
  total_length: number;
  exon_positions: number[];
  five_prime_utr: number;
  three_prime_utr: number;
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
  for (const feature of gff) {
    if (feature.length > 1) {
      // FIXME: featureのlengthが1ではないパターンがわからない
      throw new Error("featureが1つではありません");
    }

    const stack: GFF3Feature[] = [feature];
    while (stack.length > 0) {
      const current = stack.pop();
      if (current && current[0].type === "mRNA") {
        mRNAs.push(current[0]);
      }
    }
  }
  return mRNAs;
}

export function getGeneStructureInfo(mRNAs: GFF3Feature): GeneStructureInfo[] {
  const geneStructureInfo: GeneStructureInfo[] = [];
  for (const mRNA of mRNAs) {
    const exon_positions: number[] = [];
    let five_prime_utr: number = Number.NaN;
    let three_prime_utr: number = Number.NaN;
    for (const feature of mRNA.child_features) {
      switch (feature[0].type) {
        case "exon":
          exon_positions.push(feature[0].start ?? Number.NaN);
          exon_positions.push(feature[0].end ?? Number.NaN);
          break;
        case "five_prime_utr":
          five_prime_utr = feature[0].start ?? Number.NaN;
          break;
        case "three_prime_utr":
          three_prime_utr = feature[0].start ?? Number.NaN;
          break;
      }
    }
    geneStructureInfo.push({
      ...mRNA,
      transcript_id: mRNA.attributes?.ID?.[0] ?? "",
      total_length: mRNA.end && mRNA.start ? mRNA.end - mRNA.start : Number.NaN,
      exon_positions: exon_positions,
      five_prime_utr: five_prime_utr,
      three_prime_utr: three_prime_utr,
    });
  }
  return geneStructureInfo;
}
