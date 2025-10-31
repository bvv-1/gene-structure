"use client";

import { useEffect, useRef, useState } from "react";
import {
  ReactSVGPanZoom,
  TOOL_NONE,
  type Tool,
  type Value,
} from "react-svg-pan-zoom";

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
  const [value, setValue] = useState<Value | null>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const viewerRef = useRef<ReactSVGPanZoom>(null);

  useEffect(() => {
    if (!svgUrl) {
      setSvgContent("");
      return;
    }

    const loadSvg = async () => {
      try {
        const response = await fetch(svgUrl);
        const text = await response.text();
        setSvgContent(text);
      } catch (error) {
        console.error("Error loading SVG:", error);
        setSvgContent("");
      }
    };

    loadSvg();
  }, [svgUrl]);

  useEffect(() => {
    if (viewerRef.current && svgContent) {
      viewerRef.current.fitToViewer();
    }
  }, [svgContent]);

  if (!svgUrl || !svgContent) {
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
        <p style={{ color: "#666" }}>SVGコンテンツが読み込まれていません</p>
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
