from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import io
import svgwrite


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

# =====================
# 描画の色やスタイル設定
# =====================

# デフォルト色設定
DEFAULT_COLORS = {
    'utr_color': 'orange',
    'exon_color': 'lightblue',
    'line_color': 'black',
    'domain_color': 'green',
}

FEATURE_OUTLINES = {
    'exon': 'black',
    'CDS': 'black',
    'five_prime_UTR': 'black',
    'three_prime_UTR': 'black',
    'domain': 'black',
}

FEATURE_OUTLINE_ENABLED = {
    'exon': True,
    'CDS': True,
    'five_prime_UTR': True,
    'three_prime_UTR': True,
    'domain': True,
}

FEATURE_OUTLINE_WIDTHS = {
    'exon': 1,
    'CDS': 1,
    'five_prime_UTR': 1,
    'three_prime_UTR': 1,
    'domain': 1,
    'intron': 1,
}

LEFT_MARGIN = 50  # 左側マージン

# =====================
# クラス定義
# =====================

class GeneFeature:
    def __init__(self, seqid, start, end, feature_type, strand, attributes=None):
        self.seqid = seqid
        self.start = start
        self.end = end
        self.feature_type = feature_type
        self.strand = strand
        self.attributes = attributes or {}

class GeneStructure:
    def __init__(self, gene_id, seqid, strand):
        self.gene_id = gene_id
        self.seqid = seqid
        self.strand = strand
        self.features = []

    def add_feature(self, feature: GeneFeature):
        self.features.append(feature)

    def get_sorted_features(self):
        return sorted(self.features, key=lambda f: f.start, reverse=False)

    def add_introns(self):
        # exon / CDS / UTR をまとめて処理
        exon_like_list = sorted(
            [f for f in self.features if f.feature_type in ('exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR')],
            key=lambda x: x.start
        )

        for i in range(len(exon_like_list) - 1):
            intron_start = exon_like_list[i].end + 1
            intron_end = exon_like_list[i + 1].start - 1
            if intron_start <= intron_end:
                intron = GeneFeature(self.seqid, intron_start, intron_end, 'intron', self.strand, {})
                self.features.append(intron)

    def add_domains(self, domain_regions):
        for domain in domain_regions:
            start = domain['start']
            end = domain['end']
            name = domain.get('name', '')
            color = domain.get('color', '')
            domain_feature = GeneFeature(
                self.seqid,
                start,
                end,
                'domain',
                self.strand,
                attributes={'name': name, 'color': color}
            )
            self.features.append(domain_feature)

    def update_features_with_deletions(self, deletion_regions):
        new_features = []

        for i, feature in enumerate(self.features):
            f_start, f_end = feature.start, feature.end
            segments = [(f_start, f_end)]  # featureの元の範囲

            for del_start, del_end in deletion_regions:
                updated_segments = []

                if i == 0:
                    new_features.append(GeneFeature(
                        self.seqid, del_start, del_end,
                        'deletion', self.strand, {}
                    ))

                for seg_start, seg_end in segments:
                    # 削除領域と重なっていなければそのまま残す
                    if seg_end < del_start or seg_start > del_end:
                        updated_segments.append((seg_start, seg_end))
                    else:
                        # 左端が削除領域より前
                        if seg_start < del_start:
                            updated_segments.append((seg_start, del_start - 1))
                        # 右端が削除領域より後
                        if seg_end > del_end:
                            updated_segments.append((del_end + 1, seg_end))
                segments = updated_segments

            # 分割後の有効セグメントが残っていれば追加（完全削除されたらスキップ）
            for start, end in segments:
                if start <= end:
                    new_features.append(GeneFeature(
                        seqid=feature.seqid,
                        start=start,
                        end=end,
                        feature_type=feature.feature_type,
                        strand=feature.strand,
                        attributes=feature.attributes
                    ))

        # 結果を更新
        self.features = new_features

    def to_relative(self):
        cds_list = [f for f in self.features if f.feature_type in ('exon', 'CDS')]
        if not cds_list:
            return 0
        anchor = min(cds_list, key=lambda f: f.start).start
        for f in self.features:
            f.start = f.start - anchor + 1
            f.end = f.end - anchor + 1
        min_start = min(f.start for f in self.features)
        return min_start

    def add_domain_from_protein_coords(self, start_aa: int, end_aa: int, domain_name: str):
        """
        アミノ酸座標（1-based）を基に、CDSからcDNA、そしてゲノム座標へと変換して
        ドメイン領域をfeaturesに追加する。
        """
        # アミノ酸座標 → cDNA 座標（1-based）
        cdna_start = (start_aa - 1) * 3 + 1
        cdna_end = end_aa * 3

        # CDS features を取得してストランド順に並べ替え
        cds_features = [f for f in self.features if f.feature_type == 'CDS']
        if self.strand == '-':
            cds_sorted = sorted(cds_features, key=lambda f: f.start)
        else:
            cds_sorted = sorted(cds_features, key=lambda f: f.start, reverse=True)

        gdna_segments = []
        current_cdna_pos = 1

        for cds in cds_sorted:
            cds_len = cds.end - cds.start + 1
            next_cdna_pos = current_cdna_pos + cds_len - 1

            # このCDSにドメインが含まれているか？
            if next_cdna_pos < cdna_start:
                current_cdna_pos = next_cdna_pos + 1
                continue
            if current_cdna_pos > cdna_end:
                break

            # オーバーラップする部分だけを計算
            overlap_start = max(cdna_start, current_cdna_pos)
            overlap_end = min(cdna_end, next_cdna_pos)
            offset_start = overlap_start - current_cdna_pos
            offset_end = overlap_end - current_cdna_pos

            # ゲノム座標に変換
            if self.strand == '-':
                g_start = cds.start + offset_start
                g_end = cds.start + offset_end
            else:
                g_end = cds.end - offset_start
                g_start = cds.end - offset_end

            # ドメイン feature を追加
            domain_feature = GeneFeature(
                seqid=self.seqid,
                start=g_start,
                end=g_end,
                feature_type='domain',
                strand=self.strand,
                attributes={'name': domain_name}
            )
            self.features.append(domain_feature)

            current_cdna_pos = next_cdna_pos + 1

# =====================
# GFFパーサ
# =====================

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

# =====================
# 描画関数
# =====================

def draw_gene_structure(gene: GeneStructure, scale=2, extra_padding=100, shrink_factor=30.0,
                        utr_color=None, exon_color=None, line_color=None, domain_color=None):
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    min_start = gene.to_relative()
    all_features = gene.get_sorted_features()
    max_end = max(f.end / shrink_factor for f in all_features)

    shift = -min_start if min_start < 0 else 0

    canvas_width = LEFT_MARGIN + (max_end + shift / shrink_factor) * scale + extra_padding + 300
    canvas_height = 300  # 凡例分のスペースを確保

    # メモリ上にSVGを作成
    output = io.StringIO()
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))
    y_pos = 50
    height_feature = 15
    max_x_coord = LEFT_MARGIN + (max_end + shift / shrink_factor) * scale

    for feat in all_features:
        x_start = LEFT_MARGIN + (feat.start / shrink_factor + shift / shrink_factor) * scale
        x_end = LEFT_MARGIN + (feat.end / shrink_factor + shift / shrink_factor) * scale
        width = x_end - x_start

        if feat.feature_type == 'domain':
            continue

        if feat.feature_type == 'deletion':
            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill='none',
                    stroke='red',
                    stroke_dasharray="5,5",
                    stroke_width=2
                )
            )
        elif feat.feature_type in ('exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR'):
            # five_prime_UTR と three_prime_UTR は utr_color、exon/CDS は exon_color
            if feat.feature_type in ('five_prime_UTR', 'three_prime_UTR'):
                fill_color = utr_color
            else:
                fill_color = exon_color

            stroke_color = FEATURE_OUTLINES.get(feat.feature_type, 'black')
            stroke_width = FEATURE_OUTLINE_WIDTHS.get(feat.feature_type, 1)
            outline_enabled = FEATURE_OUTLINE_ENABLED.get(feat.feature_type, True)

            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill=fill_color,
                    stroke=stroke_color if outline_enabled else 'none',
                    stroke_width=stroke_width
                )
            )
        elif feat.feature_type == 'intron':
            if x_start < x_end:
                y_line = y_pos + height_feature // 2
                dwg.add(
                    dwg.line(
                        start=(x_start, y_line),
                        end=(x_end, y_line),
                        stroke=line_color,
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                    )
                )

    for feat in all_features:
        if feat.feature_type == 'domain':
            x_start = LEFT_MARGIN + (feat.start / shrink_factor + shift / shrink_factor) * scale
            x_end = LEFT_MARGIN + (feat.end / shrink_factor + shift / shrink_factor) * scale
            width = x_end - x_start

            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill=domain_color,
                    stroke=FEATURE_OUTLINES.get('domain', 'black'),
                    stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                )
            )

    # === 凡例 ===
    legend_x = max_x_coord + 100
    legend_y = 30
    box_size = 12
    spacing = 20
    legend_items = [
        ('domain', 'Domain', domain_color),
        ('CDS', 'Exon/CDS', exon_color),
        ('five_prime_UTR', "5' UTR", utr_color),
        ('three_prime_UTR', "3' UTR", utr_color),
        ('intron', 'Intron', line_color),
        ('deletion', 'Deletion', None)
    ]
    for i, (feat_key, label, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill='none',
                stroke='red',
                stroke_dasharray="5,5",
                stroke_width=2
            ))
        elif feat_key == 'intron':
            y_line = y_legend + box_size // 2
            dwg.add(dwg.line(
                start=(legend_x, y_line),
                end=(legend_x + box_size, y_line),
                stroke=color,
                stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
            ))
        else:
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill=color,
                stroke='black'
            ))
        dwg.add(dwg.text(
            label,
            insert=(legend_x + box_size + 5, y_legend + box_size - 2),
            font_size='12px',
            fill='black'
        ))

    return dwg.tostring()

# =====================
# Pydanticモデル
# =====================

class DrawGeneRequest(BaseModel):
    transcript_id: str
    gff_file_path: str = './gff3/IRGSP-1.0_representative/transcripts.gff'
    deletion_regions: List[List[int]] = []
    domains: List[Dict] = []
    protein_domain_start: Optional[int] = None
    protein_domain_end: Optional[int] = None
    protein_domain_name: Optional[str] = None

class Position(BaseModel):
    start: int
    end: int

class DrawSettings(BaseModel):
    mode: str  # "domain" or "gene"
    utr_color: str
    exon_color: str
    line_color: str
    intron_shape: str  # "straight" or "zigzag"
    gene_height: Optional[int] = None
    margin_x: Optional[int] = None
    margin_y: Optional[int] = None

class GeneStructureInfo(BaseModel):
    seq_id: Optional[str] = None
    source: Optional[str] = None
    type: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    score: Optional[float] = None
    strand: Optional[str] = None
    phase: Optional[str] = None
    attributes: Optional[Dict] = None
    transcript_id: str
    total_length: int
    exons: List[Position]
    cds: List[Position]
    five_prime_utrs: List[Position]
    three_prime_utrs: List[Position]

class GeneStructureRequest(BaseModel):
    draw_settings: DrawSettings
    gene_structure: GeneStructureInfo

# =====================
# エンドポイント
# =====================

@app.post("/api/py/draw-gene")
async def draw_gene(request: DrawGeneRequest):
    """
    遺伝子構造を描画するエンドポイント
    """
    try:
        # GFFファイルをパース
        gene = parse_gff_for_transcript(request.gff_file_path, request.transcript_id)

        if not gene:
            raise HTTPException(status_code=404, detail=f"Transcript {request.transcript_id} not found in GFF file")

        # イントロンを追加
        gene.add_introns()

        # 相対座標に変換
        gene.to_relative()

        # プロテインドメインを追加（指定されている場合）
        if request.protein_domain_start and request.protein_domain_end and request.protein_domain_name:
            gene.add_domain_from_protein_coords(
                request.protein_domain_start,
                request.protein_domain_end,
                request.protein_domain_name
            )

        # ドメインを追加
        if request.domains:
            gene.add_domains(request.domains)

        # デリーション処理
        deletion_regions_as_tuples = [tuple(r) for r in request.deletion_regions]
        gene.update_features_with_deletions(deletion_regions_as_tuples)

        # SVGを生成
        svg_content = draw_gene_structure(gene)

        return Response(content=svg_content, media_type="image/svg+xml")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="GFF file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        # SVGを生成（DrawSettingsから色を取得）
        draw_settings = request.draw_settings
        svg_content = draw_gene_structure(
            gene,
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
