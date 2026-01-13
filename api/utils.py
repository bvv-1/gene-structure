from .models import GeneFeature, GeneStructure, GeneStructureInfo


def build_gene_structure(gene_info: GeneStructureInfo) -> GeneStructure:
    """
    GeneStructureInfoからGeneStructureオブジェクトを構築する共通関数

    Args:
        gene_info: フロントエンドから送られたGeneStructureInfo

    Returns:
        構築されたGeneStructureオブジェクト（イントロン追加済み、相対座標変換済み）
    """
    gene = GeneStructure(
        gene_id=gene_info.transcript_id,
        seqid=gene_info.seq_id or "",
        strand=gene_info.strand or "+"
    )

    # Exonを追加
    for exon in gene_info.exons:
        if gene_info.strand == '-':
            feature = GeneFeature(
                gene_info.seq_id or "",
                exon.end * -1,
                exon.start * -1,
                'exon',
                gene_info.strand or "+",
                {}
            )
        else:
            feature = GeneFeature(
                gene_info.seq_id or "",
                exon.start,
                exon.end,
                'exon',
                gene_info.strand or "+",
                {}
            )
        gene.add_feature(feature)

    # CDSを追加
    for cds in gene_info.cds:
        if gene_info.strand == '-':
            feature = GeneFeature(
                gene_info.seq_id or "",
                cds.end * -1,
                cds.start * -1,
                'CDS',
                gene_info.strand or "+",
                {}
            )
        else:
            feature = GeneFeature(
                gene_info.seq_id or "",
                cds.start,
                cds.end,
                'CDS',
                gene_info.strand or "+",
                {}
            )
        gene.add_feature(feature)

    # 5' UTRを追加
    for utr in gene_info.five_prime_utrs:
        if gene_info.strand == '-':
            feature = GeneFeature(
                gene_info.seq_id or "",
                utr.end * -1,
                utr.start * -1,
                'five_prime_UTR',
                gene_info.strand or "+",
                {}
            )
        else:
            feature = GeneFeature(
                gene_info.seq_id or "",
                utr.start,
                utr.end,
                'five_prime_UTR',
                gene_info.strand or "+",
                {}
            )
        gene.add_feature(feature)

    # 3' UTRを追加
    for utr in gene_info.three_prime_utrs:
        if gene_info.strand == '-':
            feature = GeneFeature(
                gene_info.seq_id or "",
                utr.end * -1,
                utr.start * -1,
                'three_prime_UTR',
                gene_info.strand or "+",
                {}
            )
        else:
            feature = GeneFeature(
                gene_info.seq_id or "",
                utr.start,
                utr.end,
                'three_prime_UTR',
                gene_info.strand or "+",
                {}
            )
        gene.add_feature(feature)

    # イントロンを追加
    gene.add_introns()

    # 相対座標に変換
    gene.to_relative()

    return gene
