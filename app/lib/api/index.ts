// Re-export generated types from orval
export * from "./generated/model";

// Re-export generated API functions
export * from "./generated/default/default";

// Custom fetch for blob responses
export {
  customFetch,
  generateGeneStructureSvgBlob,
  type GenerateSvgBlobResult,
  type GenerateSvgBlobError,
} from "./custom-fetch";
