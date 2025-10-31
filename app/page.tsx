"use client";

import {
  Autocomplete,
  Badge,
  Button,
  Card,
  Code,
  ColorInput,
  Grid,
  Group,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";
import {
  IconArrowRight,
  IconCloudUpload,
  IconDownload,
  IconPlayerPlay,
  IconRefresh,
  IconX,
} from "@tabler/icons-react";
import Fuse from "fuse.js";
import { useMemo, useRef, useState } from "react";
import useSWR from "swr";

import SvgViewer from "./components/SvgViewer";
import {
  type GeneStructureInfo,
  getGeneStructureInfo,
  getmRNAs,
  parseGff,
} from "./utils/gff";

type UIState = "upload" | "preview";

type DrawSettings = {
  mode: "domain" | "gene";
  utr_color: string;
  exon_color: string;
  line_color: string;
  intron_shape: "straight" | "zigzag";
  gene_height?: number;
  margin_x?: number;
  margin_y?: number;
};

type GeneStructureRequest = {
  draw_settings: DrawSettings;
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
  const [input, setInput] = useState("");
  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);
  const [utrColor, setUtrColor] = useState("#d3d3d3");
  const [exonColor, setExonColor] = useState("#000000");
  const [lineColor, setLineColor] = useState("#000000");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [width, setWidth] = useState(1200);
  const [geneStructures, setGeneStructures] = useState<GeneStructureInfo[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    format: "svg",
    dpi: 300,
    background: "white",
    filename: "gene_structure",
  });

  const fuseInstance = useMemo(() => {
    const fuse = new Fuse(geneStructures, {
      keys: ["transcript_id", "attributes.Parent"],
      threshold: 0.5,
    });
    return fuse;
  }, [geneStructures]);

  const autocompleteData = useMemo(() => {
    if (!input) {
      return geneStructures
        .filter((gs) => !selectedTranscripts.includes(gs.transcript_id))
        .slice(0, 20)
        .map((gs) => gs.transcript_id);
    }

    const searchResults = fuseInstance.search(input);
    return searchResults
      .filter(
        (result) => !selectedTranscripts.includes(result.item.transcript_id),
      )
      .slice(0, 20)
      .map((result) => result.item.transcript_id);
  }, [geneStructures, selectedTranscripts, input, fuseInstance]);

  // ファイル処理関数（アップロード→解析）
  const handleFileProcess = async () => {
    if (!selectedFile) {
      alert("Select a GFF file");
      return;
    }
    if (selectedTranscripts.length === 0) {
      alert("Select at least one gene/transcript");
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

    return {
      draw_settings: {
        mode: "domain",
        utr_color: utrColor,
        exon_color: exonColor,
        line_color: lineColor,
        intron_shape: "straight",
      },
      gene_structure: geneStructures.filter((gs) =>
        selectedTranscripts.includes(gs.transcript_id),
      )[0],
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
    // setGeneStructures([]);
    setSelectedTranscripts([]);
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
        <Stack>
          <Title order={2} mb="md">
            Upload
          </Title>

          <Stack mb="8" gap="md">
            <Grid gutter="md">
              <Grid.Col span={6}>
                <Card
                  shadow="xl"
                  padding="lg"
                  radius="md"
                  className="mb-8"
                  h="100%"
                >
                  <Title order={3} mb="md">
                    Upload File
                  </Title>

                  <Stack>
                    <Dropzone
                      style={{
                        border: "2px dashed #D9D9D9",
                        borderRadius: "8px",
                        cursor: "pointer",
                      }}
                      onDrop={async (files) => {
                        if (files.length > 0) {
                          setSelectedFile(files[0]);
                          setIsLoading(true);
                          try {
                            const gffData = await parseGff(files[0]);
                            const mRNAs = getmRNAs(gffData);
                            const geneStructureInfo =
                              getGeneStructureInfo(mRNAs);
                            setGeneStructures(geneStructureInfo);
                          } catch (error) {
                            alert(`Error parsing GFF file: ${error}`);
                          } finally {
                            setIsLoading(false);
                          }
                        }
                      }}
                      accept={{
                        "text/plain": [".gff", ".gff3"],
                      }}
                      maxFiles={1}
                      loading={isLoading}
                    >
                      <Group
                        justify="center"
                        align="center"
                        gap="xl"
                        style={{
                          minHeight: 220,
                          pointerEvents: "none",
                          textAlign: "center",
                        }}
                      >
                        <Stack align="center" gap="md">
                          <Dropzone.Accept>
                            <IconCloudUpload size={80} color="#AAA" />
                          </Dropzone.Accept>
                          <Dropzone.Reject>
                            <IconX size={80} color="#AAA" />
                          </Dropzone.Reject>
                          <Dropzone.Idle>
                            <IconCloudUpload size={80} color="#AAA" />
                          </Dropzone.Idle>
                          <Text size="md" c="dimmed">
                            Drag and drop a GFF3 file here
                            <br />
                            or click to select a file
                          </Text>
                          {selectedFile && (
                            <Text size="sm" mt="md">
                              Selected file: {selectedFile.name}
                            </Text>
                          )}
                        </Stack>
                      </Group>
                    </Dropzone>

                    <div className="mt-4">
                      <Text fw={500} mb="xs">
                        Example GFF3 Format:
                      </Text>
                      <Code block p="md">
                        {`##gff-version 3
Chr1 TAIR10 gene 3631 5899 . + . ID=AT1G01010;Name=AT1G01010
Chr1 TAIR10 mRNA 3631 5899 . + . ID=AT1G01010.1;Parent=AT1G01010
Chr1 TAIR10 exon 3631 3913 . + . Parent=AT1G01010.1
Chr1 TAIR10 exon 3996 4276 . + . Parent=AT1G01010.1`}
                      </Code>
                    </div>
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card
                  shadow="xl"
                  padding="lg"
                  radius="md"
                  className="mb-8"
                  h="100%"
                >
                  <Title order={3} mb="md">
                    Search Genes/Transcripts
                  </Title>

                  <Stack>
                    <Autocomplete
                      label=""
                      placeholder="Select gene ID/transcript ID"
                      disabled={!geneStructures.length}
                      value={input}
                      onChange={setInput}
                      data={autocompleteData}
                      onOptionSubmit={(value) => {
                        if (!selectedTranscripts.includes(value)) {
                          setSelectedTranscripts([
                            ...selectedTranscripts,
                            value,
                          ]);
                          setInput("");
                        }
                      }}
                    />

                    {selectedTranscripts.length > 0 && (
                      <>
                        <Text size="sm" fw={500} mb="xs">
                          Selected Transcripts:
                        </Text>
                        <Stack gap="xs">
                          {selectedTranscripts.map((transcript) => (
                            <Badge
                              key={transcript}
                              size="lg"
                              style={{ textTransform: "none" }}
                              rightSection={
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedTranscripts(
                                      selectedTranscripts.filter(
                                        (t) => t !== transcript,
                                      ),
                                    );
                                  }}
                                  style={{
                                    border: "none",
                                    background: "transparent",
                                    cursor: "pointer",
                                    padding: 0,
                                    marginLeft: 4,
                                    color: "white",
                                    fontSize: 20,
                                  }}
                                >
                                  ×
                                </button>
                              }
                            >
                              {transcript}
                            </Badge>
                          ))}
                        </Stack>
                      </>
                    )}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>

            <Stack align="flex-end" mb="8">
              <Button
                onClick={handleFileProcess}
                disabled={isLoading || !selectedFile}
                loading={isLoading}
                rightSection={<IconArrowRight size={16} />}
              >
                Generate Preview
              </Button>
            </Stack>
          </Stack>
        </Stack>
      )}

      {/* プレビューページを追加 */}
      {uiState === "preview" && (
        <Stack>
          <Title order={2} mb="md">
            Preview
          </Title>

          <Grid gutter="md" mb="8">
            <Grid.Col span={8}>
              <Card shadow="xl" radius="md">
                <SvgViewer svgUrl={svgData?.url} />
              </Card>
            </Grid.Col>

            <Grid.Col span={4}>
              <Stack gap="md">
                <Card shadow="xl" padding="lg" radius="md">
                  <Title order={3} mb="md">
                    Actions
                  </Title>
                  <Stack gap="md">
                    <Button
                      onClick={() => handleGenerateSVG(geneStructures[0])}
                      disabled={isLoading}
                      loading={isLoading}
                      leftSection={<IconPlayerPlay size={16} />}
                      fullWidth
                    >
                      Regenerate
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleResetUpload}
                      disabled={isLoading}
                      leftSection={<IconRefresh size={16} />}
                      fullWidth
                    >
                      Back to Upload
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowExportDialog(true)}
                      disabled={isLoading || !svgData}
                      leftSection={<IconDownload size={16} />}
                      fullWidth
                    >
                      Export
                    </Button>
                  </Stack>
                </Card>

                <Card shadow="xl" padding="lg" radius="md">
                  <Title order={3} mb="md">
                    Basic Settings
                  </Title>
                  <Stack gap="xs">
                    <Text size="sm" fw={500} mb="xs">
                      Color Settings:
                    </Text>
                    <Grid>
                      <Grid.Col span={4}>
                        <ColorInput
                          label="UTRs"
                          value={utrColor}
                          onChange={setUtrColor}
                          format="hex"
                          withEyeDropper={false}
                          styles={{
                            swatch: {
                              display: "none",
                            },
                          }}
                        />
                      </Grid.Col>
                      <Grid.Col span={4}>
                        <ColorInput
                          label="Exons"
                          value={exonColor}
                          onChange={setExonColor}
                          format="hex"
                          withEyeDropper={false}
                        />
                      </Grid.Col>
                      <Grid.Col span={4}>
                        <ColorInput
                          label="Introns"
                          value={lineColor}
                          onChange={setLineColor}
                          format="hex"
                          withEyeDropper={false}
                        />
                      </Grid.Col>
                    </Grid>
                  </Stack>
                </Card>

                <Card shadow="xl" padding="lg" radius="md">
                  <Title order={3} mb="md">
                    Detail Settings
                  </Title>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </Stack>
      )}

      {/* Export dialog */}
      <Modal
        opened={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        title="Export Settings"
        centered
      >
        <Stack gap="md">
          <TextInput
            label="File Name"
            value={exportSettings.filename}
            onChange={(e) =>
              setExportSettings({
                ...exportSettings,
                filename: e.target.value,
              })
            }
          />

          <Select
            label="File Format"
            value={exportSettings.format}
            onChange={(value) =>
              setExportSettings({
                ...exportSettings,
                format: value as "svg" | "png",
              })
            }
            data={[
              { value: "svg", label: "SVG" },
              { value: "png", label: "PNG" },
            ]}
          />

          {exportSettings.format === "png" && (
            <>
              <Select
                label="DPI"
                value={String(exportSettings.dpi)}
                onChange={(value) =>
                  setExportSettings({
                    ...exportSettings,
                    dpi: Number(value),
                  })
                }
                data={[
                  { value: "72", label: "72 DPI" },
                  { value: "150", label: "150 DPI" },
                  { value: "300", label: "300 DPI" },
                  { value: "600", label: "600 DPI" },
                ]}
              />

              <Select
                label="Background"
                value={exportSettings.background}
                onChange={(value) =>
                  setExportSettings({
                    ...exportSettings,
                    background: value as "transparent" | "white",
                  })
                }
                data={[
                  { value: "transparent", label: "Transparent" },
                  { value: "white", label: "White" },
                ]}
              />
            </>
          )}

          <Group justify="flex-end" mt="md">
            <Button
              variant="outline"
              onClick={() => setShowExportDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDownload}
              disabled={isLoading}
              loading={isLoading}
              leftSection={<i className="bx bx-download" />}
            >
              Download
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  );
}
