"use client";

import { useRef, useState } from "react";
import useSWR from 'swr'

import { getStructureFromFile, getTranscriptIdFromFile } from "./utils/gff";

// UIの状態を表す型
type UIState = "upload" | "generate";

// 遺伝子構造情報の型を定義
type GeneStructureInfo = {
  transcript_id: string;
  strand: string;
  total_length: number;
  exon_positions: number[];
  five_prime_utr: number;
  three_prime_utr: number;
};

// APIリクエストの型定義を追加
type GeneStructureRequest = {
  mode: string;
  utr_color: string;
  exon_color: string;
  line_color: string;
  file_name: string;
  gene_structure: GeneStructureInfo;
};

const postFetcher = async (url: string, data: GeneStructureRequest) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const blob = await response.blob();
  return { blob, url: window.URL.createObjectURL(blob) };
};

export default function Home() {
  // UIの状態管理用state
  const [uiState, setUiState] = useState<UIState>("upload");
  const [isLoading, setIsLoading] = useState(false);
  const [geneId, setGeneId] = useState("SORBI_3007G204600");
  const [utrColor, setUtrColor] = useState("#d3d3d3");
  const [exonColor, setExonColor] = useState("#000000");
  const [lineColor, setLineColor] = useState("#000000");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // Blobの代わりに構造情報を保持するstateを追加
  const [geneStructure, setGeneStructure] = useState<GeneStructureInfo | null>(
    null,
  );
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [svgPreview, setSvgPreview] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // ファイル処理関数（アップロード→解析）
  const handleFileProcess = async () => {
    if (!selectedFile) {
      alert("GFFファイルを選択してください");
      return;
    }

    try {
      setIsLoading(true);

      // 遺伝子IDからトランスクリプトIDとストランドを取得
      const { transcriptId, strand } = await getTranscriptIdFromFile(
        selectedFile,
        geneId,
      );

      if (!transcriptId) {
        throw new Error(
          `指定された遺伝子ID "${geneId}" が見つかりませんでした。`,
        );
      }

      // トランスクリプトの構造情報を取得
      const { totalLength, exonPositions, fivePrimeUTR, threePrimeUTR } =
        await getStructureFromFile(selectedFile, transcriptId);

      // 構造情報をstateに保存
      const structure = {
        transcript_id: transcriptId,
        strand,
        total_length: totalLength,
        exon_positions: exonPositions,
        five_prime_utr: fivePrimeUTR,
        three_prime_utr: threePrimeUTR,
      }
      setGeneStructure(structure);

      // 処理完了後、UI状態を生成画面に変更
      setUiState("generate");
      await handleGenerateSVG(structure);
    } catch (error) {
      console.error("Error processing file:", error);
      alert(
        `ファイルの処理中にエラーが発生しました: ${error instanceof Error ? error.message : "不明なエラー"}`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  // ダウンロード用の共通関数を追加
  const downloadFile = (url: string, filename: string) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const getRequestData = (): GeneStructureRequest | null => {
    if (!geneStructure) return null;
    
    return {
      mode: "basic",
      utr_color: utrColor,
      exon_color: exonColor,
      line_color: lineColor,
      file_name: selectedFile?.name ?? "gene_structure",
      gene_structure: {
        transcript_id: geneStructure.transcript_id,
        strand: geneStructure.strand,
        total_length: geneStructure.total_length,
        exon_positions: geneStructure.exon_positions,
        five_prime_utr: geneStructure.five_prime_utr,
        three_prime_utr: geneStructure.three_prime_utr,
      },
    };
  };

  // useSWRの設定を修正
  const { data: svgData, mutate: mutateSVG } = useSWR(
    geneStructure ? ['/api/py/generate-gene-structure-svg', getRequestData(), utrColor, exonColor, lineColor] : null,
    ([url, data]) => postFetcher(url, data as GeneStructureRequest),
  );

  // SVG生成関数を修正
  const handleGenerateSVG = async (structure: GeneStructureInfo | null) => {
    if (!structure) {
      alert("まずファイルを処理してください");
      setUiState("upload");
      return;
    }

    try {
      setIsLoading(true);
      // SWRのキャッシュを更新して再フェッチをトリガー
      await mutateSVG();

      if (svgData) {
        setDownloadUrl(svgData.url);
        const svgText = await svgData.blob.text();
        setSvgPreview(svgText);
        renderSvgToCanvas(svgData.url);
      }
    } catch (error) {
      console.error("Error generating SVG:", error);
      alert("SVG生成中にエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  };

  // SVGをCanvas要素に描画する関数を修正
  const renderSvgToCanvas = (svgUrl: string) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // 画像オブジェクトを作成
    const img = new Image();
    img.onload = () => {
      // キャンバスのサイズを設定
      canvas.width = img.width;
      canvas.height = img.height;
      
      // SVGをキャンバスに描画
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
    };
    
    // 画像のソースにSVGのURLを設定
    img.src = svgUrl;
  };

  // アップロード画面に戻る関数を修正
  const handleResetUpload = () => {
    // 既存のURLがあれば解放
    if (downloadUrl) {
      window.URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }
    setGeneStructure(null);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setUiState("upload");
  };

  // ダウンロードハンドラーを修正
  const handleDownload = () => {
    if (downloadUrl) {
      downloadFile(downloadUrl, "gene_structure.svg");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-3xl font-bold mb-6 text-center">
          Gene Structure Visualizer
        </h1>

        <div className="flex flex-col items-center justify-center p-8 bg-gray-100 dark:bg-gray-800 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">
            {uiState === "upload"
              ? "Upload GFF file"
              : "Generate Gene Structure PDF"}
          </h2>

          {uiState === "upload" && (
            <div className="w-full max-w-md space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Gene ID
                </label>
                <input
                  type="text"
                  value={geneId}
                  onChange={(e) => setGeneId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  GFF file
                </label>
                <input
                  type="file"
                  accept=".gff3"
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                {selectedFile && (
                  <p className="mt-1 text-sm text-gray-500">
                    Selected file: {selectedFile.name}
                  </p>
                )}
              </div>

              <div className="flex justify-center mt-4">
                <button
                  className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300 ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                  onClick={handleFileProcess}
                  disabled={isLoading || !selectedFile}
                >
                  {isLoading ? "Processing..." : "Process file"}
                </button>
              </div>
            </div>
          )}

          {uiState === "generate" && (
            <div className="w-full max-w-md space-y-4 mb-6">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    UTR Color
                  </label>
                  <input
                    type="color"
                    value={utrColor}
                    onChange={(e) => setUtrColor(e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Exon Color
                  </label>
                  <input
                    type="color"
                    value={exonColor}
                    onChange={(e) => setExonColor(e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Line Color
                  </label>
                  <input
                    type="color"
                    value={lineColor}
                    onChange={(e) => setLineColor(e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                  />
                </div>
              </div>

              <div className="flex flex-col space-y-3 mt-4">
                <div className="flex space-x-4 justify-center">
                  <button
                    className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300"
                    onClick={handleResetUpload}
                    disabled={isLoading}
                  >
                    Back
                  </button>

                  {/* <button
                    className={`bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300 ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                    onClick={handleGeneratePDF}
                    disabled={isLoading}
                  >
                    {isLoading ? "処理中..." : "PDFを生成"}
                  </button> */}

                  <button
                    className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300 ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                    onClick={() => handleGenerateSVG(geneStructure)}
                    disabled={isLoading}
                  >
                    {isLoading ? "Processing..." : "Generate SVG"}
                  </button>

                  {/* ダウンロードボタン */}
                  <button
                    className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300"
                    onClick={handleDownload}
                    disabled={isLoading || !downloadUrl}
                  >
                    Download
                  </button>
                </div>
              </div>

              {/* SVGプレビュー表示用のセクション */}
              {svgPreview && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium mb-2">Gene Structure Preview</h3>
                  <div className="border border-gray-300 rounded-md p-2 bg-white">
                    <canvas
                      ref={canvasRef}
                      className="w-full"
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-8 text-sm text-gray-500 dark:text-gray-400 text-center">
          <p>© 2025 geneSTRUCTURE</p>
        </div>
      </div>
    </main>
  );
}
