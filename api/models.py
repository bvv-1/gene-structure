from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict, Any


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
    attributes: Optional[Dict[str, Any]] = None
    transcript_id: str
    total_length: int
    exons: List[Position]
    cds: List[Position]
    five_prime_utrs: List[Position]
    three_prime_utrs: List[Position]


class GeneStructureRequest(BaseModel):
    draw_settings: DrawSettings
    gene_structure: GeneStructureInfo
    deletion_regions: List[List[int]] = []
    domains: List[Dict] = []
    protein_domain_start: Optional[int] = None
    protein_domain_end: Optional[int] = None
    protein_domain_name: Optional[str] = None

    @field_validator('deletion_regions')
    @classmethod
    def validate_deletion_regions(cls, v):
        """deletion_regionsのバリデーション"""
        for i, region in enumerate(v):
            if len(region) != 2:
                raise ValueError(f"Deletion region {i} must have exactly 2 elements [start, end]")
            start, end = region
            if start <= 0 or end <= 0:
                raise ValueError(f"Deletion region {i}: coordinates must be positive integers (got start={start}, end={end})")
            if start >= end:
                raise ValueError(f"Deletion region {i}: start ({start}) must be less than end ({end})")
        return v

    @field_validator('protein_domain_start')
    @classmethod
    def validate_protein_domain_start(cls, v):
        """protein_domain_startのバリデーション"""
        if v is not None and v <= 0:
            raise ValueError(f"protein_domain_start must be a positive integer (got {v})")
        return v

    @field_validator('protein_domain_end')
    @classmethod
    def validate_protein_domain_end(cls, v):
        """protein_domain_endのバリデーション"""
        if v is not None and v <= 0:
            raise ValueError(f"protein_domain_end must be a positive integer (got {v})")
        return v

    @model_validator(mode='after')
    def validate_protein_domain(self):
        """protein domainの整合性チェック"""
        start = self.protein_domain_start
        end = self.protein_domain_end
        name = self.protein_domain_name

        # 3つのうち1つでも設定されている場合、すべてが必要
        if any([start, end, name]):
            if not all([start, end, name]):
                raise ValueError(
                    "protein_domain_start, protein_domain_end, and protein_domain_name must all be provided together"
                )
            if start >= end:
                raise ValueError(
                    f"protein_domain_start ({start}) must be less than protein_domain_end ({end})"
                )
        return self

    @field_validator('domains')
    @classmethod
    def validate_domains(cls, v):
        """domainsのバリデーション"""
        for i, domain in enumerate(v):
            # 必須フィールドのチェック
            if 'start' not in domain:
                raise ValueError(f"Domain {i}: 'start' field is required")
            if 'end' not in domain:
                raise ValueError(f"Domain {i}: 'end' field is required")
            if 'name' not in domain:
                raise ValueError(f"Domain {i}: 'name' field is required")

            start = domain['start']
            end = domain['end']
            name = domain['name']

            # 型チェック
            if not isinstance(start, int):
                raise ValueError(f"Domain {i}: 'start' must be an integer (got {type(start).__name__})")
            if not isinstance(end, int):
                raise ValueError(f"Domain {i}: 'end' must be an integer (got {type(end).__name__})")
            if not isinstance(name, str):
                raise ValueError(f"Domain {i}: 'name' must be a string (got {type(name).__name__})")

            # 範囲チェック
            if start <= 0 or end <= 0:
                raise ValueError(f"Domain {i}: coordinates must be positive integers (got start={start}, end={end})")
            if start >= end:
                raise ValueError(f"Domain {i}: start ({start}) must be less than end ({end})")
        return v


class MultiGeneStructureRequest(BaseModel):
    """複数遺伝子のSVG生成リクエスト"""
    draw_settings: DrawSettings
    gene_structures: List[GeneStructureInfo]
    show_labels: bool = True
    gene_spacing: int = 50  # 遺伝子間の余白（ピクセル）
    label_spacing: int = 10  # ラベルと遺伝子構造の余白（ピクセル）
    deletion_regions: List[List[int]] = []
    domains: List[Dict] = []
    protein_domain_start: Optional[int] = None
    protein_domain_end: Optional[int] = None
    protein_domain_name: Optional[str] = None

    @field_validator('gene_structures')
    @classmethod
    def validate_gene_structures(cls, v):
        """gene_structuresのバリデーション"""
        if len(v) == 0:
            raise ValueError("At least one gene structure is required")
        if len(v) > 30:
            raise ValueError("Maximum 30 gene structures allowed")
        return v

    @field_validator('gene_spacing')
    @classmethod
    def validate_gene_spacing(cls, v):
        """gene_spacingのバリデーション"""
        if v < 0:
            raise ValueError("gene_spacing must be non-negative")
        if v > 500:
            raise ValueError("gene_spacing must be 500 or less")
        return v

    @field_validator('label_spacing')
    @classmethod
    def validate_label_spacing(cls, v):
        """label_spacingのバリデーション"""
        if v < 0:
            raise ValueError("label_spacing must be non-negative")
        if v > 200:
            raise ValueError("label_spacing must be 200 or less")
        return v

    @field_validator('deletion_regions')
    @classmethod
    def validate_deletion_regions(cls, v):
        """deletion_regionsのバリデーション"""
        for i, region in enumerate(v):
            if len(region) != 2:
                raise ValueError(f"Deletion region {i} must have exactly 2 elements [start, end]")
            start, end = region
            if start <= 0 or end <= 0:
                raise ValueError(f"Deletion region {i}: coordinates must be positive integers (got start={start}, end={end})")
            if start >= end:
                raise ValueError(f"Deletion region {i}: start ({start}) must be less than end ({end})")
        return v

    @field_validator('protein_domain_start')
    @classmethod
    def validate_protein_domain_start(cls, v):
        """protein_domain_startのバリデーション"""
        if v is not None and v <= 0:
            raise ValueError(f"protein_domain_start must be a positive integer (got {v})")
        return v

    @field_validator('protein_domain_end')
    @classmethod
    def validate_protein_domain_end(cls, v):
        """protein_domain_endのバリデーション"""
        if v is not None and v <= 0:
            raise ValueError(f"protein_domain_end must be a positive integer (got {v})")
        return v

    @model_validator(mode='after')
    def validate_protein_domain(self):
        """protein domainの整合性チェック"""
        start = self.protein_domain_start
        end = self.protein_domain_end
        name = self.protein_domain_name

        # 3つのうち1つでも設定されている場合、すべてが必要
        if any([start, end, name]):
            if not all([start, end, name]):
                raise ValueError(
                    "protein_domain_start, protein_domain_end, and protein_domain_name must all be provided together"
                )
            if start >= end:
                raise ValueError(
                    f"protein_domain_start ({start}) must be less than protein_domain_end ({end})"
                )
        return self

    @field_validator('domains')
    @classmethod
    def validate_domains(cls, v):
        """domainsのバリデーション"""
        for i, domain in enumerate(v):
            # 必須フィールドのチェック
            if 'start' not in domain:
                raise ValueError(f"Domain {i}: 'start' field is required")
            if 'end' not in domain:
                raise ValueError(f"Domain {i}: 'end' field is required")
            if 'name' not in domain:
                raise ValueError(f"Domain {i}: 'name' field is required")

            start = domain['start']
            end = domain['end']
            name = domain['name']

            # 型チェック
            if not isinstance(start, int):
                raise ValueError(f"Domain {i}: 'start' must be an integer (got {type(start).__name__})")
            if not isinstance(end, int):
                raise ValueError(f"Domain {i}: 'end' must be an integer (got {type(end).__name__})")
            if not isinstance(name, str):
                raise ValueError(f"Domain {i}: 'name' must be a string (got {type(name).__name__})")

            # 範囲チェック
            if start <= 0 or end <= 0:
                raise ValueError(f"Domain {i}: coordinates must be positive integers (got start={start}, end={end})")
            if start >= end:
                raise ValueError(f"Domain {i}: start ({start}) must be less than end ({end})")
        return v


class RegionGeneStructureRequest(BaseModel):
    """領域指定による複数遺伝子のSVG生成リクエスト"""
    draw_settings: DrawSettings
    gene_structures: List[GeneStructureInfo]
    region_start: int  # 表示領域の開始座標
    region_end: int    # 表示領域の終了座標
    show_labels: bool = True
    gene_spacing: int = 50
    label_spacing: int = 10

    @field_validator('gene_structures')
    @classmethod
    def validate_gene_structures(cls, v):
        if len(v) == 0:
            raise ValueError("At least one gene structure is required")
        if len(v) > 30:
            raise ValueError("Maximum 30 gene structures allowed")
        return v

    @field_validator('gene_spacing')
    @classmethod
    def validate_gene_spacing(cls, v):
        if v < 0:
            raise ValueError("gene_spacing must be non-negative")
        if v > 500:
            raise ValueError("gene_spacing must be 500 or less")
        return v

    @field_validator('label_spacing')
    @classmethod
    def validate_label_spacing(cls, v):
        if v < 0:
            raise ValueError("label_spacing must be non-negative")
        if v > 200:
            raise ValueError("label_spacing must be 200 or less")
        return v

    @model_validator(mode='after')
    def validate_region(self):
        if self.region_start >= self.region_end:
            raise ValueError(
                f"region_start ({self.region_start}) must be less than region_end ({self.region_end})"
            )
        return self