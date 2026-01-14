"use client";

import { Alert, Group, NumberInput, Select, Stack, Text } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";

interface RegionFilter {
  seqId: string;
  start: string;
  end: string;
}

interface RegionSelectorProps {
  seqIds: string[];
  regionFilter: RegionFilter;
  onFilterChange: (filter: RegionFilter) => void;
  matchCount: number;
  maxSelection?: number;
}

export function RegionSelector({
  seqIds,
  regionFilter,
  onFilterChange,
  matchCount,
  maxSelection = 30,
}: RegionSelectorProps) {
  const startNum = Number.parseInt(regionFilter.start) || 0;
  const endNum = Number.parseInt(regionFilter.end) || 0;
  const isValidRange = startNum > 0 && endNum > 0 && startNum < endNum;
  const isOverLimit = matchCount > maxSelection;

  return (
    <Stack gap="md">
      <Select
        label="Chromosome"
        placeholder="染色体を選択"
        data={seqIds}
        value={regionFilter.seqId}
        onChange={(value) =>
          onFilterChange({ ...regionFilter, seqId: value || "" })
        }
        searchable
        clearable
      />

      <Group grow>
        <NumberInput
          label="Start"
          placeholder="開始座標"
          value={regionFilter.start ? Number.parseInt(regionFilter.start) : ""}
          onChange={(value) =>
            onFilterChange({ ...regionFilter, start: String(value || "") })
          }
          min={1}
          allowNegative={false}
        />

        <NumberInput
          label="End"
          placeholder="終了座標"
          value={regionFilter.end ? Number.parseInt(regionFilter.end) : ""}
          onChange={(value) =>
            onFilterChange({ ...regionFilter, end: String(value || "") })
          }
          min={1}
          allowNegative={false}
        />
      </Group>

      {regionFilter.seqId &&
        isValidRange &&
        (matchCount === 0 ? (
          <Alert icon={<IconInfoCircle size={16} />} color="yellow">
            この領域にはトランスクリプトがありません
          </Alert>
        ) : isOverLimit ? (
          <Alert icon={<IconInfoCircle size={16} />} color="red">
            {matchCount}件のトランスクリプトが見つかりました（上限
            {maxSelection}件を超えています）
          </Alert>
        ) : (
          <Text size="sm" c="dimmed">
            {matchCount}件のトランスクリプトが見つかりました
          </Text>
        ))}

      {!isValidRange && regionFilter.start && regionFilter.end && (
        <Alert icon={<IconInfoCircle size={16} />} color="red">
          開始座標は終了座標より小さくしてください
        </Alert>
      )}
    </Stack>
  );
}
