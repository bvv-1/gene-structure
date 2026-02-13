"use client";

import {
  Accordion,
  Anchor,
  Card,
  Code,
  Container,
  Divider,
  List,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconApi,
  IconCode,
  IconCpu,
  IconDatabase,
  IconFileCode,
  IconPalette,
  IconUpload,
  IconUserCheck,
} from "@tabler/icons-react";

export default function Docs() {
  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        <Title order={1} mb="md">
          Documentation
        </Title>

        {/* User Guide */}
        <Card shadow="xl" padding="lg" radius="md">
          <Title order={2} mb="md">
            <ThemeIcon variant="light" radius="xl" size="lg" mr="sm">
              <IconUserCheck size={20} />
            </ThemeIcon>
            User Guide
          </Title>

          <Accordion variant="separated" radius="md">
            {/* Step 1: File Upload */}
            <Accordion.Item value="step1">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconUpload size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Step 1: Upload GFF3 File</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    1. Open the application and drag & drop your GFF3 file into
                    the drop zone on the Upload page, or click to select a file.
                  </Text>
                  <Text>
                    2. Once the file is uploaded, parsing begins automatically
                    and mRNA features are extracted.
                  </Text>
                  <Text fw={500}>Supported File Formats:</Text>
                  <List spacing="xs">
                    <List.Item>
                      Extensions: <Code>.gff</Code> or <Code>.gff3</Code>
                    </List.Item>
                    <List.Item>
                      Format: GFF3 (Generic Feature Format version 3)
                    </List.Item>
                    <List.Item>Tab-delimited format</List.Item>
                  </List>
                  <Text size="sm" c="dimmed">
                    Note: The file must have a properly defined gene structure
                    hierarchy (gene → mRNA → exon/CDS/UTR).
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Step 2: Gene Search */}
            <Accordion.Item value="step2">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconDatabase size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Step 2: Select Genes/Transcripts</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    Once the file upload is complete, the search box becomes
                    enabled.
                  </Text>
                  <Text fw={500}>Search Features:</Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>Autocomplete:</Text> Suggestions appear in
                      real-time as you type
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Fuzzy Search:</Text> Flexible search using
                      Fuse.js (threshold: 0.5)
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Search Fields:</Text> transcript_id, Parent
                      attribute
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Display Limit:</Text> Up to 20 results
                    </List.Item>
                  </List>
                  <Text>
                    Selected transcripts are displayed as badges and can be
                    removed with the × button.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Step 3: Preview Generation */}
            <Accordion.Item value="step3">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconPalette size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Step 3: Generate and Customize Preview</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    Click the "Generate Preview" button to create a gene
                    structure diagram for the selected transcript.
                  </Text>
                  <Text fw={500}>Preview Screen Features:</Text>
                  <List spacing="md">
                    <List.Item>
                      <Text fw={500}>SVG Viewer:</Text>
                      <List withPadding>
                        <List.Item>Pan (drag to move)</List.Item>
                        <List.Item>Zoom (mouse wheel)</List.Item>
                        <List.Item>Auto-fit functionality</List.Item>
                      </List>
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Color Customization:</Text>
                      <List withPadding>
                        <List.Item>
                          UTRs (5' and 3' untranslated regions)
                        </List.Item>
                        <List.Item>Exons (exons/CDS)</List.Item>
                        <List.Item>Introns (intron lines)</List.Item>
                      </List>
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Regenerate Button:</Text> Click to
                      regenerate the diagram after changing colors
                    </List.Item>
                  </List>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Step 4: Export */}
            <Accordion.Item value="step4">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconFileCode size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Step 4: Export</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    Click the "Export" button to open the export settings
                    dialog.
                  </Text>
                  <Text fw={500}>Export Options:</Text>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Setting</Table.Th>
                        <Table.Th>Options</Table.Th>
                        <Table.Th>Description</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td>Filename</Table.Td>
                        <Table.Td>Any text</Table.Td>
                        <Table.Td>
                          Output filename (extension auto-appended)
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Format</Table.Td>
                        <Table.Td>SVG / PNG</Table.Td>
                        <Table.Td>Output format selection</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>DPI (PNG only)</Table.Td>
                        <Table.Td>72 / 150 / 300 / 600</Table.Td>
                        <Table.Td>
                          Image resolution (300+ recommended for publications)
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Background (PNG only)</Table.Td>
                        <Table.Td>Transparent / White</Table.Td>
                        <Table.Td>Background color selection</Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Card>

        <Divider />

        {/* Technical Specifications */}
        <Card shadow="xl" padding="lg" radius="md">
          <Title order={2} mb="md">
            <ThemeIcon variant="light" radius="xl" size="lg" mr="sm">
              <IconCpu size={20} />
            </ThemeIcon>
            Technical Specifications
          </Title>

          <Accordion variant="separated" radius="md">
            {/* GFF Parser */}
            <Accordion.Item value="gff-parser">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconCode size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>GFF3 Parser Implementation</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text fw={500}>Library Used:</Text>
                  <Code block p="md">
                    @gmod/gff (util.parseFeature)
                  </Code>
                  <Text>
                    The frontend uses the <Code>@gmod/gff</Code> library with
                    streaming parsing for efficient memory usage on large files.
                  </Text>

                  <Text fw={500} mt="md">
                    Parser Processing Flow:
                  </Text>
                  <Code block p="md">
                    {`// Streaming parser for GFF3 files
async function* parseGff3FileGenerator(file: File) {
  const stream = file.stream();
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader();

  // Parse line by line
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    for (const line of lines) {
      const feature = gffUtil.parseFeature(line);
      // Process mRNA, exon, CDS, UTR features
    }
  }

  yield* yieldGeneStructures(mRNAs);
}`}
                  </Code>

                  <Text fw={500} mt="md">
                    Data Type Definitions:
                  </Text>
                  <Code block p="md">
                    {`type Position = {
  start: number;
  end: number;
};

type GeneStructureInfo = GFF3FeatureLine & {
  transcript_id: string;
  total_length: number;
  exons: Position[];
  cds: Position[];
  five_prime_utrs: Position[];
  three_prime_utrs: Position[];
};`}
                  </Code>

                  <Text fw={500} mt="md">
                    Main Functions:
                  </Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>parseGff:</Text> Uses FileReader to read
                      file as string and parses with parseStringSync
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>getmRNAs:</Text> Traverses GFF3
                      hierarchical tree with depth-first search (DFS) to extract
                      only mRNA features
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>getGeneStructureInfo:</Text> Categorizes
                      mRNA child features (exon, CDS, UTR) and converts to
                      structured data
                    </List.Item>
                  </List>

                  <Text size="sm" c="dimmed" mt="md">
                    Implementation file: <Code>app/utils/gff.ts</Code>
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* API Specifications */}
            <Accordion.Item value="api-spec">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconApi size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>API Specifications</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    This application consists of a Next.js frontend and FastAPI
                    (Python) backend.
                  </Text>

                  <Divider
                    label="Python API (FastAPI)"
                    labelPosition="center"
                  />

                  <Text fw={500}>Endpoint List:</Text>

                  <Card withBorder p="md">
                    <Stack gap="sm">
                      <Text fw={700} size="lg">
                        POST /api/py/generate-gene-structure-svg
                      </Text>
                      <Text>
                        Generates SVG image of gene structure (main API).
                      </Text>

                      <Text fw={500} mt="xs">
                        Request Body:
                      </Text>
                      <Code block p="md">
                        {`{
  "draw_settings": {
    "mode": "domain" | "gene",
    "utr_color": "#d3d3d3",
    "exon_color": "#000000",
    "line_color": "#000000",
    "intron_shape": "straight" | "zigzag",
    "gene_height": number (optional),
    "margin_x": number (optional),
    "margin_y": number (optional)
  },
  "gene_structure": {
    "transcript_id": "AT1G01010.1",
    "seq_id": "Chr1",
    "strand": "+" | "-",
    "start": number,
    "end": number,
    "total_length": number,
    "exons": [{ "start": number, "end": number }],
    "cds": [{ "start": number, "end": number }],
    "five_prime_utrs": [{ "start": number, "end": number }],
    "three_prime_utrs": [{ "start": number, "end": number }]
  }
}`}
                      </Code>

                      <Text fw={500} mt="xs">
                        Response:
                      </Text>
                      <List spacing="xs">
                        <List.Item>
                          Content-Type: <Code>image/svg+xml</Code>
                        </List.Item>
                        <List.Item>Body: SVG format image data</List.Item>
                      </List>
                    </Stack>
                  </Card>

                  <Card withBorder p="md">
                    <Stack gap="sm">
                      <Text fw={700} size="lg">
                        POST /api/py/draw-gene
                      </Text>
                      <Text>
                        Draws gene structure directly from GFF file (legacy
                        API).
                      </Text>

                      <Text fw={500} mt="xs">
                        Request Body:
                      </Text>
                      <Code block p="md">
                        {`{
  "transcript_id": "AT1G01010.1",
  "gff_file_path": "./path/to/file.gff",
  "deletion_regions": [[start, end], ...],
  "domains": [
    {
      "start": number,
      "end": number,
      "name": "domain name",
      "color": "#hexcolor"
    }
  ],
  "protein_domain_start": number (optional),
  "protein_domain_end": number (optional),
  "protein_domain_name": string (optional)
}`}
                      </Code>
                    </Stack>
                  </Card>

                  <Card withBorder p="md">
                    <Stack gap="sm">
                      <Text fw={700} size="lg">
                        GET /
                      </Text>
                      <Text>Health check endpoint.</Text>
                      <Text fw={500} mt="xs">
                        Response:
                      </Text>
                      <Code block p="md">
                        {`{ "message": "health check" }`}
                      </Code>
                    </Stack>
                  </Card>

                  <Divider
                    label="Next.js API Routes"
                    labelPosition="center"
                    mt="lg"
                  />

                  <Card withBorder p="md">
                    <Stack gap="sm">
                      <Text fw={700} size="lg">
                        POST /api/upload-gff
                      </Text>
                      <Text>
                        Handles file uploads to Vercel Blob Storage (currently
                        unused).
                      </Text>

                      <Text fw={500} mt="xs">
                        Features:
                      </Text>
                      <List spacing="xs">
                        <List.Item>
                          File upload using Vercel Blob Client API
                        </List.Item>
                        <List.Item>
                          Allowed content types: application/gff3, text/plain
                        </List.Item>
                        <List.Item>
                          Token generation before upload (onBeforeGenerateToken)
                        </List.Item>
                        <List.Item>
                          Callback processing on upload completion
                          (onUploadCompleted)
                        </List.Item>
                      </List>

                      <Text size="sm" c="dimmed" mt="xs">
                        Note: This API is not currently used as GFF parsing is
                        done client-side.
                      </Text>
                    </Stack>
                  </Card>

                  <Text fw={500} mt="md">
                    Deployment Configuration (vercel.json):
                  </Text>
                  <Code block p="md">
                    {`{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "package.json", "use": "@vercel/next" }
  ],
  "routes": [
    { "src": "/api/py/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "/$1" }
  ]
}`}
                  </Code>

                  <Text size="sm" c="dimmed" mt="md">
                    Python API documentation:{" "}
                    <Anchor
                      href="/api/py/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      /api/py/docs
                    </Anchor>
                  </Text>

                  <Text size="sm" c="dimmed">
                    Implementation files: <Code>api/index.py</Code>,{" "}
                    <Code>app/api/upload-gff/route.ts</Code>
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Python Drawing Engine */}
            <Accordion.Item value="python-engine">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconFileCode size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Python Drawing Engine</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    The backend Python (FastAPI) uses the svgwrite library to
                    generate SVG images.
                  </Text>

                  <Text fw={500}>Main Classes:</Text>

                  <Card withBorder p="md">
                    <Text fw={700}>GeneFeature</Text>
                    <Code block p="md" mt="xs">
                      {`class GeneFeature:
    def __init__(self, seqid, start, end,
                 feature_type, strand, attributes=None):
        self.seqid = seqid
        self.start = start
        self.end = end
        self.feature_type = feature_type
        self.strand = strand
        self.attributes = attributes or {}`}
                    </Code>
                    <Text size="sm" mt="xs">
                      Class representing individual gene features (exon, CDS,
                      UTR, etc.)
                    </Text>
                  </Card>

                  <Card withBorder p="md">
                    <Text fw={700}>GeneStructure</Text>
                    <Code block p="md" mt="xs">
                      {`class GeneStructure:
    def __init__(self, gene_id, seqid, strand):
        self.gene_id = gene_id
        self.seqid = seqid
        self.strand = strand
        self.features = []

    def add_feature(self, feature: GeneFeature)
    def get_sorted_features(self)
    def add_introns(self)
    def to_relative(self)
    def add_domains(self, domain_regions)
    def update_features_with_deletions(self, deletion_regions)`}
                    </Code>
                    <Text size="sm" mt="xs">
                      Class managing entire gene structure with feature addition
                      and coordinate transformation
                    </Text>
                  </Card>

                  <Text fw={500} mt="md">
                    Main Drawing Function Processes:
                  </Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>Coordinate Relativization:</Text>{" "}
                      to_relative() converts to relative coordinates based on
                      minimum coordinate
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Scaling:</Text> shrink_factor (default
                      30.0) compresses coordinates, scale parameter adjusts
                      drawing size
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Minus Strand Support:</Text> When strand =
                      "-", coordinates are converted to negative values
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Automatic Intron Generation:</Text> Intron
                      regions automatically calculated from exon/CDS/UTR gaps
                    </List.Item>
                  </List>

                  <Text fw={500} mt="md">
                    Drawing Elements:
                  </Text>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Element</Table.Th>
                        <Table.Th>SVG Element</Table.Th>
                        <Table.Th>Default Settings</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td>Exon/CDS</Table.Td>
                        <Table.Td>rect</Table.Td>
                        <Table.Td>
                          fill: exon_color, stroke: black, stroke-width: 1
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>UTR</Table.Td>
                        <Table.Td>rect</Table.Td>
                        <Table.Td>
                          fill: utr_color, stroke: black, stroke-width: 1
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Intron</Table.Td>
                        <Table.Td>line</Table.Td>
                        <Table.Td>stroke: line_color, stroke-width: 1</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Domain</Table.Td>
                        <Table.Td>rect</Table.Td>
                        <Table.Td>
                          fill: domain_color, stroke: black, stroke-width: 1
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Deletion</Table.Td>
                        <Table.Td>rect</Table.Td>
                        <Table.Td>
                          fill: none, stroke: red, stroke-dasharray: "5,5"
                        </Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>

                  <Text fw={500} mt="md">
                    Automatic Legend Generation:
                  </Text>
                  <Text>
                    A legend is automatically added to the right side of the
                    SVG, allowing visual understanding of each element's
                    meaning.
                  </Text>

                  <Text size="sm" c="dimmed" mt="md">
                    Implementation file: <Code>api/index.py</Code> (lines
                    258-395)
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Frontend Implementation */}
            <Accordion.Item value="frontend">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconCode size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Frontend Implementation</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text fw={500}>Main Technology Stack:</Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>Next.js:</Text> React framework
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Mantine UI:</Text> UI component library
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>SWR:</Text> Data fetching and caching
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Fuse.js:</Text> Fuzzy search engine
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>react-svg-pan-zoom:</Text> SVG viewer
                      component
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>react-dropzone:</Text> File upload
                    </List.Item>
                  </List>

                  <Text fw={500} mt="md">
                    State Management:
                  </Text>
                  <Code block p="md">
                    {`// UI state
const [uiState, setUiState] = useState<UIState>("upload" | "preview");

// File & data state
const [selectedFile, setSelectedFile] = useState<File | null>(null);
const [geneStructures, setGeneStructures] = useState<GeneStructureInfo[]>([]);
const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);

// Drawing settings
const [utrColor, setUtrColor] = useState("#d3d3d3");
const [exonColor, setExonColor] = useState("#000000");
const [lineColor, setLineColor] = useState("#000000");

// SVG data caching with SWR
const { data: svgData, mutate: mutateSVG } = useSWR(
  ["/api/py/generate-gene-structure-svg", getRequestData()],
  () => postFetcher("/api/py/generate-gene-structure-svg", getRequestData())
);`}
                  </Code>

                  <Text fw={500} mt="md">
                    Processing Flow:
                  </Text>
                  <List type="ordered" spacing="sm">
                    <List.Item>
                      File drop → parseGff() → getmRNAs() →
                      getGeneStructureInfo()
                    </List.Item>
                    <List.Item>
                      Search input → Fuse.js fuzzy search → autocomplete
                      suggestions
                    </List.Item>
                    <List.Item>
                      Transcript selection → add to selectedTranscripts array
                    </List.Item>
                    <List.Item>
                      "Generate Preview" click → SWR API request → receive SVG
                    </List.Item>
                    <List.Item>
                      Color change → "Regenerate" click → SWR cache update →
                      refetch
                    </List.Item>
                    <List.Item>
                      "Export" click → PNG conversion (using Canvas API) →
                      download
                    </List.Item>
                  </List>

                  <Text fw={500} mt="md">
                    SVG Viewer Component:
                  </Text>
                  <Code block p="md">
                    {`// SvgViewer.tsx
<ReactSVGPanZoom
  tool={tool}
  onChangeTool={setTool}
  value={value}
  onChangeValue={setValue}
  detectAutoPan={false}
  background="#ffffff"
>
  <svg>
    <g dangerouslySetInnerHTML={{ __html: svgContent }} />
  </svg>
</ReactSVGPanZoom>`}
                  </Code>

                  <Text size="sm" c="dimmed" mt="md">
                    Implementation files: <Code>app/page.tsx</Code>,{" "}
                    <Code>app/components/SvgViewer.tsx</Code>
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Card>
      </Stack>
    </Container>
  );
}
