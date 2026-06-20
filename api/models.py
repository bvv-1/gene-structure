from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict, Any

from .config import DOMAIN_COLOR_PALETTE
from .color_utils import get_domain_color


class CoordinateMode(str, Enum):
    """座標モードの列挙型"""
    RELATIVE = "relative"  # 相対座標（デフォルト）
    ABSOLUTE = "absolute"  # 絶対座標（染色体座標）


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
        self.insertions: List[Insertion] = []
        self.snps: List[Snp] = []
        self.deletion_regions: List[Deletion] = []
        self.domain_color_map = {}
        self.is_relative = False

    def add_insertions(self, insertions: List[Insertion]):
        """Insertionオブジェクトのリストを設定"""
        self.insertions = insertions

    def add_snps(self, snps: List[Snp]):
        """Snpオブジェクトのリストを設定"""
        self.snps = snps

    def add_feature(self, feature: GeneFeature):
        self.features.append(feature)

    def get_sorted_features(self):
        return sorted(self.features, key=lambda f: f.start, reverse=False)

    def normalize_features(self):
        """
        Feature の正規化処理（イントロン追加を含む）
        1. exon + CDS + UTR → exon を削除
        2. exon + CDS (UTRなし) → exon と CDS の差分から UTR を計算し、exon を削除
        3. exon のみ → そのまま維持
        4. イントロンを追加
        """
        exons = [f for f in self.features if f.feature_type == 'exon']
        cds_list = [f for f in self.features if f.feature_type == 'CDS']
        utrs = [f for f in self.features if f.feature_type in ('five_prime_UTR', 'three_prime_UTR')]

        # Case 1 & 2: CDS がある場合
        if cds_list:
            # UTR がない場合、exon と CDS の差分から UTR を計算
            if not utrs and exons:
                self._compute_utrs_from_exon_cds(exons, cds_list)

            # exon を削除（CDS + UTR で表現するため）
            self.features = [f for f in self.features if f.feature_type != 'exon']

        # Case 3: exon のみの場合はそのまま

        # イントロンを追加
        self.add_introns()

    def _compute_utrs_from_exon_cds(self, exons, cds_list):
        """
        exon と CDS の差分から UTR を計算して追加
        """
        # CDS の全体範囲を取得
        cds_start = min(c.start for c in cds_list)
        cds_end = max(c.end for c in cds_list)

        for exon in exons:
            if self.strand == '-':
                # マイナスストランド: 5' UTR は CDS より大きな座標、3' UTR は CDS より小さな座標
                # 5' UTR: CDS の終了から exon の終了まで
                if exon.end > cds_end and exon.start <= cds_end + 1:
                    utr_start = max(exon.start, cds_end + 1)
                    if utr_start <= exon.end:
                        self.features.append(GeneFeature(
                            self.seqid, utr_start, exon.end,
                            'five_prime_UTR', self.strand, {}
                        ))

                # 3' UTR: exon の開始から CDS の開始まで
                if exon.start < cds_start and exon.end >= cds_start - 1:
                    utr_end = min(exon.end, cds_start - 1)
                    if exon.start <= utr_end:
                        self.features.append(GeneFeature(
                            self.seqid, exon.start, utr_end,
                            'three_prime_UTR', self.strand, {}
                        ))
            else:
                # プラスストランド: 5' UTR は CDS より小さな座標、3' UTR は CDS より大きな座標
                # 5' UTR: exon の開始から CDS の開始まで
                if exon.start < cds_start and exon.end >= cds_start - 1:
                    utr_end = min(exon.end, cds_start - 1)
                    if exon.start <= utr_end:
                        self.features.append(GeneFeature(
                            self.seqid, exon.start, utr_end,
                            'five_prime_UTR', self.strand, {}
                        ))

                # 3' UTR: CDS の終了から exon の終了まで
                if exon.end > cds_end and exon.start <= cds_end + 1:
                    utr_start = max(exon.start, cds_end + 1)
                    if utr_start <= exon.end:
                        self.features.append(GeneFeature(
                            self.seqid, utr_start, exon.end,
                            'three_prime_UTR', self.strand, {}
                        ))

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
            # colorが未指定の場合、パレットから自動割り当て
            if not color:
                color = get_domain_color(name, self.domain_color_map, DOMAIN_COLOR_PALETTE)
            else:
                # 指定された色もdomain_color_mapに記録
                self.domain_color_map[name] = color
            domain_feature = GeneFeature(
                self.seqid,
                start,
                end,
                'domain',
                self.strand,
                attributes={'name': name, 'color': color}
            )
            self.features.append(domain_feature)

    def get_sorted_features(self):
        return sorted(self.features, key=lambda f: f.start)

    def get_full_extent(self):
        """SNPや挿入を含めた、遺伝子構造の真の開始・終了座標を返す"""
        starts = [f.start for f in self.features]
        ends = [f.end for f in self.features]

        for snp in self.snps:
            pos = getattr(snp, 'position', snp)
            starts.append(pos)
            ends.append(pos)

        for ins in self.insertions:
            pos = getattr(ins, 'position', ins)
            length = getattr(ins, 'length', 1)
            starts.append(pos)
            ends.append(pos + length - 1)

        if not starts:
            return 1, 1
        return min(starts), max(ends)

    def update_features_with_deletions(self, deletion_regions: List[Deletion]):
        self.deletion_regions = deletion_regions
        new_features = []
        structural_types = {'exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR', 'intron', 'domain'}

        # まずデリーション自体をフィーチャーとして追加
        for deletion in deletion_regions:
            new_features.append(GeneFeature(
                self.seqid, deletion.start, deletion.end,
                'deletion', self.strand, {'color': deletion.color}
            ))

        for feature in self.features:
            # すでに存在するデリーションは重複を避けるためにスキップ（通常はないはずだが）
            if feature.feature_type == 'deletion':
                continue

            # 非構造的要素（ドメイン等）の場合、デリーションと重なれば削除する
            if feature.feature_type not in structural_types:
                overlaps = False
                for deletion in deletion_regions:
                    if not (feature.end < deletion.start or feature.start > deletion.end):
                        overlaps = True
                        break
                if overlaps:
                    continue

            # 構造的要素（または重なっていない非構造要素）の処理
            f_start, f_end = feature.start, feature.end
            segments = [(f_start, f_end)]  # featureの元の範囲

            for deletion in deletion_regions:
                del_start, del_end = deletion.start, deletion.end
                updated_segments = []

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

            # 分割後の有効セグメントが残っていれば追加
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

        # SNPと挿入のフィルタリング
        if deletion_regions:
            self.snps = [
                s for s in self.snps 
                if not any(d.start <= s.position <= d.end for d in deletion_regions)
            ]
            self.insertions = [
                i for i in self.insertions 
                if not any(d.start <= i.position <= d.end for d in deletion_regions)
            ]

    def to_relative(self):
        if self.is_relative:
            return 1

        # 基準（1番）を決定するためのフィーチャーを選択
        # ユーザー要望により、Exon または CDS の開始位置を基準とする
        anchor_targets = [f for f in self.features if f.feature_type in ('exon', 'CDS')]
        
        # もし Exon/CDS がない場合は UTR を含めて探す（フォールバック）
        if not anchor_targets:
            anchor_targets = [f for f in self.features if f.feature_type in ('five_prime_UTR', 'three_prime_UTR')]
        
        # それでもない場合は全フィーチャーから探す
        if not anchor_targets:
            anchor_targets = self.features
            
        if not anchor_targets:
            return 0

        # プラス鎖: 最小値が基準 (anchor)
        # マイナス鎖: 最大値が基準 (anchor)
        all_coords = []
        for f in anchor_targets:
            all_coords.append(f.start)
            all_coords.append(f.end)
        
        if self.strand == '-':
            anchor = max(all_coords)
        else:
            anchor = min(all_coords)

        # すべてのフィーチャー（イントロン、ドメイン、デリーション含む）をシフト
        for f in self.features:
            if self.strand == '-':
                s = anchor - f.start + 1
                e = anchor - f.end + 1
                f.start = min(s, e)
                f.end = max(s, e)
            else:
                f.start = f.start - anchor + 1
                f.end = f.end - anchor + 1

        # SNPと挿入も相対座標に変換
        if hasattr(self, 'snps') and self.snps:
            for i in range(len(self.snps)):
                s = self.snps[i]
                if hasattr(s, 'position'):
                    if self.strand == '-':
                        s.position = anchor - s.position + 1
                    else:
                        s.position = s.position - anchor + 1
                else:
                    if self.strand == '-':
                        self.snps[i] = anchor - s + 1
                    else:
                        self.snps[i] = s - anchor + 1
        
        if hasattr(self, 'insertions') and self.insertions:
            for i in range(len(self.insertions)):
                ins = self.insertions[i]
                if hasattr(ins, 'position'):
                    if self.strand == '-':
                        ins.position = anchor - ins.position + 1
                    else:
                        ins.position = ins.position - anchor + 1
                else:
                    if self.strand == '-':
                        self.insertions[i] = anchor - ins + 1
                    else:
                        self.insertions[i] = ins - anchor + 1

        # デリーション領域も相対座標に変換
        if hasattr(self, 'deletion_regions') and self.deletion_regions:
            for i in range(len(self.deletion_regions)):
                d = self.deletion_regions[i]
                if isinstance(d, Deletion):
                    s_orig, e_orig = d.start, d.end
                    if self.strand == '-':
                        s = anchor - s_orig + 1
                        e = anchor - e_orig + 1
                        d.start, d.end = min(s, e), max(s, e)
                    else:
                        d.start = s_orig - anchor + 1
                        d.end = e_orig - anchor + 1
                elif isinstance(d, dict):
                    # dict形式の場合（geneSTRUCTUREとの互換性用）
                    s_orig, e_orig = d['start'], d['end']
                    if self.strand == '-':
                        s = anchor - s_orig + 1
                        e = anchor - e_orig + 1
                        d['start'], d['end'] = min(s, e), max(s, e)
                    else:
                        d['start'] = s_orig - anchor + 1
                        d['end'] = e_orig - anchor + 1

        self.is_relative = True
        return 1

    def add_domain_from_protein_coords(self, start_aa: int, end_aa: int, domain_name: str):
        """
        アミノ酸座標（1-based）を基に、CDSからcDNA、そして現在の座標系へと変換して
        ドメイン領域をfeaturesに追加する。
        """
        # アミノ酸座標 → cDNA 座標（1-based）
        cdna_start = (start_aa - 1) * 3 + 1
        cdna_end = end_aa * 3

        # CDS features を取得
        cds_features = [f for f in self.features if f.feature_type == 'CDS']
        if not cds_features:
            return

        # すでに to_relative() が実行されている場合、
        # プラス・マイナスに関わらず start が小さい順に並べれば 5' -> 3' になる
        cds_sorted = sorted(cds_features, key=lambda f: f.start)

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

            # 現在の座標（相対座標化されていれば相対座標）で位置を決定
            # 5'末端が常に start になっているため、プラス鎖と同じ計算式でOK
            g_start = cds.start + offset_start
            g_end = cds.start + offset_end

            # ドメイン色を取得（まだ割り当てられていなければパレットから自動割り当て）
            color = get_domain_color(domain_name, self.domain_color_map, DOMAIN_COLOR_PALETTE)

            # ドメイン feature を追加
            domain_feature = GeneFeature(
                seqid=self.seqid,
                start=g_start,
                end=g_end,
                feature_type='domain',
                strand=self.strand,
                attributes={'name': domain_name, 'color': color}
            )
            self.features.append(domain_feature)

            current_cdna_pos = next_cdna_pos + 1


# =====================
# Pydanticモデル
# =====================

class Insertion(BaseModel):
    """挿入位置と長さを指定するモデル"""
    position: int  # 挿入位置（ゲノム座標）
    length: int    # 挿入長（bp）
    color: Optional[str] = "black"  # 描画色

    @model_validator(mode='after')
    def validate_insertion(self):
        if self.length <= 0:
            raise ValueError(f"length must be a positive integer (got {self.length})")
        return self


class Snp(BaseModel):
    """SNP位置と色を指定するモデル"""
    position: int
    color: Optional[str] = "black"

    @model_validator(mode='after')
    def validate_snp(self):
        return self


class Deletion(BaseModel):
    """削除領域と色を指定するモデル"""
    start: int
    end: int
    color: Optional[str] = "black"

    @model_validator(mode='after')
    def validate_deletion(self):
        if self.start >= self.end:
            raise ValueError(f"start ({self.start}) must be less than end ({self.end})")
        return self


class ProteinDomain(BaseModel):
    """アミノ酸座標で指定するプロテインドメイン"""
    start: int
    end: int
    name: str

    @model_validator(mode='after')
    def validate_range(self):
        if self.start <= 0:
            raise ValueError(f"start must be a positive integer (got {self.start})")
        if self.end <= 0:
            raise ValueError(f"end must be a positive integer (got {self.end})")
        if self.start >= self.end:
            raise ValueError(f"start ({self.start}) must be less than end ({self.end})")
        return self


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
    # オプション: 個別のバリアント情報
    snps: List[Snp] = []
    insertions: List[Insertion] = []
    deletion_regions: List[Deletion] = []
    domains: List[Dict] = []
    protein_domains: List[ProteinDomain] = []
    total_length: int
    exons: List[Position]
    cds: List[Position]
    five_prime_utrs: List[Position]
    three_prime_utrs: List[Position]


class GeneStructureRequest(BaseModel):
    draw_settings: DrawSettings
    gene_structure: GeneStructureInfo
    deletion_regions: List[Deletion] = []
    domains: List[Dict] = []
    protein_domains: List[ProteinDomain] = []
    snps: List[Snp] = []
    insertions: List[Insertion] = []
    coordinate_mode: CoordinateMode = CoordinateMode.RELATIVE

    @field_validator('deletion_regions', mode='before')
    @classmethod
    def validate_deletion_regions_before(cls, v):
        """[start, end] のリスト形式を Deletion オブジェクトに変換"""
        new_v = []
        for item in v:
            if isinstance(item, list):
                if len(item) != 2:
                    raise ValueError(f"Deletion region must have exactly 2 elements [start, end]")
                new_v.append({"start": item[0], "end": item[1], "color": "black"})
            else:
                new_v.append(item)
        return new_v

    @field_validator('snps', mode='before')
    @classmethod
    def validate_snps_before(cls, v):
        """int のリスト形式を Snp オブジェクトに変換"""
        new_v = []
        for item in v:
            if isinstance(item, int):
                new_v.append({"position": item, "color": "black"})
            else:
                new_v.append(item)
        return new_v

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


class MultiGeneItem(BaseModel):
    """各トランスクリプトの構造とバリアント定義"""
    gene_structure: GeneStructureInfo
    snps: List[Snp] = []
    insertions: List[Insertion] = []
    deletion_regions: List[Deletion] = []
    domains: List[Dict] = []
    protein_domains: List[ProteinDomain] = []

    @field_validator('deletion_regions', mode='before')
    @classmethod
    def validate_deletion_regions_before(cls, v):
        """[start, end] のリスト形式を Deletion オブジェクトに変換"""
        new_v = []
        for item in v:
            if isinstance(item, list):
                if len(item) != 2:
                    raise ValueError(f"Deletion region must have exactly 2 elements [start, end]")
                new_v.append({"start": item[0], "end": item[1], "color": "black"})
            else:
                new_v.append(item)
        return new_v

    @field_validator('snps', mode='before')
    @classmethod
    def validate_snps_before(cls, v):
        """int のリスト形式を Snp オブジェクトに変換"""
        new_v = []
        for item in v:
            if isinstance(item, int):
                new_v.append({"position": item, "color": "black"})
            else:
                new_v.append(item)
        return new_v

    @field_validator('domains')
    @classmethod
    def validate_domains(cls, v):
        """domainsのバリデーション"""
        for i, domain in enumerate(v):
            if 'start' not in domain:
                raise ValueError(f"Domain {i}: 'start' field is required")
            if 'end' not in domain:
                raise ValueError(f"Domain {i}: 'end' field is required")
            if 'name' not in domain:
                raise ValueError(f"Domain {i}: 'name' field is required")
            start = domain['start']
            end = domain['end']
            name = domain['name']
            if not isinstance(start, int):
                raise ValueError(f"Domain {i}: 'start' must be an integer (got {type(start).__name__})")
            if not isinstance(end, int):
                raise ValueError(f"Domain {i}: 'end' must be an integer (got {type(end).__name__})")
            if not isinstance(name, str):
                raise ValueError(f"Domain {i}: 'name' must be a string (got {type(name).__name__})")
            if start <= 0 or end <= 0:
                raise ValueError(f"Domain {i}: coordinates must be positive integers (got start={start}, end={end})")
            if start >= end:
                raise ValueError(f"Domain {i}: start ({start}) must be less than end ({end})")
        return v

class MultiGeneStructureRequest(BaseModel):
    """複数遺伝子のSVG生成リクエスト"""
    draw_settings: DrawSettings
    items: List[MultiGeneItem]
    show_labels: bool = True
    show_scale: bool = False  # スケールバー表示フラグ
    gene_spacing: int = 50  # 遺伝子間の余白（ピクセル）
    label_spacing: int = 10  # ラベルと遺伝子構造の余白（ピクセル）
    coordinate_mode: CoordinateMode = CoordinateMode.RELATIVE

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        """itemsのバリデーション"""
        if len(v) == 0:
            raise ValueError("At least one item is required")
        if len(v) > 30:
            raise ValueError("Maximum 30 items allowed")
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
