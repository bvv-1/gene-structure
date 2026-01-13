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
  Badge,
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
import type { GeneStructureInfo } from "../utils/gff";

interface GeneSelectorProps {
  geneStructures: GeneStructureInfo[];
  selectedTranscripts: string[];
  onSelectionChange: (transcripts: string[]) => void;
  maxSelection?: number;
  disabled?: boolean;
}

interface SortableItemProps {
  id: string;
  onRemove: (id: string) => void;
  disabled?: boolean;
}

function SortableItem({ id, onRemove, disabled }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id, disabled });

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
          <Text size="sm" style={{ fontFamily: "monospace" }}>
            {id}
          </Text>
        </Group>
        <Button
          size="compact-xs"
          variant="subtle"
          color="red"
          onClick={() => onRemove(id)}
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
  selectedTranscripts,
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
      return geneStructures
        .filter((gs) => !selectedTranscripts.includes(gs.transcript_id))
        .slice(0, 50)
        .map((gs) => gs.transcript_id);
    }

    const results = fuseInstance.search(input);
    return results
      .filter((r) => !selectedTranscripts.includes(r.item.transcript_id))
      .slice(0, 50)
      .map((r) => r.item.transcript_id);
  }, [geneStructures, fuseInstance, input, selectedTranscripts]);

  const handleSelect = (value: string) => {
    if (
      value &&
      !selectedTranscripts.includes(value) &&
      selectedTranscripts.length < maxSelection
    ) {
      onSelectionChange([...selectedTranscripts, value]);
      setInput("");
    }
  };

  const handleRemove = (transcriptId: string) => {
    onSelectionChange(selectedTranscripts.filter((id) => id !== transcriptId));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = selectedTranscripts.indexOf(active.id as string);
      const newIndex = selectedTranscripts.indexOf(over.id as string);
      onSelectionChange(arrayMove(selectedTranscripts, oldIndex, newIndex));
    }
  };

  const isAtLimit = selectedTranscripts.length >= maxSelection;

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

      {selectedTranscripts.length > 0 && (
        <>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">
              Selected: {selectedTranscripts.length} / {maxSelection}
            </Text>
            <Button
              size="compact-xs"
              variant="subtle"
              color="red"
              leftSection={<IconTrash size={14} />}
              onClick={handleClearAll}
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
              items={selectedTranscripts}
              strategy={verticalListSortingStrategy}
            >
              <Box
                style={{
                  maxHeight: "300px",
                  overflowY: "auto",
                  padding: "4px",
                }}
              >
                {selectedTranscripts.map((id) => (
                  <SortableItem
                    key={id}
                    id={id}
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
