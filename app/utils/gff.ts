export type GeneStructureInfo = {
  gene_id: string;
  transcript_id: string;
  strand: string;
  total_length: number;
  exon_positions: number[];
  five_prime_utr: number;
  three_prime_utr: number;
};

/**
 * トランスクリプト構造の情報を表すインターフェース
 */
export interface TranscriptStructure {
  totalLength: number;
  exonPositions: number[];
  fivePrimeUTR: number;
  threePrimeUTR: number;
}

/**
 * トランスクリプト情報を表すインターフェース
 */
export interface TranscriptInfo {
  transcriptId: string;
  strand: string;
}

/**
 * GFFファイルの内容からトランスクリプトの構造情報を取得する
 * @param fileContent GFFファイルの内容（テキスト形式）
 * @param transcriptId 対象のトランスクリプトID
 * @returns トランスクリプト構造の情報（全長、エクソン位置、5'UTR、3'UTR）
 */
export function getStructure(
  fileContent: string,
  transcriptId: string,
): TranscriptStructure {
  const exonPos: number[] = [];
  const exonLen: number[] = [];
  let totalLength = 0;
  let fivePrimeUTR = 0;
  let threePrimeUTR = 0;

  // ファイル内容を行ごとに分割
  const lines = fileContent.split(/\r?\n/);

  for (const line of lines) {
    if (line.startsWith("#")) {
      continue;
    }

    if (line.trim() === "") {
      continue;
    }

    const columns = line.split("\t");
    if (columns.length < 9) continue; // 必要なカラム数がない場合はスキップ

    const idMatch = columns[8].match(/ID=([^;]+)/);
    if (columns[2] === "mRNA" && idMatch && idMatch[1] === transcriptId) {
      totalLength =
        (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
      continue;
    }

    const parentMatch = columns[8].match(/Parent=([^;]+)/);
    if (parentMatch && parentMatch[1] === transcriptId) {
      if (columns[2] === "exon") {
        exonPos.push(Number.parseInt(columns[3]));
        exonPos.push(Number.parseInt(columns[4]));
        exonLen.push(
          (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10,
        );
      } else if (columns[2] === "five_prime_UTR") {
        fivePrimeUTR =
          (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
      } else if (columns[2] === "three_prime_UTR") {
        threePrimeUTR =
          (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
      }
    }
  }

  return {
    totalLength,
    exonPositions: exonPos,
    fivePrimeUTR,
    threePrimeUTR,
  };
}

/**
 * ブラウザ環境でGFFファイルを読み込み、トランスクリプトの構造情報を取得する
 * @param file ブラウザのFileオブジェクト（GFFファイル）
 * @param transcriptId 対象のトランスクリプトID
 * @returns 構造情報を含むPromise
 */
export async function getStructureFromFile(
  file: File,
  transcriptId: string,
): Promise<TranscriptStructure> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (!event.target || typeof event.target.result !== "string") {
        reject(new Error("ファイルの読み込みに失敗しました"));
        return;
      }

      try {
        const fileContent = event.target.result;
        const result = getStructure(fileContent, transcriptId);
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

/**
 * GFFファイルからトランスクリプトIDを取得する
 * @param fileContent GFFファイルの内容（テキスト形式）
 * @param geneId 対象の遺伝子ID
 * @returns トランスクリプト情報、見つからない場合はtranscriptIdとstrandが空文字
 */
export function getTranscriptIds(
  fileContent: string,
  geneId: string,
): TranscriptInfo[] {
  const transcriptInfos: TranscriptInfo[] = [];

  // ファイル内容を行ごとに分割
  const lines = fileContent.split(/\r?\n/);

  for (const line of lines) {
    if (line.startsWith("#")) {
      continue;
    }

    if (line.trim() === "") {
      continue;
    }

    const columns = line.split("\t");
    if (columns.length < 9) continue; // 必要なカラム数がない場合はスキップ
    if (columns[2] !== "mRNA") continue;

    const idMatch = columns[8].match(/ID=([^;]+)/);
    if (columns[8].includes(geneId) && idMatch) {
      const transcriptId = idMatch[1];
      const strand = columns[6];
      transcriptInfos.push({ transcriptId, strand });
    }
  }

  return transcriptInfos;
}

/**
 * ブラウザ環境でGFFファイルを読み込み、トランスクリプトIDを取得する
 * @param file ブラウザのFileオブジェクト（GFFファイル）
 * @param geneId 対象の遺伝子ID
 * @returns トランスクリプトIDとストランドを含むPromise
 */
export async function getTranscriptIdFromFile(
  file: File,
  geneId: string,
): Promise<TranscriptInfo> {
  // GFF3ファイル以外はエラー
  if (!file.name.endsWith(".gff3")) {
    throw new Error(
      "無効なファイル形式です。.gff3ファイルのみ対応しています。",
    );
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (!event.target || typeof event.target.result !== "string") {
        reject(new Error("ファイルの読み込みに失敗しました"));
        return;
      }

      try {
        const fileContent = event.target.result;
        const result = getTranscriptIds(fileContent, geneId);

        if (result.length === 0) {
          reject(new Error(`遺伝子ID "${geneId}" が見つかりませんでした。`));
          return;
        }

        resolve(result[0]);
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

export async function parseGff(file: File): Promise<GeneStructureInfo[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (!event.target || typeof event.target.result !== "string") {
        reject(new Error("ファイルの読み込みに失敗しました"));
        return;
      }

      try {
        const fileContent = event.target.result;
        const lines = fileContent.split(/\r?\n/);
        const geneStructures: GeneStructureInfo[] = [];

        let currentGeneId = "";
        let currentTranscriptId = "";
        let currentStrand = "";
        let exonPositions: number[] = [];
        let fivePrimeUTR = 0;
        let threePrimeUTR = 0;
        let totalLength = 0;

        for (const line of lines) {
          if (line.startsWith("#") || line.trim() === "") {
            continue;
          }

          const columns = line.split("\t");
          if (columns.length < 9) continue;

          const idCol = columns[8].split(/[:;]/);

          if (columns[2] === "gene") {
            if (currentGeneId) {
              geneStructures.push({
                gene_id: currentGeneId,
                transcript_id: currentTranscriptId,
                strand: currentStrand,
                total_length: totalLength,
                exon_positions: exonPositions,
                five_prime_utr: fivePrimeUTR,
                three_prime_utr: threePrimeUTR,
              });
            }
            currentGeneId = idCol[1];
            exonPositions = [];
            fivePrimeUTR = 0;
            threePrimeUTR = 0;
            totalLength = 0;
          } else if (columns[2] === "mRNA") {
            currentTranscriptId = idCol[1];
            currentStrand = columns[6];
            totalLength =
              (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
          } else if (columns[2] === "exon") {
            exonPositions.push(Number.parseInt(columns[3]));
            exonPositions.push(Number.parseInt(columns[4]));
          } else if (columns[2] === "five_prime_UTR") {
            fivePrimeUTR =
              (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
          } else if (columns[2] === "three_prime_UTR") {
            threePrimeUTR =
              (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
          }
        }

        if (currentGeneId) {
          geneStructures.push({
            gene_id: currentGeneId,
            transcript_id: currentTranscriptId,
            strand: currentStrand,
            total_length: totalLength,
            exon_positions: exonPositions,
            five_prime_utr: fivePrimeUTR,
            three_prime_utr: threePrimeUTR,
          });
        }

        resolve(geneStructures);
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
