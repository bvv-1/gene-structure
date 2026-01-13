from .models import GeneFeature, GeneStructure


def parse_gff_for_transcript(gff_file, transcript_id):
    gene_structure = None
    with open(gff_file) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) != 9:
                continue
            seqid, source, feature_type, start, end, score, strand, phase, attributes = parts
            if f"Parent={transcript_id}" not in attributes and f"ID={transcript_id}" not in attributes:
                continue
            if gene_structure is None:
                gene_structure = GeneStructure(transcript_id, seqid, strand)
            if strand == '+':
                feature = GeneFeature(seqid, int(start), int(end), feature_type, strand)
            elif strand == '-':
                feature = GeneFeature(seqid, int(end)*-1, int(start)*-1, feature_type, strand)
            gene_structure.add_feature(feature)
    return gene_structure
