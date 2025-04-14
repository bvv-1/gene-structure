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

    const idCol = columns[8].split(/[:;]/);

    if (idCol[1] === transcriptId) {
      if (columns[2] === "mRNA") {
        totalLength =
          (Number.parseInt(columns[4]) - Number.parseInt(columns[3])) / 10;
      } else if (columns[2] === "exon") {
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
export function getTranscriptId(
  fileContent: string,
  geneId: string,
): TranscriptInfo {
  let transcriptId = "";
  let strand = "";

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

    const idCol = columns[8].split(/[:;]/);

    if (idCol.length < 4) continue;
    if (idCol[3] === geneId) {
      transcriptId = idCol[1];
      strand = columns[6];
      break; // 見つかったら終了
    }
  }

  return { transcriptId, strand };
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
        const result = getTranscriptId(fileContent, geneId);

        if (result.transcriptId === "") {
          reject(new Error(`遺伝子ID "${geneId}" が見つかりませんでした。`));
          return;
        }

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
