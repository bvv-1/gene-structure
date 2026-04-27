"use client";

import {
  Accordion,
  Box,
  Button,
  ColorInput,
  Divider,
  Group,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { IconPlus, IconX } from "@tabler/icons-react";
import { CoordinateMode } from "../lib/api";
import type { SelectedTranscriptItem } from "../types/variant";
import { DelayedNumberInput } from "./DelayedNumberInput";

interface TranscriptVariantEditorProps {
  items: SelectedTranscriptItem[];
  onUpdate: (uid: string, newItem: SelectedTranscriptItem) => void;
  disabled?: boolean;
  coordinateMode?: CoordinateMode;
}

export function TranscriptVariantEditor({
  items,
  onUpdate,
  disabled = false,
  coordinateMode = CoordinateMode.relative,
}: TranscriptVariantEditorProps) {
  const isAbsolute = coordinateMode === CoordinateMode.absolute;
  const posPlaceholder = isAbsolute ? "Chr Pos" : "Rel Pos";
  const updateItem = (
    uid: string,
    item: SelectedTranscriptItem,
    updates: Partial<SelectedTranscriptItem>,
  ) => {
    onUpdate(uid, { ...item, ...updates });
  };

  return (
    <Stack gap="sm">
      <Accordion variant="separated">
        {items.map((item) => (
          <Accordion.Item key={item.uid} value={item.uid}>
            <Accordion.Control>
              <Stack gap={0}>
                <Text size="sm" style={{ fontFamily: "monospace" }} fw={500}>
                  {item.transcript_id}
                </Text>
              </Stack>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="sm" p="xs">
                <Divider label="SNPs" labelPosition="left" />
                <Stack gap="xs">
                  {item.snps.map((snp, idx) => (
                    <Group key={snp.id || idx} gap="xs">
                      <DelayedNumberInput
                        placeholder={posPlaceholder}
                        value={snp.position}
                        onChange={(val) => {
                          const newSnps = [...item.snps];
                          newSnps[idx].position =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, { snps: newSnps });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <ColorInput
                        value={snp.color}
                        onChange={(val) => {
                          const newSnps = [...item.snps];
                          newSnps[idx].color = val;
                          updateItem(item.uid, item, { snps: newSnps });
                        }}
                        size="xs"
                        format="hex"
                        withEyeDropper={false}
                        style={{ width: 100 }}
                      />
                      <Button
                        size="compact-xs"
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          updateItem(item.uid, item, {
                            snps: item.snps.filter((_, i) => i !== idx),
                          });
                        }}
                      >
                        <IconX size={14} />
                      </Button>
                    </Group>
                  ))}
                  <Button
                    variant="light"
                    size="compact-xs"
                    leftSection={<IconPlus size={14} />}
                    onClick={() => {
                      updateItem(item.uid, item, {
                        snps: [
                          ...item.snps,
                          {
                            id: Math.random().toString(36).substr(2, 9),
                            position: undefined,
                            color: "#000000",
                          },
                        ],
                      });
                    }}
                    disabled={disabled}
                  >
                    Add SNP
                  </Button>
                </Stack>

                <Divider label="Insertions" labelPosition="left" />
                <Stack gap="xs">
                  {item.insertions.map((ins, idx) => (
                    <Group key={ins.id || idx} gap="xs" align="flex-end">
                      <DelayedNumberInput
                        label="Pos"
                        value={ins.position}
                        onChange={(val) => {
                          const newIns = [...item.insertions];
                          newIns[idx].position =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, { insertions: newIns });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <DelayedNumberInput
                        label="Len"
                        value={ins.length}
                        onChange={(val) => {
                          const newIns = [...item.insertions];
                          newIns[idx].length =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, { insertions: newIns });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <ColorInput
                        value={ins.color}
                        onChange={(val) => {
                          const newIns = [...item.insertions];
                          newIns[idx].color = val;
                          updateItem(item.uid, item, { insertions: newIns });
                        }}
                        size="xs"
                        format="hex"
                        withEyeDropper={false}
                        style={{ width: 100 }}
                      />
                      <Button
                        size="compact-xs"
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          updateItem(item.uid, item, {
                            insertions: item.insertions.filter(
                              (_, i) => i !== idx,
                            ),
                          });
                        }}
                      >
                        <IconX size={14} />
                      </Button>
                    </Group>
                  ))}
                  <Button
                    variant="light"
                    size="compact-xs"
                    leftSection={<IconPlus size={14} />}
                    onClick={() => {
                      updateItem(item.uid, item, {
                        insertions: [
                          ...item.insertions,
                          {
                            id: Math.random().toString(36).substr(2, 9),
                            position: undefined,
                            length: undefined,
                            color: "#000000",
                          },
                        ],
                      });
                    }}
                    disabled={disabled}
                  >
                    Add Insertion
                  </Button>
                </Stack>

                <Divider label="Deletions" labelPosition="left" />
                <Stack gap="xs">
                  {item.deletion_regions.map((del, idx) => (
                    <Group key={del.id || idx} gap="xs" align="flex-end">
                      <DelayedNumberInput
                        label="Start"
                        value={del.start}
                        onChange={(val) => {
                          const newDels = [...item.deletion_regions];
                          newDels[idx].start =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, {
                            deletion_regions: newDels,
                          });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <DelayedNumberInput
                        label="End"
                        value={del.end}
                        onChange={(val) => {
                          const newDels = [...item.deletion_regions];
                          newDels[idx].end =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, {
                            deletion_regions: newDels,
                          });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <ColorInput
                        value={del.color}
                        onChange={(val) => {
                          const newDels = [...item.deletion_regions];
                          newDels[idx].color = val;
                          updateItem(item.uid, item, {
                            deletion_regions: newDels,
                          });
                        }}
                        size="xs"
                        format="hex"
                        withEyeDropper={false}
                        style={{ width: 100 }}
                      />
                      <Button
                        size="compact-xs"
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          updateItem(item.uid, item, {
                            deletion_regions: item.deletion_regions.filter(
                              (_, i) => i !== idx,
                            ),
                          });
                        }}
                      >
                        <IconX size={14} />
                      </Button>
                    </Group>
                  ))}
                  <Button
                    variant="light"
                    size="compact-xs"
                    leftSection={<IconPlus size={14} />}
                    onClick={() => {
                      updateItem(item.uid, item, {
                        deletion_regions: [
                          ...item.deletion_regions,
                          {
                            id: Math.random().toString(36).substr(2, 9),
                            start: undefined,
                            end: undefined,
                            color: "#000000",
                          },
                        ],
                      });
                    }}
                    disabled={disabled}
                  >
                    Add Deletion
                  </Button>
                </Stack>

                <Divider label="Protein Domains" labelPosition="left" />
                <Stack gap="xs">
                  {item.protein_domains.map((pd, idx) => (
                    <Group key={pd.id || idx} gap="xs" align="flex-end">
                      <DelayedNumberInput
                        label="Start"
                        value={pd.start}
                        onChange={(val) => {
                          const newPds = [...item.protein_domains];
                          newPds[idx].start =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, {
                            protein_domains: newPds,
                          });
                        }}
                        size="xs"
                        style={{ flex: 0.5 }}
                      />
                      <DelayedNumberInput
                        label="End"
                        value={pd.end}
                        onChange={(val) => {
                          const newPds = [...item.protein_domains];
                          newPds[idx].end =
                            val === "" ? undefined : Number(val);
                          updateItem(item.uid, item, {
                            protein_domains: newPds,
                          });
                        }}
                        size="xs"
                        style={{ flex: 0.5 }}
                      />
                      <TextInput
                        label="Name"
                        value={pd.name}
                        onChange={(e) => {
                          const newPds = [...item.protein_domains];
                          newPds[idx].name = e.currentTarget.value;
                          updateItem(item.uid, item, {
                            protein_domains: newPds,
                          });
                        }}
                        size="xs"
                        style={{ flex: 1 }}
                      />
                      <Button
                        size="compact-xs"
                        variant="subtle"
                        color="red"
                        onClick={() => {
                          updateItem(item.uid, item, {
                            protein_domains: item.protein_domains.filter(
                              (_, i) => i !== idx,
                            ),
                          });
                        }}
                      >
                        <IconX size={14} />
                      </Button>
                    </Group>
                  ))}
                  <Button
                    variant="light"
                    size="compact-xs"
                    leftSection={<IconPlus size={14} />}
                    onClick={() => {
                      updateItem(item.uid, item, {
                        protein_domains: [
                          ...item.protein_domains,
                          {
                            id: Math.random().toString(36).substr(2, 9),
                            start: undefined,
                            end: undefined,
                            name: "",
                          },
                        ],
                      });
                    }}
                    disabled={disabled}
                  >
                    Add Domain
                  </Button>
                </Stack>
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    </Stack>
  );
}
