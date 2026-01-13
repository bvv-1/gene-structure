type ResponseType = "json" | "blob" | "text";

// orval SWR client request format
export interface OrvalRequestConfig {
  url: string;
  method: string;
  headers?: Record<string, string>;
  data?: unknown;
  params?: Record<string, unknown>;
}

export interface CustomRequestInit extends RequestInit {
  responseType?: ResponseType;
}

// Custom fetcher compatible with orval SWR client
export async function customFetch<T>(
  config: OrvalRequestConfig,
  options?: CustomRequestInit,
): Promise<T> {
  const { url, method, headers, data } = config;
  const { responseType = "json", ...fetchOptions } = options || {};

  const response = await fetch(url, {
    method,
    headers: headers as HeadersInit,
    body: data ? JSON.stringify(data) : undefined,
    ...fetchOptions,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      status: response.status,
      data: errorData,
      response,
    };
  }

  let responseData: unknown;
  if (responseType === "blob") {
    responseData = await response.blob();
  } else if (responseType === "text") {
    responseData = await response.text();
  } else {
    responseData = await response.json();
  }

  return responseData as T;
}

export default customFetch;

// Blob response specific fetch for SVG generation
import type {
  GeneStructureRequest,
  HTTPValidationError,
} from "./generated/model";

export type GenerateSvgBlobResult = {
  blob: Blob;
  status: number;
};

export type GenerateSvgBlobError = {
  status: number;
  data: HTTPValidationError;
  response: Response;
};

export async function generateGeneStructureSvgBlob(
  request: GeneStructureRequest,
): Promise<GenerateSvgBlobResult> {
  const url = "/api/py/generate-gene-structure-svg";

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      status: response.status,
      data: errorData,
      response,
    } as GenerateSvgBlobError;
  }

  const blob = await response.blob();
  return {
    blob,
    status: response.status,
  };
}
