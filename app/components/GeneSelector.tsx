"use client";

import {
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Group,
  Stack,
  Text,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconGripVertical,
  IconTrash,
  IconX,
} from "@tabler/icons-react";
import Fuse from "fuse.js";
import { useMemo, useState } from "react";
import type { SelectedTranscriptItem } from "../types/variant";
import type { GeneStructureInfo } from "../utils/gff";

interface GeneSelectorProps {
  geneStructures: GeneStructureInfo[];
  selectedItems: SelectedTranscriptItem[];
  onSelectionChange: (items: SelectedTranscriptItem[]) => void;
  maxSelection?: number;
  disabled?: boolean;
}

interface SortableItemProps {
  item: SelectedTranscriptItem;
  onRemove: (uid: string) => void;
  disabled?: boolean;
}

function SortableItem({ item, onRemove, disabled }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.uid, disabled });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    borderRadius: "4px",
    border: "1px solid var(--mantine-color-gray-3)",
    cursor: disabled ? "default" : "grab",
  };

  return (
    <Box
      ref={setNodeRef}
      style={style}
      {...attributes}
      p="xs"
      mb="xs"
      bg="gray.0"
    >
      <Group justify="space-between" wrap="nowrap">
        <Group wrap="nowrap" gap="xs">
          <Box
            {...listeners}
            style={{
              cursor: disabled ? "not-allowed" : "grab",
              display: "flex",
              alignItems: "center",
            }}
          >
            <IconGripVertical size={16} color="gray" />
          </Box>
          <Stack gap={0}>
            <Text size="sm" style={{ fontFamily: "monospace" }} fw={500}>
              {item.transcript_id}
            </Text>
          </Stack>
        </Group>
        <Button
          size="compact-xs"
          variant="subtle"
          color="red"
          onClick={() => onRemove(item.uid)}
          disabled={disabled}
        >
          <IconX size={14} />
        </Button>
      </Group>
    </Box>
  );
}

export function GeneSelector({
  geneStructures,
  selectedItems,
  onSelectionChange,
  maxSelection = 30,
  disabled = false,
}: GeneSelectorProps) {
  const [input, setInput] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const fuseInstance = useMemo(() => {
    return new Fuse(geneStructures, {
      keys: ["transcript_id", "attributes.Parent"],
      threshold: 0.5,
    });
  }, [geneStructures]);

  const autocompleteOptions = useMemo(() => {
    if (!input) {
      return geneStructures.slice(0, 50).map((gs) => gs.transcript_id);
    }

    const results = fuseInstance.search(input);
    return results.slice(0, 50).map((r) => r.item.transcript_id);
  }, [geneStructures, fuseInstance, input]);

  const handleSelect = (value: string) => {
    if (value && selectedItems.length < maxSelection) {
      const newItem: SelectedTranscriptItem = {
        uid: `${value}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        transcript_id: value,
        snps: [],
        insertions: [],
        deletion_regions: [],
        protein_domains: [],
      };
      onSelectionChange([...selectedItems, newItem]);
    }
    // MantineのAutocompleteは選択後に内部で値を設定するため、
    // setTimeoutで処理完了後にクリアする
    setTimeout(() => setInput(""), 0);
  };

  const handleRemove = (uid: string) => {
    onSelectionChange(selectedItems.filter((item) => item.uid !== uid));
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = selectedItems.findIndex(
        (item) => item.uid === active.id,
      );
      const newIndex = selectedItems.findIndex((item) => item.uid === over.id);
      onSelectionChange(arrayMove(selectedItems, oldIndex, newIndex));
    }
  };

  const isAtLimit = selectedItems.length >= maxSelection;

  return (
    <Stack gap="sm">
      <Autocomplete
        label="Transcript ID"
        placeholder={
          isAtLimit
            ? `Maximum ${maxSelection} genes selected`
            : "Search and select genes..."
        }
        data={autocompleteOptions}
        value={input}
        onChange={setInput}
        onOptionSubmit={handleSelect}
        disabled={disabled || isAtLimit}
        limit={50}
      />

      {isAtLimit && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          color="orange"
          variant="light"
        >
          Maximum of {maxSelection} genes can be selected.
        </Alert>
      )}

      {selectedItems.length > 0 && (
        <>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">
              Selected: {selectedItems.length} / {maxSelection}
            </Text>
            <Button
              size="compact-xs"
              variant="subtle"
              color="red"
              leftSection={<IconTrash size={14} />}
              onClick={() => onSelectionChange([])}
              disabled={disabled}
            >
              Clear All
            </Button>
          </Group>

          <Text size="xs" c="dimmed">
            Drag to reorder
          </Text>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={selectedItems.map((item) => item.uid)}
              strategy={verticalListSortingStrategy}
            >
              <Box
                style={{
                  maxHeight: "300px",
                  overflowY: "auto",
                  padding: "4px",
                }}
              >
                {selectedItems.map((item) => (
                  <SortableItem
                    key={item.uid}
                    item={item}
                    onRemove={handleRemove}
                    disabled={disabled}
                  />
                ))}
              </Box>
            </SortableContext>
          </DndContext>
        </>
      )}
    </Stack>
  );
}
