import { defineConfig } from "orval";

export default defineConfig({
  geneStructure: {
    input: {
      target: "./openapi.json",
    },
    output: {
      mode: "tags-split",
      target: "./app/lib/api/generated",
      schemas: "./app/lib/api/generated/model",
      client: "fetch",
      override: {
        mutator: {
          path: "./app/lib/api/custom-fetch.ts",
          name: "customFetch",
        },
      },
    },
  },
});
