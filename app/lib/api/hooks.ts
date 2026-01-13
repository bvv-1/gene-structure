import useSWR from "swr";

// Type definitions
export type GffFileOption = {
  value: string;
  label: string;
  group: string;
};

export type ListGffsResponse = {
  files: GffFileOption[];
};

export type GroupedGffOptions = {
  group: string;
  items: { value: string; label: string }[];
}[];

// Fetchers
const jsonFetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.status}`);
  }
  return response.json();
};

const textFetcher = async (url: string): Promise<string> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.status}`);
  }
  return response.text();
};

// Transform list-gffs response to grouped format for Mantine Select
const transformToGroupedOptions = (
  data: ListGffsResponse | undefined,
): GroupedGffOptions => {
  if (!data?.files) return [];

  const groupMap = new Map<string, { value: string; label: string }[]>();

  for (const file of data.files) {
    const group = file.group || "Other";
    if (!groupMap.has(group)) {
      groupMap.set(group, []);
    }
    groupMap.get(group)?.push({ value: file.value, label: file.label });
  }

  const result: GroupedGffOptions = [];
  for (const [group, items] of groupMap) {
    result.push({ group, items });
  }

  return result;
};

/**
 * Hook to fetch preset GFF files list
 */
export function useListGffs() {
  const { data, error, isLoading } = useSWR<ListGffsResponse>(
    "/api/list-gffs",
    jsonFetcher,
  );

  return {
    data,
    groupedOptions: transformToGroupedOptions(data),
    error,
    isLoading,
  };
}

/**
 * Hook to fetch SVG content from a URL
 */
export function useSvgContent(svgUrl: string | undefined) {
  const { data, error, isLoading } = useSWR<string>(
    svgUrl ?? null,
    textFetcher,
  );

  return {
    svgContent: data ?? "",
    error,
    isLoading,
  };
}
