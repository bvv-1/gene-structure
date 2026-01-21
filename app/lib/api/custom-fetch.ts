// Custom fetcher compatible with orval v8 SWR client
// orval v8 passes (url: string, options: RequestInit) to the mutator
export async function customFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      status: response.status,
      data: errorData,
      response,
    };
  }

  const responseData = await response.json();

  return {
    data: responseData,
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
