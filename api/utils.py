from __future__ import annotations
from typing import List, Tuple

from .models import GeneFeature, GeneStructure, GeneStructureInfo, Insertion, Snp, Deletion


def get_anchor_from_gene_info(gene_info: GeneStructureInfo) -> int:
    """
    GeneStructureInfoからanchor（基準座標）を計算する
    GeneStructure.to_relative()と同じロジックを使用

    Args:
        gene_info: フロントエンドから送られたGeneStructureInfo

    Returns:
        anchor座標（プラス鎖なら最小開始位置、マイナス鎖なら最大終了位置）
    """
    all_coords = []
    for exon in gene_info.exons:
        all_coords.append(exon.start)
        all_coords.append(exon.end)
    for cds in gene_info.cds:
        all_coords.append(cds.start)
        all_coords.append(cds.end)
    for utr in gene_info.five_prime_utrs:
        all_coords.append(utr.start)
        all_coords.append(utr.end)
    for utr in gene_info.three_prime_utrs:
        all_coords.append(utr.start)
        all_coords.append(utr.end)

    if not all_coords:
        return 0
    
    if gene_info.strand == '-':
        return max(all_coords)
    else:
        return min(all_coords)


def convert_absolute_to_relative(
    absolute_coord: int,
    anchor: int,
    strand: str
) -> int:
    """
    絶対座標（染色体座標）を相対座標に変換する

    Args:
        absolute_coord: 絶対座標（染色体座標）
        anchor: 基準となるゲノム座標（通常はCDS/exonの開始位置）
        strand: ストランド方向（'+' または '-'）

    Returns:
        相対座標（1-based）
    """
    if strand == '-':
        # マイナスストランドの場合、座標は反転している
        # 絶対座標が大きいほど相対座標は小さくなる
        return anchor - absolute_coord + 1
    else:
        # プラスストランドの場合
        return absolute_coord - anchor + 1


def convert_coordinates_to_relative(
    deletion_regions: List[Deletion],
    snps: List[Snp],
    insertions: List[Insertion],
    anchor: int,
    strand: str
) -> Tuple[List[Deletion], List[Snp], List[Insertion]]:
    """
    絶対座標を相対座標に一括変換する

    Args:
        deletion_regions: 絶対座標での削除領域リスト
        snps: 絶対座標でのSNP位置リスト
        insertions: 絶対座標での挿入リスト
        anchor: 基準となるゲノム座標
        strand: ストランド方向

    Returns:
        相対座標に変換された (deletion_regions, snps, insertions) のタプル
    """
    # 削除領域の変換
    converted_deletion_regions = []
    for region in deletion_regions:
        start_rel = convert_absolute_to_relative(region.start, anchor, strand)
        end_rel = convert_absolute_to_relative(region.end, anchor, strand)
        # マイナスストランドの場合、startとendが逆転する可能性があるので正規化
        if start_rel > end_rel:
            start_rel, end_rel = end_rel, start_rel
        converted_deletion_regions.append(Deletion(start=start_rel, end=end_rel, color=region.color))

    # SNP位置の変換
    converted_snps = [
        Snp(position=convert_absolute_to_relative(snp.position, anchor, strand), color=snp.color)
        for snp in snps
    ]

    # 挿入位置の変換
    converted_insertions = [
        Insertion(
            position=convert_absolute_to_relative(ins.position, anchor, strand),
            length=ins.length,
            color=ins.color
        )
        for ins in insertions
    ]

    return converted_deletion_regions, converted_snps, converted_insertions


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

    # 正規化（exon + CDS/UTR の重複を解消 + イントロン追加）
    gene.normalize_features()

    # 相対座標に変換
    gene.to_relative()

    return gene


def build_gene_structure_no_relative(gene_info: GeneStructureInfo) -> GeneStructure:
    """
    GeneStructureInfoからGeneStructureオブジェクトを構築する
    （座標変換なし、ゲノム座標をそのまま保持）

    Args:
        gene_info: フロントエンドから送られたGeneStructureInfo

    Returns:
        構築されたGeneStructureオブジェクト（イントロン追加済み、ゲノム座標のまま）
    """
    gene = GeneStructure(
        gene_id=gene_info.transcript_id,
        seqid=gene_info.seq_id or "",
        strand=gene_info.strand or "+"
    )

    # Exonを追加（ゲノム座標をそのまま使用）
    for exon in gene_info.exons:
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
        feature = GeneFeature(
            gene_info.seq_id or "",
            utr.start,
            utr.end,
            'three_prime_UTR',
            gene_info.strand or "+",
            {}
        )
        gene.add_feature(feature)

    # 正規化（exon + CDS/UTR の重複を解消 + イントロン追加）
    gene.normalize_features()

    # 注意: to_relative() は呼ばない

    return gene
