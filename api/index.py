from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    CoordinateMode,
    GeneFeature,
    GeneStructure,
    GeneStructureRequest,
    MultiGeneStructureRequest,
    RegionGeneStructureRequest,
)
from .drawer import draw_gene_structure, draw_multiple_gene_structures, draw_region_gene_structures, DEFAULT_COLORS
from .utils import (
    build_gene_structure,
    build_gene_structure_no_relative,
    convert_coordinates_to_relative,
    get_anchor_from_gene_info,
)


### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/py/generate-gene-structure-svg")
async def generate_gene_structure_svg(request: GeneStructureRequest):
    """
    フロントエンドから送られたGeneStructureInfoを基に遺伝子構造を描画するエンドポイント
    """
    try:
        # GeneStructureオブジェクトを作成
        gene_info = request.gene_structure
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

        # プロテインドメインを追加（指定されている場合）
        for pd in request.protein_domains:
            gene.add_domain_from_protein_coords(pd.start, pd.end, pd.name)

        # ドメインを追加
        if request.domains:
            gene.add_domains(request.domains)
            print("Added domains:", request.domains)

        # 座標モードに応じた変換処理
        deletion_regions = request.deletion_regions
        snps = request.snps
        insertions = request.insertions

        if request.coordinate_mode == CoordinateMode.ABSOLUTE:
            # 絶対座標を相対座標に変換
            anchor = get_anchor_from_gene_info(gene_info)
            strand = gene_info.strand or "+"
            deletion_regions, snps, insertions = convert_coordinates_to_relative(
                deletion_regions,
                snps,
                insertions,
                anchor,
                strand
            )

        # SNPsを追加
        if snps:
            gene.add_snps(snps)

        # Insertionsを追加
        if insertions:
            gene.add_insertions(insertions)

        # デリーション処理
        if deletion_regions:
            gene.update_features_with_deletions(deletion_regions)
            print("Applied deletions:", deletion_regions)

        # SVGを生成（DrawSettingsから色を取得）
        draw_settings = request.draw_settings
        svg_content = draw_gene_structure(
            gene,
            utr_color=draw_settings.utr_color,
            exon_color=draw_settings.exon_color,
            line_color=draw_settings.line_color,
            domain_color=DEFAULT_COLORS['domain_color']
        )

        return Response(content=svg_content, media_type="image/svg+xml")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/py/generate-multi-gene-structure-svg")
async def generate_multi_gene_structure_svg(request: MultiGeneStructureRequest):
    """
    複数の遺伝子構造を1つのSVGに縦並びで描画するエンドポイント
    """
    try:
        genes = []
        labels = []

        # 座標モードがABSOLUTEの場合、最初のトランスクリプトのanchorを使用
        anchor = None
        first_strand = "+"
        if request.coordinate_mode == CoordinateMode.ABSOLUTE and request.gene_structures:
            first_gene_info = request.gene_structures[0]
            anchor = get_anchor_from_gene_info(first_gene_info)
            first_strand = first_gene_info.strand or "+"

        for gene_info in request.gene_structures:
            # 共通関数でGeneStructureを構築
            gene = build_gene_structure(gene_info)

            # プロテインドメインを追加
            for pd in request.protein_domains:
                gene.add_domain_from_protein_coords(pd.start, pd.end, pd.name)

            # ドメインを追加
            if request.domains:
                gene.add_domains(request.domains)

            # 座標モードに応じた変換処理
            deletion_regions = request.deletion_regions
            snps = request.snps
            insertions = request.insertions

            if request.coordinate_mode == CoordinateMode.ABSOLUTE and anchor is not None:
                # 絶対座標を相対座標に変換（最初のトランスクリプトのanchorを使用）
                deletion_regions, snps, insertions = convert_coordinates_to_relative(
                    deletion_regions,
                    snps,
                    insertions,
                    anchor,
                    first_strand
                )

            # SNPsを追加
            if snps:
                gene.add_snps(snps)

            # Insertionsを追加
            if insertions:
                gene.add_insertions(insertions)

            # デリーション処理
            if deletion_regions:
                gene.update_features_with_deletions(deletion_regions)

            genes.append(gene)
            labels.append(gene_info.transcript_id)

        # SVGを生成
        draw_settings = request.draw_settings
        svg_content = draw_multiple_gene_structures(
            genes=genes,
            labels=labels,
            show_labels=request.show_labels,
            show_scale=request.show_scale,
            gene_spacing=request.gene_spacing,
            label_spacing=request.label_spacing,
            utr_color=draw_settings.utr_color,
            exon_color=draw_settings.exon_color,
            line_color=draw_settings.line_color,
            domain_color=DEFAULT_COLORS['domain_color'],
            coordinate_mode=request.coordinate_mode.value if hasattr(request.coordinate_mode, 'value') else request.coordinate_mode,
            anchor=anchor if anchor is not None else 0,
            strand=first_strand
        )

        return Response(content=svg_content, media_type="image/svg+xml")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/py/generate-region-gene-structure-svg")
async def generate_region_gene_structure_svg(request: RegionGeneStructureRequest):
    """
    領域指定による複数遺伝子構造を共通座標軸上に描画するエンドポイント
    """
    try:
        genes = []
        labels = []

        for gene_info in request.gene_structures:
            # to_relative()を呼ばないバージョンでGeneStructureを構築
            gene = build_gene_structure_no_relative(gene_info)
            genes.append(gene)
            labels.append(gene_info.transcript_id)

        # SVGを生成
        draw_settings = request.draw_settings
        svg_content = draw_region_gene_structures(
            genes=genes,
            labels=labels,
            region_start=request.region_start,
            region_end=request.region_end,
            show_labels=request.show_labels,
            gene_spacing=request.gene_spacing,
            label_spacing=request.label_spacing,
            utr_color=draw_settings.utr_color,
            exon_color=draw_settings.exon_color,
            line_color=draw_settings.line_color
        )

        return Response(content=svg_content, media_type="image/svg+xml")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "health check"}
