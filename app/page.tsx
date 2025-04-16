"use client";

import { useRef, useState } from "react";
import useSWR from "swr";
import Fuse from "fuse.js";

import {
  parseGff,
  getmRNAs,
  getGeneStructureInfo,
  type GeneStructureInfo,
} from "./utils/gff";

type UIState = "upload" | "preview";

type GeneStructureRequest = {
  mode: string;
  utr_color: string;
  exon_color: string;
  line_color: string;
  file_name: string;
  gene_structure: GeneStructureInfo;
};

type ExportSettings = {
  format: "svg" | "png";
  dpi: number;
  background: "transparent" | "white";
  filename: string;
};

const postFetcher = async (url: string, data: GeneStructureRequest | null) => {
  if (!data) {
    throw new Error("No data provided");
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
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
  const [uiState, setUiState] = useState<UIState>("upload");
  const [isLoading, setIsLoading] = useState(false);
  const [geneId, setGeneId] = useState("SORBI_3007G204600");
  const [utrColor, setUtrColor] = useState("#d3d3d3");
  const [exonColor, setExonColor] = useState("#000000");
  const [lineColor, setLineColor] = useState("#000000");
  // カラー変更時のデバウンス用
  const [tempUtrColor, setTempUtrColor] = useState(utrColor);
  const [tempExonColor, setTempExonColor] = useState(exonColor);
  const [tempLineColor, setTempLineColor] = useState(lineColor);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [width, setWidth] = useState(1200);
  const [geneStructures, setGeneStructures] = useState<GeneStructureInfo[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    format: "svg",
    dpi: 300,
    background: "white",
    filename: "gene_structure",
  });

  const fuse = new Fuse(geneStructures, {
    includeScore: true,
    threshold: 0.2,
  });

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      // setIsLoading(true);
      // try {
      //   const gffData = await parseGff(e.target.files[0]);
      //   setParsedGff(gffData);
      // } catch (error) {
      //   alert(`Error parsing GFF file: ${error}`);
      // } finally {
      //   setIsLoading(false);
      // }
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setIsLoading(true);
      try {
        const gffData = await parseGff(e.dataTransfer.files[0]);
        const mRNAs = getmRNAs(gffData);
        const geneStructureInfo = getGeneStructureInfo(mRNAs);
        setGeneStructures(geneStructureInfo);
      } catch (error) {
        alert(`Error parsing GFF file: ${error}`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // ファイル処理関数（アップロード→解析）
  const handleFileProcess = async () => {
    if (!selectedFile) {
      alert("Select a GFF file");
      return;
    }

    try {
      setIsLoading(true);

      // 処理完了後、UI状態を生成画面に変更
      setUiState("preview");
      await handleGenerateSVG(geneStructures[0]);
    } catch (error) {
      console.error("Error processing file:", error);
      alert(
        `An error occurred while processing the file: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getRequestData = (): GeneStructureRequest | null => {
    if (geneStructures.length === 0) return null;

    console.log(geneStructures[0]);
    return {
      mode: "basic",
      utr_color: utrColor,
      exon_color: exonColor,
      line_color: lineColor,
      file_name: selectedFile?.name ?? "gene_structure",
      gene_structure: geneStructures[0],
    };
  };

  const { data: svgData, mutate: mutateSVG } = useSWR(
    ["/api/py/generate-gene-structure-svg", getRequestData()],
    geneStructures
      ? () =>
          postFetcher("/api/py/generate-gene-structure-svg", getRequestData())
      : null,
    {
      onSuccess: (data) => {
        renderSvgToCanvas(data.url);
      },
    },
  );

  const handleGenerateSVG = async (structure: GeneStructureInfo | null) => {
    if (!structure) {
      alert("Please process the file first");
      setUiState("upload");
      return;
    }

    try {
      setIsLoading(true);
      // SWRのキャッシュを更新して再フェッチをトリガー
      await mutateSVG();
    } catch (error) {
      console.error("Error generating SVG:", error);
      alert("An error occurred while generating the SVG.");
    } finally {
      setIsLoading(false);
    }
  };

  // SVGをCanvas要素に描画する関数を修正
  const renderSvgToCanvas = (svgUrl: string) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
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

  // アップロード画面に戻る関数を拡張
  const handleResetUpload = () => {
    // 既存のURLがあれば解放
    if (svgData) {
      window.URL.revokeObjectURL(svgData.url);
    }
    setGeneStructures([]);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setUiState("upload");
  };

  // ダウンロードハンドラーを修正
  const handleDownload = async () => {
    if (!svgData) return;

    let finalUrl = svgData.url;
    const finalFilename = `${exportSettings.filename}.${exportSettings.format}`;

    if (exportSettings.format === "png") {
      // PNGの場合はcanvasを使用して変換
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const img = new Image();

      await new Promise((resolve) => {
        img.onload = () => {
          // DPIに応じてキャンバスサイズを設定
          const scale = exportSettings.dpi / 96; // 96はデフォルトのDPI
          canvas.width = img.width * scale;
          canvas.height = img.height * scale;

          if (ctx) {
            if (exportSettings.background === "white") {
              ctx.fillStyle = "white";
              ctx.fillRect(0, 0, canvas.width, canvas.height);
            }

            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          }
          resolve(true);
        };
        img.src = svgData.url;
      });

      finalUrl = canvas.toDataURL("image/png");
    }

    const a = document.createElement("a");
    a.href = finalUrl;
    a.download = finalFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setShowExportDialog(false);
  };

  return (
    <div className="flex-1 flex flex-col">
      {uiState === "upload" && (
        <>
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-black mb-4">Upload File</h2>
            <p className="text-black">
              Upload a GFF3 file containing gene feature data.
            </p>
          </div>

          <div className="flex flex-row gap-4">
            <div className="card p-6 mb-8 bg-white rounded-lg shadow-md flex-1">
              <h3 className="text-xl font-semibold text-black mb-4">
                Upload File
              </h3>
              <div
                className={`file-upload mb-4 ${dragActive ? "border-blue-500 bg-blue-50" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <i className="bx bx-cloud-upload text-5xl text-blue-500 mb-4" />
                <p className="text-black mb-2">
                  Drag and drop a GFF3 file here
                </p>
                <p className="text-sm text-black mb-4">or</p>
                <label className="btn-primary cursor-pointer">
                  <span>Select a file</span>
                  <input
                    type="file"
                    className="hidden"
                    accept=".gff,.gff3"
                    onChange={handleFileChange}
                    ref={fileInputRef}
                  />
                </label>
                {selectedFile && (
                  <p className="mt-4 text-black">
                    Selected file: {selectedFile.name}
                  </p>
                )}
              </div>
              <div className="text-black">
                <h4 className="font-medium mb-2">Example GFF3 Format:</h4>
                <pre className="bg-gray-100 p-3 rounded-lg text-xs overflow-auto">
                  ##gff-version 3<br />
                  Chr1 TAIR10 gene 3631 5899 . + . ID=AT1G01010;Name=AT1G01010
                  <br />
                  Chr1 TAIR10 mRNA 3631 5899 . + .
                  ID=AT1G01010.1;Parent=AT1G01010
                  <br />
                  Chr1 TAIR10 exon 3631 3913 . + . Parent=AT1G01010.1
                  <br />
                  Chr1 TAIR10 exon 3996 4276 . + . Parent=AT1G01010.1
                </pre>
              </div>
            </div>

            <div className="card p-6 mb-8 bg-white rounded-lg shadow-md">
              <h3 className="text-xl font-semibold text-black mb-4">
                Select Gene ID
              </h3>

              <input
                type="text"
                className="w-full border border-gray-300 rounded-lg px-4 py-2"
                placeholder="Enter gene ID"
                value={geneId}
                onChange={(e) => setGeneId(e.target.value)}
              />

              {/* 選ばれたgene id */}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              className={`btn-primary flex items-center ${isLoading || !selectedFile ? "opacity-50 cursor-not-allowed" : ""}`}
              onClick={handleFileProcess}
              disabled={isLoading || !selectedFile}
            >
              {isLoading ? "Processing..." : "Generate Visualization"}
              <i className="bx bx-right-arrow-alt ml-2" />
            </button>
          </div>
        </>
      )}

      {/* プレビューページを追加 */}
      {uiState === "preview" && (
        <>
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-black mb-4">Preview</h2>
            <p className="text-black">
              You can preview the gene structure diagram generated from the
              uploaded data.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-8 mb-8">
            <div className="col-span-2">
              <div className="card p-6 flex items-center justify-center h-full">
                <div className="w-full bg-white border border-gray-200 rounded-lg flex items-center justify-center">
                  <canvas ref={canvasRef} className="w-full" />
                </div>
              </div>
            </div>

            <div>
              <div className="card p-6 mb-6">
                <h3 className="text-xl font-semibold text-black mb-4">
                  Basic Settings
                </h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="width" className="block text-black mb-2">
                      Width (px)
                    </label>
                    <input
                      id="width"
                      type="number"
                      className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      value={width}
                      onChange={(e) =>
                        setWidth(Number.parseInt(e.target.value))
                      }
                    />
                  </div>
                  <div>
                    <p className="block text-black mb-2">
                      Gene Feature Color Settings
                    </p>
                    <div className="grid grid-cols-3 gap-2 mb-2">
                      <div>
                        <label
                          htmlFor="utr-color"
                          className="block text-xs text-black mb-1"
                        >
                          UTR
                        </label>
                        <input
                          id="utr-color"
                          type="color"
                          value={utrColor}
                          onChange={(e) => setTempUtrColor(e.target.value)}
                          onBlur={() => setUtrColor(tempUtrColor)}
                          className="w-full h-8 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                        />
                      </div>
                      <div>
                        <label
                          htmlFor="exon-color"
                          className="block text-xs text-black mb-1"
                        >
                          Exon
                        </label>
                        <input
                          type="color"
                          value={exonColor}
                          onChange={(e) => setTempExonColor(e.target.value)}
                          onBlur={() => setExonColor(tempExonColor)}
                          className="w-full h-8 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                        />
                      </div>
                      <div>
                        <label
                          htmlFor="line-color"
                          className="block text-xs text-black mb-1"
                        >
                          Line
                        </label>
                        <input
                          type="color"
                          value={lineColor}
                          onChange={(e) => setTempLineColor(e.target.value)}
                          onBlur={() => setLineColor(tempLineColor)}
                          className="w-full h-8 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-xl font-semibold text-black mb-4">
                  Actions
                </h3>
                <div className="flex flex-col space-y-3">
                  <button
                    type="button"
                    className="btn-primary flex items-center justify-center"
                    onClick={() => handleGenerateSVG(geneStructures[0])}
                    disabled={isLoading}
                  >
                    <i className="bx bx-edit text-xl mr-2" />
                    <span>{isLoading ? "Processing..." : "Regenerate"}</span>
                  </button>
                  <button
                    type="button"
                    className="border border-blue-500 text-blue-500 hover:bg-blue-50 rounded-lg py-2 px-4 transition-colors flex items-center justify-center"
                    onClick={handleResetUpload}
                    disabled={isLoading}
                  >
                    <i className="bx bx-refresh text-xl mr-2" />
                    <span>Back to Upload</span>
                  </button>
                  <button
                    type="button"
                    className="border border-blue-500 text-blue-500 hover:bg-blue-50 rounded-lg py-2 px-4 transition-colors flex items-center justify-center"
                    onClick={() => setShowExportDialog(true)}
                    disabled={isLoading || !svgData}
                  >
                    <i className="bx bx-download text-xl mr-2" />
                    <span>Export</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Export dialog */}
      {showExportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-xl font-semibold mb-4">Export Settings</h3>

            <div className="space-y-4">
              <div>
                <label
                  htmlFor="filename"
                  className="block text-sm font-medium mb-1"
                >
                  File Name
                </label>
                <input
                  id="filename"
                  type="text"
                  className="w-full border rounded px-3 py-2"
                  value={exportSettings.filename}
                  onChange={(e) =>
                    setExportSettings({
                      ...exportSettings,
                      filename: e.target.value,
                    })
                  }
                />
              </div>

              <div>
                <label
                  htmlFor="format"
                  className="block text-sm font-medium mb-1"
                >
                  File Format
                </label>
                <select
                  id="format"
                  className="w-full border rounded px-3 py-2"
                  value={exportSettings.format}
                  onChange={(e) =>
                    setExportSettings({
                      ...exportSettings,
                      format: e.target.value as "svg" | "png",
                    })
                  }
                >
                  <option value="svg">SVG</option>
                  <option value="png">PNG</option>
                </select>
              </div>

              {exportSettings.format === "png" && (
                <>
                  <div>
                    <label
                      htmlFor="dpi"
                      className="block text-sm font-medium mb-1"
                    >
                      DPI
                    </label>
                    <select
                      className="w-full border rounded px-3 py-2"
                      value={exportSettings.dpi}
                      onChange={(e) =>
                        setExportSettings({
                          ...exportSettings,
                          dpi: Number(e.target.value),
                        })
                      }
                    >
                      <option value="72">72 DPI</option>
                      <option value="150">150 DPI</option>
                      <option value="300">300 DPI</option>
                      <option value="600">600 DPI</option>
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="background"
                      className="block text-sm font-medium mb-1"
                    >
                      Background
                    </label>
                    <select
                      id="background"
                      className="w-full border rounded px-3 py-2"
                      value={exportSettings.background}
                      onChange={(e) =>
                        setExportSettings({
                          ...exportSettings,
                          background: e.target.value as "transparent" | "white",
                        })
                      }
                    >
                      <option value="transparent">Transparent</option>
                      <option value="white">White</option>
                    </select>
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                className="border border-blue-500 text-blue-500 hover:bg-blue-50 rounded-lg py-2 px-4 transition-colors flex items-center justify-center"
                onClick={() => setShowExportDialog(false)}
              >
                <span>Cancel</span>
              </button>
              <button
                type="button"
                className="btn-primary flex items-center justify-center"
                onClick={handleDownload}
                disabled={isLoading}
              >
                <i className="bx bx-download text-xl mr-2" />
                <span>{isLoading ? "Processing..." : "Download"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
