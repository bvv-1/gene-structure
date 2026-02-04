"use client";

import { Alert, Loader, Stack, Text } from "@mantine/core";
import { IconAlertCircle } from "@tabler/icons-react";
import { useEffect, useRef, useState } from "react";
import {
  ReactSVGPanZoom,
  TOOL_NONE,
  type Tool,
  type Value,
} from "react-svg-pan-zoom";
import { useSvgContent } from "../lib/api";

interface SvgViewerProps {
  svgUrl?: string;
  width?: number;
  height?: number;
}

export default function SvgViewer({
  svgUrl,
  width = 800,
  height = 600,
}: SvgViewerProps) {
  const [tool, setTool] = useState<Tool>(TOOL_NONE);
  const [value, setValue] = useState<Value>({} as Value);
  const viewerRef = useRef<ReactSVGPanZoom>(null);

  // SWR hook for fetching SVG content
  const { svgContent, error, isLoading } = useSvgContent(svgUrl);

  // Fit to viewer when SVG content changes (external system sync - appropriate use of useEffect)
  useEffect(() => {
    if (viewerRef.current && svgContent) {
      viewerRef.current.fitToViewer();
    }
  }, [svgContent]);

  // Placeholder container style
  const placeholderStyle = {
    width,
    height,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid #ccc",
    borderRadius: "4px",
    backgroundColor: "#f5f5f5",
  };

  // Initial state: no URL provided
  if (!svgUrl) {
    return (
      <div style={placeholderStyle}>
        <Text c="dimmed">No SVG content loaded</Text>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div style={placeholderStyle}>
        <Stack align="center" gap="sm">
          <Loader size="md" />
          <Text c="dimmed">Loading SVG...</Text>
        </Stack>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={placeholderStyle}>
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="Failed to load SVG"
          color="red"
          variant="light"
        >
          {error.message || "An unknown error occurred"}
        </Alert>
      </div>
    );
  }

  // Empty content state
  if (!svgContent) {
    return (
      <div
        style={{
          width,
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "1px solid #ccc",
          borderRadius: "4px",
          backgroundColor: "#f5f5f5",
        }}
      >
        <p style={{ color: "#666" }}>No SVG content loaded</p>
      </div>
    );
  }

  return (
    <ReactSVGPanZoom
      ref={viewerRef}
      width={width}
      height={height}
      tool={tool}
      onChangeTool={setTool}
      value={value}
      onChangeValue={setValue}
      detectAutoPan={false}
      background="#ffffff"
    >
      {/* biome-ignore lint/a11y/noSvgWithoutTitle: <explanation> */}
      <svg width={width} height={height}>
        {/* biome-ignore lint/security/noDangerouslySetInnerHtml: <explanation> */}
        <g dangerouslySetInnerHTML={{ __html: svgContent }} />
      </svg>
    </ReactSVGPanZoom>
  );
}
