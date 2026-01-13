type ResponseType = "json" | "blob" | "text";

export interface CustomRequestInit extends RequestInit {
  responseType?: ResponseType;
}

export async function customFetch<T>(
  url: string,
  options?: CustomRequestInit,
): Promise<T> {
  const { responseType = "json", ...fetchOptions } = options || {};

  const response = await fetch(url, fetchOptions);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      status: response.status,
      data: errorData,
      response,
    };
  }

  let data: unknown;
  if (responseType === "blob") {
    data = await response.blob();
  } else if (responseType === "text") {
    data = await response.text();
  } else {
    data = await response.json();
  }

  return {
    data,
    status: response.status,
    headers: response.headers,
  } as T;
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
