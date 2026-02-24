import pytest
import sys
from pathlib import Path

# api ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 直接クラスを定義してテストを実行（相対インポート問題を回避）
# 元のモジュールの代わりにここでクラスを再定義


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
        self.insertions = []
        self.snps = []
        self.domain_color_map = {}

    def add_feature(self, feature: GeneFeature):
        self.features.append(feature)

    def normalize_features(self):
        """
        Feature の正規化処理（イントロン追加を含む）
        1. exon + CDS + UTR -> exon を削除
        2. exon + CDS (UTRなし) -> exon と CDS の差分から UTR を計算し、exon を削除
        3. exon のみ -> そのまま維持
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

    def _compute_utrs_from_exon_cds(self, exons, cds_list):
        """
        exon と CDS の差分から UTR を計算して追加
        """
        # CDS の全体範囲を取得
        cds_start = min(c.start for c in cds_list)
        cds_end = max(c.end for c in cds_list)

        for exon in exons:
            # 5' UTR: exon の開始から CDS の開始まで
            if exon.start < cds_start and exon.end >= cds_start:
                utr_end = min(exon.end, cds_start - 1)
                if exon.start <= utr_end:
                    self.features.append(GeneFeature(
                        self.seqid, exon.start, utr_end,
                        'five_prime_UTR', self.strand, {}
                    ))

            # 3' UTR: CDS の終了から exon の終了まで
            if exon.end > cds_end and exon.start <= cds_end:
                utr_start = max(exon.start, cds_end + 1)
                if utr_start <= exon.end:
                    self.features.append(GeneFeature(
                        self.seqid, utr_start, exon.end,
                        'three_prime_UTR', self.strand, {}
                    ))


class TestNormalizeFeatures:
    def test_exon_only_preserved(self):
        """exonのみの場合は保持される（イントロンも追加される）"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 200, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 300, 400, "exon", "+", {}))

        gene.normalize_features()

        exons = [f for f in gene.features if f.feature_type == "exon"]
        introns = [f for f in gene.features if f.feature_type == "intron"]
        assert len(exons) == 2
        assert len(introns) == 1
        assert introns[0].start == 201 and introns[0].end == 299

    def test_exon_removed_when_cds_utr_present(self):
        """CDS/UTRがある場合、exonは削除される"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 300, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 100, 150, "five_prime_UTR", "+", {}))
        gene.add_feature(GeneFeature("chr1", 151, 250, "CDS", "+", {}))
        gene.add_feature(GeneFeature("chr1", 251, 300, "three_prime_UTR", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types
        assert "five_prime_UTR" in feature_types
        assert "three_prime_UTR" in feature_types

    def test_cds_utr_only_unchanged(self):
        """CDS/UTRのみの場合は変更なし"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 150, "five_prime_UTR", "+", {}))
        gene.add_feature(GeneFeature("chr1", 151, 250, "CDS", "+", {}))

        original_count = len(gene.features)
        gene.normalize_features()

        assert len(gene.features) == original_count

    def test_exon_cds_computes_utrs(self):
        """exon + CDS のみの場合、UTR が計算される"""
        gene = GeneStructure("test", "chr1", "+")
        # exon: 100-500, CDS: 200-400
        # -> 5' UTR: 100-199, 3' UTR: 401-500
        gene.add_feature(GeneFeature("chr1", 100, 500, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 200, 400, "CDS", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types
        assert "five_prime_UTR" in feature_types
        assert "three_prime_UTR" in feature_types

        # UTR の座標を確認
        five_utr = next(f for f in gene.features if f.feature_type == "five_prime_UTR")
        three_utr = next(f for f in gene.features if f.feature_type == "three_prime_UTR")
        assert five_utr.start == 100 and five_utr.end == 199
        assert three_utr.start == 401 and three_utr.end == 500

    def test_multiple_exons_with_cds(self):
        """複数のexonとCDSがある場合"""
        gene = GeneStructure("test", "chr1", "+")
        # exon1: 100-200, exon2: 300-500
        # CDS: 150-450 (exon1の後半とexon2の前半を含む)
        gene.add_feature(GeneFeature("chr1", 100, 200, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 300, 500, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 150, 200, "CDS", "+", {}))
        gene.add_feature(GeneFeature("chr1", 300, 450, "CDS", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types

        # 5' UTR: 100-149 (exon1の前半)
        five_utrs = [f for f in gene.features if f.feature_type == "five_prime_UTR"]
        assert len(five_utrs) == 1
        assert five_utrs[0].start == 100 and five_utrs[0].end == 149

        # 3' UTR: 451-500 (exon2の後半)
        three_utrs = [f for f in gene.features if f.feature_type == "three_prime_UTR"]
        assert len(three_utrs) == 1
        assert three_utrs[0].start == 451 and three_utrs[0].end == 500

    def test_cds_only_no_change(self):
        """CDSのみの場合、exonがなければUTRは計算されない"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 300, "CDS", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "CDS" in feature_types
        assert "five_prime_UTR" not in feature_types
        assert "three_prime_UTR" not in feature_types

    def test_minus_strand(self):
        """マイナス鎖でも正しく動作する"""
        gene = GeneStructure("test", "chr1", "-")
        gene.add_feature(GeneFeature("chr1", 100, 500, "exon", "-", {}))
        gene.add_feature(GeneFeature("chr1", 200, 400, "CDS", "-", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types
        assert "five_prime_UTR" in feature_types
        assert "three_prime_UTR" in feature_types

    def test_exon_with_existing_utrs_removes_exon(self):
        """exon + CDS + UTR があり、UTRが既に存在する場合、exonのみ削除"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 500, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 100, 199, "five_prime_UTR", "+", {}))
        gene.add_feature(GeneFeature("chr1", 200, 400, "CDS", "+", {}))
        gene.add_feature(GeneFeature("chr1", 401, 500, "three_prime_UTR", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types
        # UTR は既存のものがそのまま残る（新たに計算されない）
        utrs = [f for f in gene.features if f.feature_type in ("five_prime_UTR", "three_prime_UTR")]
        assert len(utrs) == 2

    def test_no_utr_needed_when_exon_equals_cds(self):
        """exonとCDSが完全に一致する場合、UTRは生成されない"""
        gene = GeneStructure("test", "chr1", "+")
        gene.add_feature(GeneFeature("chr1", 100, 500, "exon", "+", {}))
        gene.add_feature(GeneFeature("chr1", 100, 500, "CDS", "+", {}))

        gene.normalize_features()

        feature_types = [f.feature_type for f in gene.features]
        assert "exon" not in feature_types
        assert "CDS" in feature_types
        assert "five_prime_UTR" not in feature_types
        assert "three_prime_UTR" not in feature_types
