'use client'

import { useState, useRef } from "react";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [geneId, setGeneId] = useState("SORBI_3007G204600");
  const [utrColor, setUtrColor] = useState("#d3d3d3");
  const [exonColor, setExonColor] = useState("#000000");
  const [lineColor, setLineColor] = useState("#000000");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleGeneratePDF = async () => {
    if (!selectedFile) {
      alert('GFFファイルを選択してください');
      return;
    }

    try {
      setIsLoading(true);
      
      // FormDataを作成
      const formData = new FormData();
      
      // ファイルを追加
      formData.append('gff_file', selectedFile);
      
      // その他のパラメータをJSONとして追加
      const requestData = {
        gene_id: geneId,
        mode: "basic",
        utr_color: utrColor,
        exon_color: exonColor,
        line_color: lineColor,
      };
      
      formData.append('request', JSON.stringify(requestData));
      
      // APIエンドポイントを呼び出す
      const response = await fetch('/api/py/generate-gene-structure', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      // レスポンスをBlobとして取得
      const blob = await response.blob();
      
      // Blobをダウンロード可能なURLに変換
      const url = window.URL.createObjectURL(blob);
      
      // リンク要素を作成してクリック（ダウンロード開始）
      const a = document.createElement('a');
      a.href = url;
      a.download = 'gene_structure.pdf';
      document.body.appendChild(a);
      a.click();
      
      // クリーンアップ
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error calling API:', error);
      alert('APIの呼び出し中にエラーが発生しました。');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-3xl font-bold mb-6 text-center">遺伝子構造可視化ツール</h1>

        <div className="flex flex-col items-center justify-center p-8 bg-gray-100 dark:bg-gray-800 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">遺伝子構造PDFの生成</h2>
          
          <div className="w-full max-w-md space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                GFFファイル
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
                  選択したファイル: {selectedFile.name}
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                遺伝子ID
              </label>
              <input
                type="text"
                value={geneId}
                onChange={(e) => setGeneId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  UTR色
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
                  エクソン色
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
                  ライン色
                </label>
                <input
                  type="color"
                  value={lineColor}
                  onChange={(e) => setLineColor(e.target.value)}
                  className="w-full h-10 border border-gray-300 rounded-md shadow-sm cursor-pointer"
                />
              </div>
            </div>
          </div>
          
          <button
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={handleGeneratePDF}
            disabled={isLoading}
          >
            {isLoading ? '処理中...' : '遺伝子構造PDFを生成'}
          </button>
        </div>
        
        <div className="mt-8 text-sm text-gray-500 dark:text-gray-400 text-center">
          <p>© 2025 geneSTRUCTURE</p>
        </div>
      </div>
    </main>
  );
}
