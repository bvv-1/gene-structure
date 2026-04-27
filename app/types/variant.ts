import type { GeneStructureInfo as ApiGeneStructureInfo } from "../lib/api";

export type InsertionInput = {
  id: string;
  position: number | undefined;
  length: number | undefined;
  color: string;
};

export type SnpInput = {
  id: string;
  position: number | undefined;
  color: string;
};

export type DeletionRegionInput = {
  id: string;
  start: number | undefined;
  end: number | undefined;
  color: string;
};

export type ProteinDomainInput = {
  id: string;
  start: number | undefined;
  end: number | undefined;
  name: string;
};

export type SelectedTranscriptItem = {
  uid: string;
  transcript_id: string;
  snps: SnpInput[];
  insertions: InsertionInput[];
  deletion_regions: DeletionRegionInput[];
  protein_domains: ProteinDomainInput[];
};
