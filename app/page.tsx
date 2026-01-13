"use client";

import {
  Autocomplete,
  Badge,
  Button,
  Card,
  Code,
  ColorInput,
  Divider,
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
import { notifications } from "@mantine/notifications";
import {
  IconArrowRight,
  IconCloudUpload,
  IconDownload,
  IconPlayerPlay,
  IconRefresh,
  IconX,
} from "@tabler/icons-react";
import Fuse from "fuse.js";
import { useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";

import SvgViewer from "./components/SvgViewer";
import { apiClient, type components } from "./lib/api";
import {
  type GeneStructureInfo,
  getGeneStructureInfo,
  getmRNAs,
  parseGff,
} from "./utils/gff";

type UIState = "upload" | "preview";

type GeneStructureRequest = components["schemas"]["GeneStructureRequest"];

type ExportSettings = {
  format: "svg" | "png";
  dpi: number;
  background: "transparent" | "white";
  filename: string;
};

const postFetcher = async (data: GeneStructureRequest | null) => {
  if (!data) {
    throw new Error("No data provided");
  }

  const {
    data: blob,
    error,
    response,
  } = await apiClient.POST("/api/py/generate-gene-structure-svg", {
    body: data,
    parseAs: "blob",
  });

  if (error) {
    if (response.status === 422) {
      const errorData = error as components["schemas"]["HTTPValidationError"];
      if (errorData.detail && Array.isArray(errorData.detail)) {
        const errorMessages = errorData.detail
          .map((err) => {
            const field = err.loc?.join(".") || "unknown";
            return `${field}: ${err.msg}`;
          })
          .join("\n");

        notifications.show({
          title: "Validation Error",
          message: errorMessages,
          color: "red",
          autoClose: 10000,
        });
        throw new Error("Validation error");
      }
    }

    notifications.show({
      title: "Error",
      message: `API error: ${response.status}`,
      color: "red",
      autoClose: 5000,
    });
    throw new Error(`API error: ${response.status}`);
  }

  if (!blob) {
    throw new Error("No blob received from API");
  }
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
  const [selectedPresetGff, setSelectedPresetGff] = useState<string | null>(
    null,
  );
  const [presetGffOptions, setPresetGffOptions] = useState<
    Array<{ group: string; items: Array<{ value: string; label: string }> }>
  >([]);
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

  // Deletion and domain settings
  const [deletionRegions, setDeletionRegions] = useState<
    Array<[number | undefined, number | undefined]>
  >([]);
  const [proteinDomainStart, setProteinDomainStart] = useState<
    number | undefined
  >();
  const [proteinDomainEnd, setProteinDomainEnd] = useState<
    number | undefined
  >();
  const [proteinDomainName, setProteinDomainName] = useState<string>("");

  // Load preset GFF files from public/gffs
  useEffect(() => {
    const loadPresetGffs = async () => {
      try {
        const response = await fetch("/api/list-gffs");
        const data = await response.json();
        if (data.files) {
          // Convert flat array with group property to grouped format for Mantine v8
          const groupedData: Array<{
            group: string;
            items: Array<{ value: string; label: string }>;
          }> = [];
          const groupMap = new Map<
            string,
            Array<{ value: string; label: string }>
          >();

          for (const file of data.files) {
            const group = file.group || "Other";
            if (!groupMap.has(group)) {
              groupMap.set(group, []);
            }
            groupMap.get(group)?.push({ value: file.value, label: file.label });
          }

          for (const [group, items] of groupMap) {
            groupedData.push({ group, items });
          }

          setPresetGffOptions(groupedData);
        }
      } catch (error) {
        console.error("Error loading preset GFF files:", error);
      }
    };
    loadPresetGffs();
  }, []);

  // Handle preset GFF selection
  const handlePresetGffSelect = async (value: string | null) => {
    if (!value) return;

    setSelectedPresetGff(value);
    setIsLoading(true);

    try {
      const response = await fetch(value);
      const text = await response.text();
      const blob = new Blob([text], { type: "text/plain" });
      const file = new File([blob], value.split("/").pop() || "preset.gff", {
        type: "text/plain",
      });

      setSelectedFile(file);
      const gffData = await parseGff(file);
      const mRNAs = getmRNAs(gffData);
      const geneStructureInfo = getGeneStructureInfo(mRNAs);
      setGeneStructures(geneStructureInfo);

      notifications.show({
        title: "Success",
        message: "Preset GFF file loaded successfully",
        color: "green",
        autoClose: 3000,
      });
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Error loading preset GFF file: ${error}`,
        color: "red",
        autoClose: 5000,
      });
      setSelectedPresetGff(null);
    } finally {
      setIsLoading(false);
    }
  };

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
      notifications.show({
        title: "Error",
        message: "Select a GFF file",
        color: "red",
        autoClose: 5000,
      });
      return;
    }
    if (selectedTranscripts.length === 0) {
      notifications.show({
        title: "Error",
        message: "Select at least one gene/transcript",
        color: "red",
        autoClose: 5000,
      });
      return;
    }

    try {
      setIsLoading(true);

      // 処理完了後、UI状態を生成画面に変更
      setUiState("preview");
      await handleGenerateSVG(geneStructures[0]);
    } catch (error) {
      console.error("Error processing file:", error);
      notifications.show({
        title: "Error",
        message: `An error occurred while processing the file: ${error instanceof Error ? error.message : "Unknown error"}`,
        color: "red",
        autoClose: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getRequestData = (): GeneStructureRequest | null => {
    if (geneStructures.length === 0) return null;
    if (selectedTranscripts.length === 0) return null;

    const selectedGeneStructure = geneStructures.find((gs) =>
      selectedTranscripts.includes(gs.transcript_id),
    );

    if (!selectedGeneStructure) return null;

    const requestData: GeneStructureRequest = {
      draw_settings: {
        mode: "domain",
        utr_color: utrColor,
        exon_color: exonColor,
        line_color: lineColor,
        intron_shape: "straight",
      },
      gene_structure:
        selectedGeneStructure as components["schemas"]["GeneStructureInfo"],
      deletion_regions: [],
      domains: [],
    };

    // Add deletion regions if any (filter out invalid regions)
    const validDeletionRegions = deletionRegions
      .filter(
        (region): region is [number, number] =>
          region[0] !== undefined &&
          region[1] !== undefined &&
          region[0] > 0 &&
          region[1] > 0,
      )
      .map(([start, end]) => [start, end]);

    if (validDeletionRegions.length > 0) {
      requestData.deletion_regions = validDeletionRegions;
    }

    // Add protein domain if specified
    if (proteinDomainStart && proteinDomainEnd && proteinDomainName) {
      requestData.protein_domain_start = proteinDomainStart;
      requestData.protein_domain_end = proteinDomainEnd;
      requestData.protein_domain_name = proteinDomainName;
    }

    return requestData;
  };

  const { data: svgData, mutate: mutateSVG } = useSWR(
    () => {
      const requestData = getRequestData();
      return requestData ? ["generate-gene-structure-svg", requestData] : null;
    },
    ([_key, data]) => postFetcher(data),
    {
      onSuccess: (data) => {
        renderSvgToCanvas(data.url);
      },
    },
  );

  const handleGenerateSVG = async (structure: GeneStructureInfo | null) => {
    if (!structure) {
      notifications.show({
        title: "Error",
        message: "Please process the file first",
        color: "red",
        autoClose: 5000,
      });
      setUiState("upload");
      return;
    }

    try {
      setIsLoading(true);
      // SWRのキャッシュを更新して再フェッチをトリガー
      await mutateSVG();
    } catch (error) {
      console.error("Error generating SVG:", error);
      // postFetcherで既にtoast表示しているので、ここでは表示しない
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
    setSelectedPresetGff(null);
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
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      {uiState === "upload" && (
        <Stack>
          <Title order={2} mb="md">
            Upload
          </Title>

          <Stack mb={32} gap="md">
            <Grid gutter="md">
              <Grid.Col span={6}>
                <Card shadow="xl" padding="lg" radius="md" mb={32} h="100%">
                  <Title order={3} mb="md">
                    Upload File
                  </Title>

                  <Stack>
                    <Select
                      label="Or select from preset GFF files"
                      placeholder="Choose a preset GFF file"
                      data={presetGffOptions}
                      value={selectedPresetGff}
                      onChange={handlePresetGffSelect}
                      searchable
                      clearable
                      disabled={isLoading}
                      maxDropdownHeight={300}
                    />

                    <Divider label="OR" labelPosition="center" />

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
                            notifications.show({
                              title: "Error",
                              message: `Error parsing GFF file: ${error}`,
                              color: "red",
                              autoClose: 5000,
                            });
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

                    <div style={{ marginTop: "1rem" }}>
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
                <Card shadow="xl" padding="lg" radius="md" mb={32} h="100%">
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
                        <Text size="sm" fw={500}>
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
                  <Stack>
                    <Text size="sm" fw={500}>
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
                  <Stack gap="md">
                    <Stack>
                      <Text size="sm" fw={500} mb="xs">
                        Protein Domain (amino acid coordinates):
                      </Text>
                      <Grid>
                        <Grid.Col span={4}>
                          <NumberInput
                            label="Start"
                            placeholder="1"
                            value={proteinDomainStart}
                            onChange={(val) =>
                              setProteinDomainStart(
                                val === "" ? undefined : Number(val),
                              )
                            }
                            min={1}
                          />
                        </Grid.Col>
                        <Grid.Col span={4}>
                          <NumberInput
                            label="End"
                            placeholder="100"
                            value={proteinDomainEnd}
                            onChange={(val) =>
                              setProteinDomainEnd(
                                val === "" ? undefined : Number(val),
                              )
                            }
                            min={1}
                          />
                        </Grid.Col>
                        <Grid.Col span={4}>
                          <TextInput
                            label="Name"
                            placeholder="Domain name"
                            value={proteinDomainName}
                            onChange={(e) =>
                              setProteinDomainName(e.currentTarget.value)
                            }
                          />
                        </Grid.Col>
                      </Grid>
                    </Stack>

                    <Stack>
                      <Text size="sm" fw={500} mb="xs">
                        Deletion Regions (genomic coordinates):
                      </Text>
                      <Text size="xs" c="dimmed" mb="xs">
                        Enter positive integers (e.g., start: 12, end: 2000)
                      </Text>
                      <Stack gap="xs">
                        {deletionRegions.map((region, idx) => (
                          <Group
                            key={`deletion-${idx}-${region[0]}-${region[1]}`}
                            gap="xs"
                          >
                            <NumberInput
                              placeholder="e.g., 12"
                              value={region[0]}
                              onChange={(val) => {
                                const newRegions = [...deletionRegions];
                                newRegions[idx][0] =
                                  val === "" ? undefined : Number(val);
                                setDeletionRegions(newRegions);
                              }}
                              min={1}
                              style={{ flex: 1 }}
                            />
                            <NumberInput
                              placeholder="e.g., 2000"
                              value={region[1]}
                              onChange={(val) => {
                                const newRegions = [...deletionRegions];
                                newRegions[idx][1] =
                                  val === "" ? undefined : Number(val);
                                setDeletionRegions(newRegions);
                              }}
                              min={1}
                              style={{ flex: 1 }}
                            />
                            <Button
                              variant="outline"
                              color="red"
                              size="sm"
                              onClick={() => {
                                setDeletionRegions(
                                  deletionRegions.filter((_, i) => i !== idx),
                                );
                              }}
                            >
                              Remove
                            </Button>
                          </Group>
                        ))}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setDeletionRegions([
                              ...deletionRegions,
                              [undefined, undefined],
                            ]);
                          }}
                        >
                          Add Deletion Region
                        </Button>
                      </Stack>
                    </Stack>
                  </Stack>
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
