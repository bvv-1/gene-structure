"use client";

import {
  Button,
  Card,
  ColorInput,
  Divider,
  Grid,
  Group,
  Modal,
  NumberInput,
  SegmentedControl,
  Select,
  Slider,
  Stack,
  Stepper,
  Switch,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";
import { notifications } from "@mantine/notifications";
import {
  IconArrowLeft,
  IconArrowRight,
  IconCloudUpload,
  IconDownload,
  IconEye,
  IconListSearch,
  IconUpload,
  IconX,
} from "@tabler/icons-react";
import { useMemo, useRef, useState } from "react";
import useSWR from "swr";

import { GeneSelector } from "./components/GeneSelector";
import { RegionSelector } from "./components/RegionSelector";
import SvgViewer from "./components/SvgViewer";
import {
  type GeneStructureInfo as ApiGeneStructureInfo,
  type GeneStructureRequest,
  type GenerateSvgBlobError,
  type HTTPValidationError,
  generateGeneStructureSvgBlob,
  useListGffs,
} from "./lib/api";
import { type GeneStructureInfo, filterByRegion, getSeqIds } from "./utils/gff";
import { parseFile, parseFileContent } from "./utils/gtf";

type UIState = "upload" | "select" | "preview";

type MultiGeneStructureRequest = {
  draw_settings: {
    mode: string;
    utr_color: string;
    exon_color: string;
    line_color: string;
    intron_shape: string;
  };
  gene_structures: ApiGeneStructureInfo[];
  show_labels: boolean;
  gene_spacing: number;
  label_spacing: number;
  deletion_regions?: number[][];
  domains?: { start: number; end: number; name: string }[];
  protein_domain_start?: number;
  protein_domain_end?: number;
  protein_domain_name?: string;
};

type RegionGeneStructureRequest = {
  draw_settings: {
    mode: string;
    utr_color: string;
    exon_color: string;
    line_color: string;
    intron_shape: string;
  };
  gene_structures: ApiGeneStructureInfo[];
  region_start: number;
  region_end: number;
  show_labels: boolean;
  gene_spacing: number;
  label_spacing: number;
};

type ExportSettings = {
  format: "svg" | "png";
  dpi: number;
  background: "transparent" | "white";
  filename: string;
};

const postMultiFetcher = async (data: MultiGeneStructureRequest | null) => {
  if (!data) {
    throw new Error("No data provided");
  }

  const response = await fetch("/api/py/generate-multi-gene-structure-svg", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 422) {
      const errorData = await response.json();
      if (errorData.detail && Array.isArray(errorData.detail)) {
        const errorMessages = errorData.detail
          .map((err: { loc?: string[]; msg: string }) => {
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

  const blob = await response.blob();
  return { blob, url: window.URL.createObjectURL(blob) };
};

const postRegionFetcher = async (data: RegionGeneStructureRequest | null) => {
  if (!data) {
    throw new Error("No data provided");
  }

  const response = await fetch("/api/py/generate-region-gene-structure-svg", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    if (response.status === 422) {
      const errorData = await response.json();
      if (errorData.detail && Array.isArray(errorData.detail)) {
        const errorMessages = errorData.detail
          .map((err: { loc?: string[]; msg: string }) => {
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

  const blob = await response.blob();
  return { blob, url: window.URL.createObjectURL(blob) };
};

const postFetcher = async (data: GeneStructureRequest | null) => {
  if (!data) {
    throw new Error("No data provided");
  }

  try {
    const result = await generateGeneStructureSvgBlob(data);
    return { blob: result.blob, url: window.URL.createObjectURL(result.blob) };
  } catch (error) {
    const apiError = error as GenerateSvgBlobError;

    if (apiError.status === 422) {
      const errorData = apiError.data as HTTPValidationError;
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
      message: `API error: ${apiError.status}`,
      color: "red",
      autoClose: 5000,
    });
    throw new Error(`API error: ${apiError.status}`);
  }
};

export default function Home() {
  const [uiState, setUiState] = useState<UIState>("upload");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);
  const [utrColor, setUtrColor] = useState("#d3d3d3");
  const [exonColor, setExonColor] = useState("#000000");
  const [lineColor, setLineColor] = useState("#000000");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedPresetGff, setSelectedPresetGff] = useState<string | null>(
    null,
  );
  const { groupedOptions: presetGffOptions } = useListGffs();
  const [geneStructures, setGeneStructures] = useState<GeneStructureInfo[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    format: "svg",
    dpi: 300,
    background: "white",
    filename: "gene_structure",
  });

  // Display options
  const [showLabels, setShowLabels] = useState(true);
  const [geneSpacing, setGeneSpacing] = useState(50);
  const [labelSpacing, setLabelSpacing] = useState(10);

  // Selection mode (transcript or region)
  const [selectionMode, setSelectionMode] = useState<"transcript" | "region">(
    "transcript",
  );

  // Region filter
  const [regionFilter, setRegionFilter] = useState({
    seqId: "",
    start: "",
    end: "",
  });

  // Derived data for region mode
  const seqIds = useMemo(() => getSeqIds(geneStructures), [geneStructures]);

  const filteredByRegion = useMemo(() => {
    if (!regionFilter.seqId || !regionFilter.start || !regionFilter.end) {
      return [];
    }
    const start = Number.parseInt(regionFilter.start);
    const end = Number.parseInt(regionFilter.end);
    if (Number.isNaN(start) || Number.isNaN(end) || start >= end) {
      return [];
    }
    return filterByRegion(geneStructures, regionFilter.seqId, start, end);
  }, [geneStructures, regionFilter]);

  const canProceedFromRegion =
    filteredByRegion.length > 0 && filteredByRegion.length <= 30;

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
      const geneStructureInfo = await parseFileContentAsync(text, file.name);
      setGeneStructures(geneStructureInfo);

      notifications.show({
        title: "Success",
        message: "Preset GFF file loaded successfully",
        color: "green",
        autoClose: 3000,
      });

      // 自動遷移: プリセット読み込み成功後にSelectへ
      setUiState("select");
    } catch (error) {
      notifications.show({
        title: "Error",
        message:
          error instanceof Error
            ? error.message
            : "プリセットGFFファイルの読み込み中にエラーが発生しました。",
        color: "red",
        autoClose: 5000,
      });
      setSelectedPresetGff(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getMultiRequestData = (): MultiGeneStructureRequest | null => {
    if (geneStructures.length === 0) return null;
    if (selectedTranscripts.length === 0) return null;

    // 選択順序を維持して遺伝子構造を取得
    const selectedGeneStructures = selectedTranscripts
      .map((id) => geneStructures.find((gs) => gs.transcript_id === id))
      .filter((gs): gs is GeneStructureInfo => gs !== undefined);

    if (selectedGeneStructures.length === 0) return null;

    const requestData: MultiGeneStructureRequest = {
      draw_settings: {
        mode: "domain",
        utr_color: utrColor,
        exon_color: exonColor,
        line_color: lineColor,
        intron_shape: "straight",
      },
      gene_structures: selectedGeneStructures as ApiGeneStructureInfo[],
      show_labels: showLabels,
      gene_spacing: geneSpacing,
      label_spacing: labelSpacing,
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

  const getRegionRequestData = (): RegionGeneStructureRequest | null => {
    if (filteredByRegion.length === 0) return null;

    return {
      draw_settings: {
        mode: "domain",
        utr_color: utrColor,
        exon_color: exonColor,
        line_color: lineColor,
        intron_shape: "straight",
      },
      gene_structures: filteredByRegion.map((g) => ({
        seq_id: g.seq_id,
        source: g.source,
        type: g.type,
        start: g.start,
        end: g.end,
        score: g.score,
        strand: g.strand,
        phase: g.phase,
        attributes: g.attributes,
        transcript_id: g.transcript_id,
        total_length: g.total_length,
        exons: g.exons,
        cds: g.cds,
        five_prime_utrs: g.five_prime_utrs,
        three_prime_utrs: g.three_prime_utrs,
      })) as ApiGeneStructureInfo[],
      region_start: Number.parseInt(regionFilter.start),
      region_end: Number.parseInt(regionFilter.end),
      show_labels: showLabels,
      gene_spacing: geneSpacing,
      label_spacing: labelSpacing,
    };
  };

  const { data: svgData, mutate: mutateSVG } = useSWR(
    () => {
      if (selectionMode === "region") {
        const requestData = getRegionRequestData();
        return requestData
          ? ["generate-region-gene-structure-svg", requestData]
          : null;
      }
      const requestData = getMultiRequestData();
      return requestData
        ? ["generate-multi-gene-structure-svg", requestData]
        : null;
    },
    ([key, data]) => {
      if (key === "generate-region-gene-structure-svg") {
        return postRegionFetcher(data as RegionGeneStructureRequest);
      }
      return postMultiFetcher(data as MultiGeneStructureRequest);
    },
    {
      onSuccess: (data) => {
        renderSvgToCanvas(data.url);
      },
    },
  );

  const handleGenerateSVG = async () => {
    if (selectionMode === "transcript" && selectedTranscripts.length === 0) {
      notifications.show({
        title: "Error",
        message: "Please select at least one gene",
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

  // ステップ番号を計算するヘルパー
  const getStepNumber = (state: UIState): number => {
    switch (state) {
      case "upload":
        return 0;
      case "select":
        return 1;
      case "preview":
        return 2;
      default:
        return 0;
    }
  };

  // ステップクリック時のハンドラー
  const handleStepClick = (step: number) => {
    const currentStep = getStepNumber(uiState);

    // 前のステップには常に戻れる
    if (step < currentStep) {
      const states: UIState[] = ["upload", "select", "preview"];
      setUiState(states[step]);
      return;
    }

    // 前進は条件付き
    if (step === 1 && geneStructures.length > 0) {
      setUiState("select");
    } else if (step === 2 && selectedTranscripts.length > 0) {
      setUiState("preview");
      handleGenerateSVG();
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <Stepper
        active={getStepNumber(uiState)}
        onStepClick={handleStepClick}
        mb="xl"
      >
        <Stepper.Step
          label="Upload"
          description="GFF3 file"
          icon={<IconUpload size={18} />}
        />
        <Stepper.Step
          label="Select"
          description="Transcripts"
          icon={<IconListSearch size={18} />}
          allowStepSelect={geneStructures.length > 0}
        />
        <Stepper.Step
          label="Preview"
          description="Figure"
          icon={<IconEye size={18} />}
          allowStepSelect={selectedTranscripts.length > 0}
        />
      </Stepper>

      {uiState === "upload" && (
        <Stack>
          <Title order={2} mb="md">
            Upload GFF3 File
          </Title>

          <Card shadow="xl" padding="lg" radius="md">
            <Stack>
              <Select
                label="Select from preset GFF files"
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
                    const file = files[0];
                    setSelectedFile(file);
                    setIsLoading(true);
                    try {
                      // GTFはストリーミング、GFF3は文字列ベースで処理
                      const geneStructureInfo = await parseFile(file);
                      setGeneStructures(geneStructureInfo);
                      // 自動遷移: ファイル解析成功後にSelectへ
                      setUiState("select");
                    } catch (error) {
                      notifications.show({
                        title: "Error",
                        message:
                          error instanceof Error
                            ? error.message
                            : "ファイルの解析中に予期しないエラーが発生しました。",
                        color: "red",
                        autoClose: 5000,
                      });
                    } finally {
                      setIsLoading(false);
                    }
                  }
                }}
                accept={{
                  "text/plain": [".gff", ".gff3", ".gtf"],
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
                      Drag and drop a GFF3/GTF file here
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
            </Stack>
          </Card>
        </Stack>
      )}

      {/* Select画面 */}
      {uiState === "select" && (
        <Stack>
          <Title order={2} mb="md">
            Select Transcripts
          </Title>

          <SegmentedControl
            value={selectionMode}
            onChange={(value) =>
              setSelectionMode(value as "transcript" | "region")
            }
            data={[
              { label: "Transcript Selection", value: "transcript" },
              { label: "Region Selection", value: "region" },
            ]}
            mb="md"
          />

          <Card shadow="xl" padding="lg" radius="md">
            {selectionMode === "transcript" ? (
              <GeneSelector
                geneStructures={geneStructures}
                selectedTranscripts={selectedTranscripts}
                onSelectionChange={setSelectedTranscripts}
                maxSelection={30}
                disabled={isLoading}
              />
            ) : (
              <RegionSelector
                seqIds={seqIds}
                regionFilter={regionFilter}
                onFilterChange={setRegionFilter}
                matchCount={filteredByRegion.length}
                maxSelection={30}
              />
            )}
          </Card>

          <Group justify="space-between" mt="md">
            <Button
              variant="outline"
              onClick={() => setUiState("upload")}
              leftSection={<IconArrowLeft size={16} />}
            >
              Back
            </Button>
            <Button
              onClick={() => {
                setUiState("preview");
                handleGenerateSVG();
              }}
              disabled={
                selectionMode === "transcript"
                  ? selectedTranscripts.length === 0 || isLoading
                  : !canProceedFromRegion || isLoading
              }
              loading={isLoading}
              rightSection={<IconArrowRight size={16} />}
            >
              Generate Preview
            </Button>
          </Group>
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
              <Button
                variant="outline"
                onClick={() => setUiState("select")}
                disabled={isLoading}
                leftSection={<IconArrowLeft size={16} />}
                mt="md"
              >
                Back to Select
              </Button>
            </Grid.Col>

            <Grid.Col span={4}>
              <Stack gap="md">
                <Button
                  size="lg"
                  onClick={() => setShowExportDialog(true)}
                  disabled={isLoading || !svgData}
                  leftSection={<IconDownload size={20} />}
                  fullWidth
                >
                  Export
                </Button>

                <Card shadow="xl" padding="lg" radius="md">
                  <Title order={3} mb="md">
                    Display Options
                  </Title>
                  <Stack gap="md">
                    <Switch
                      label="Show gene labels"
                      checked={showLabels}
                      onChange={(event) =>
                        setShowLabels(event.currentTarget.checked)
                      }
                    />
                    {selectedTranscripts.length >= 2 && (
                      <Stack gap="xs" pb="md">
                        <Text size="sm" fw={500}>
                          Gene spacing: {geneSpacing}px
                        </Text>
                        <Slider
                          value={geneSpacing}
                          onChange={setGeneSpacing}
                          min={10}
                          max={200}
                          step={5}
                          marks={[
                            { value: 10, label: "10" },
                            { value: 100, label: "100" },
                            { value: 200, label: "200" },
                          ]}
                        />
                      </Stack>
                    )}
                    {showLabels && (
                      <Stack gap="xs" pb="md">
                        <Text size="sm" fw={500}>
                          Label spacing: {labelSpacing}px
                        </Text>
                        <Slider
                          value={labelSpacing}
                          onChange={setLabelSpacing}
                          min={0}
                          max={100}
                          step={5}
                          marks={[
                            { value: 0, label: "0" },
                            { value: 50, label: "50" },
                            { value: 100, label: "100" },
                          ]}
                        />
                      </Stack>
                    )}
                  </Stack>
                </Card>

                <Card shadow="xl" padding="lg" radius="md">
                  <Title order={3} mb="md">
                    Color Settings
                  </Title>
                  <Stack>
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
