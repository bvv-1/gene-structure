"use client";

import {
  Accordion,
  Anchor,
  Card,
  Code,
  Container,
  Group,
  List,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconBrandGithub,
  IconFileDescription,
  IconHelp,
  IconPalette,
  IconSettings,
  IconUpload,
} from "@tabler/icons-react";

export default function FAQ() {
  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        <div>
          <Title order={1} mb="md">
            Frequently Asked Questions
          </Title>
          <Text size="lg" c="dimmed">
            Common questions about the gene structure visualization tool
          </Text>
        </div>

        <Card shadow="xl" padding="lg" radius="md">
          <Accordion variant="separated" radius="md">
            {/* Basic Usage */}
            <Accordion.Item value="what-is-this">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconHelp size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>What is this tool?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Text>
                  This is a web application for visualizing gene structures from
                  GFF3 format files. It generates intuitive diagrams showing
                  gene exons, introns, and UTR regions.
                </Text>
              </Accordion.Panel>
            </Accordion.Item>

            {/* File Upload */}
            <Accordion.Item value="file-format">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconUpload size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>What file formats are supported?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>
                    This tool supports GFF3 (Generic Feature Format version 3)
                    files.
                  </Text>
                  <Text fw={500}>Sample format:</Text>
                  <Code block p="md">
                    {`##gff-version 3
Chr1 TAIR10 gene 3631 5899 . + . ID=AT1G01010;Name=AT1G01010
Chr1 TAIR10 mRNA 3631 5899 . + . ID=AT1G01010.1;Parent=AT1G01010
Chr1 TAIR10 exon 3631 3913 . + . Parent=AT1G01010.1
Chr1 TAIR10 five_prime_UTR 3631 3759 . + . Parent=AT1G01010.1
Chr1 TAIR10 CDS 3760 3913 . + 0 Parent=AT1G01010.1`}
                  </Code>
                  <Text size="sm" c="dimmed">
                    Supported feature types include gene, mRNA, exon, CDS, and
                    UTR (five_prime_UTR, three_prime_UTR).
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="file-size">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconFileDescription size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Are there any file size limitations?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Text>
                  Large files can be processed within browser memory limits.
                  However, very large files (several hundred MB or more) may
                  take longer to process. For optimal performance, we recommend
                  uploading files containing only the genes/transcripts you
                  need.
                </Text>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Features */}
            <Accordion.Item value="search-gene">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconSettings size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>How do I search for genes?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>
                    After uploading a file, you can search for the following in
                    the search box:
                  </Text>
                  <List spacing="xs">
                    <List.Item>Gene ID (e.g., AT1G01010)</List.Item>
                    <List.Item>Transcript ID (e.g., AT1G01010.1)</List.Item>
                  </List>
                  <Text>
                    As you type, suggestions will appear automatically. Fuzzy
                    search is supported, so you can search even if you don't
                    know the exact ID.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="color-settings">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconPalette size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Can I customize colors?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>
                    Yes, you can customize the colors of the following elements
                    in the preview screen:
                  </Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>UTRs:</Text> Color of 5' and 3'
                      untranslated regions
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Exons:</Text> Color of coding regions
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>Introns:</Text> Color of intron lines
                    </List.Item>
                  </List>
                  <Text size="sm" c="dimmed">
                    After changing colors, click the "Regenerate" button to
                    update the diagram.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Export */}
            <Accordion.Item value="export-formats">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconFileDescription size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>What export formats are available?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="md">
                  <Text>You can export in the following two formats:</Text>
                  <List spacing="md">
                    <List.Item>
                      <Text fw={500}>SVG (Scalable Vector Graphics):</Text>
                      <List withPadding>
                        <List.Item>No quality loss when scaling</List.Item>
                        <List.Item>
                          Editable in Adobe Illustrator or Inkscape
                        </List.Item>
                        <List.Item>
                          Perfect for scientific publications
                        </List.Item>
                      </List>
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>PNG (Portable Network Graphics):</Text>
                      <List withPadding>
                        <List.Item>Raster image format</List.Item>
                        <List.Item>
                          Adjustable DPI (72, 150, 300, 600)
                        </List.Item>
                        <List.Item>
                          Transparent or white background options
                        </List.Item>
                        <List.Item>
                          Great for presentations and web use
                        </List.Item>
                      </List>
                    </List.Item>
                  </List>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="export-settings">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconSettings size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>How do I export at high resolution?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>
                    When exporting as PNG, you can adjust the DPI settings:
                  </Text>
                  <List spacing="xs">
                    <List.Item>
                      <Text fw={500}>72 DPI:</Text> For web display
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>150 DPI:</Text> Standard print quality
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>300 DPI:</Text> High-quality print
                      (recommended for papers)
                    </List.Item>
                    <List.Item>
                      <Text fw={500}>600 DPI:</Text> Highest quality (for
                      publications)
                    </List.Item>
                  </List>
                  <Text size="sm" c="dimmed" mt="xs">
                    For SVG format, resolution is not a concern as it's a vector
                    image.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Troubleshooting */}
            <Accordion.Item value="upload-error">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconHelp size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>I'm getting an error when uploading a file</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>Please check the following:</Text>
                  <List spacing="xs">
                    <List.Item>Verify the file is in GFF3 format</List.Item>
                    <List.Item>
                      Ensure the file extension is .gff or .gff3
                    </List.Item>
                    <List.Item>
                      Confirm the file content is properly formatted
                      (tab-delimited)
                    </List.Item>
                    <List.Item>
                      Check that required fields (seqid, source, type, start,
                      end, score, strand, phase, attributes) are present
                    </List.Item>
                  </List>
                  <Text size="sm" c="dimmed" mt="xs">
                    If the problem persists, try testing with a sample file.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="no-results">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconHelp size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Genes are not showing up in search results</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>Possible causes:</Text>
                  <List spacing="xs">
                    <List.Item>
                      GFF3 file does not contain mRNA features
                    </List.Item>
                    <List.Item>ID attributes are not properly set</List.Item>
                    <List.Item>
                      Parent attributes are not correctly linked
                    </List.Item>
                  </List>
                  <Text mt="xs">
                    This tool builds gene structures based on mRNA features.
                    Please ensure your GFF3 file has the proper hierarchy (gene
                    → mRNA → exon/CDS/UTR).
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Other */}
            <Accordion.Item value="browser-support">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconSettings size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>What browsers are recommended?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  <Text>This tool works on modern browsers:</Text>
                  <List spacing="xs">
                    <List.Item>Google Chrome (recommended)</List.Item>
                    <List.Item>Mozilla Firefox</List.Item>
                    <List.Item>Microsoft Edge</List.Item>
                    <List.Item>Safari</List.Item>
                  </List>
                  <Text size="sm" c="dimmed" mt="xs">
                    For the best experience, please keep your browser updated to
                    the latest version.
                  </Text>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            <Accordion.Item value="privacy">
              <Accordion.Control
                icon={
                  <ThemeIcon variant="light" radius="xl" size="lg">
                    <IconHelp size={20} />
                  </ThemeIcon>
                }
              >
                <Text fw={500}>Is my uploaded data stored?</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Text>
                  No, uploaded files are processed only in your browser and are
                  never stored on our servers. Data privacy and security are our
                  top priorities. All data is cleared when you refresh the page
                  or close the browser.
                </Text>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Card>

        <Card shadow="sm" padding="lg" radius="md" withBorder>
          <Stack gap="md">
            <Title order={3}>Need More Help?</Title>
            <Text c="dimmed">
              If the above doesn't resolve your issue, please check the Docs
              page for detailed documentation or ask questions on GitHub issues.
            </Text>
            <Group gap="md">
              <Anchor
                href="https://github.com/bvv-1/gene-structure"
                target="_blank"
                rel="noopener noreferrer"
                c="dark"
              >
                <Group gap="xs">
                  <IconBrandGithub size={20} />
                  <Text fw={500}>View on GitHub</Text>
                </Group>
              </Anchor>
              <Anchor
                href="https://github.com/bvv-1/gene-structure/issues"
                target="_blank"
                rel="noopener noreferrer"
                c="dark"
              >
                <Group gap="xs">
                  <IconHelp size={20} />
                  <Text fw={500}>Report an Issue</Text>
                </Group>
              </Anchor>
            </Group>
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
}
