"""
add_domain_from_protein_coords() のユニットテスト

ドメイン座標が5'末（スタートコドン）から正しく計算されることを検証する。

プラス鎖 (+):
  ゲノム座標が小さい方が5'末 → CDS を昇順で処理
  AA1 はゲノム上の最小CDS座標に対応

マイナス鎖 (-):
  ゲノム座標が大きい方が5'末 → CDS を降順で処理
  AA1 はゲノム上の最大CDS座標に対応
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models import GeneFeature, GeneStructure


class TestDomainFromProteinCoords:
    """ドメイン座標変換のテスト"""

    def _make_gene(self, strand, cds_ranges):
        """ヘルパー: CDS を持つ GeneStructure を作成"""
        gene = GeneStructure("test_gene", "chr1", strand)
        for start, end in cds_ranges:
            gene.features.append(
                GeneFeature("chr1", start, end, "CDS", strand, {})
            )
        return gene

    def _get_domains(self, gene):
        """ヘルパー: ドメイン feature を取得"""
        return [f for f in gene.features if f.feature_type == "domain"]

    # --- プラス鎖テスト ---

    def test_plus_strand_single_cds_first_aa(self):
        """プラス鎖: 単一CDS、最初のアミノ酸(AA1)はCDSの5'末(start)に対応"""
        # CDS: 1000-1029 (30bp = 10 AA)
        gene = self._make_gene("+", [(1000, 1029)])
        gene.add_domain_from_protein_coords(1, 1, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA1 = cDNA 1-3 → ゲノム座標 1000-1002 (5'末)
        assert domains[0].start == 1000
        assert domains[0].end == 1002

    def test_plus_strand_single_cds_last_aa(self):
        """プラス鎖: 単一CDS、最後のアミノ酸(AA10)はCDSの3'末(end)に対応"""
        # CDS: 1000-1029 (30bp = 10 AA)
        gene = self._make_gene("+", [(1000, 1029)])
        gene.add_domain_from_protein_coords(10, 10, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA10 = cDNA 28-30 → ゲノム座標 1027-1029 (3'末)
        assert domains[0].start == 1027
        assert domains[0].end == 1029

    def test_plus_strand_single_cds_range(self):
        """プラス鎖: 単一CDS、AA2-4のドメイン"""
        # CDS: 1000-1029 (30bp = 10 AA)
        gene = self._make_gene("+", [(1000, 1029)])
        gene.add_domain_from_protein_coords(2, 4, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA2-4 = cDNA 4-12 → ゲノム座標 1003-1011
        assert domains[0].start == 1003
        assert domains[0].end == 1011

    def test_plus_strand_multi_cds_domain_in_first_cds(self):
        """プラス鎖: 複数CDS、ドメインが最初のCDS（5'末）内に収まる"""
        # CDS1: 1000-1029 (30bp = 10 AA), CDS2: 2000-2029 (30bp = 10 AA)
        gene = self._make_gene("+", [(1000, 1029), (2000, 2029)])
        gene.add_domain_from_protein_coords(1, 5, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA1-5 = cDNA 1-15 → CDS1内、ゲノム座標 1000-1014
        assert domains[0].start == 1000
        assert domains[0].end == 1014

    def test_plus_strand_multi_cds_domain_spans_intron(self):
        """プラス鎖: 複数CDS、ドメインがイントロンをまたぐ"""
        # CDS1: 1000-1008 (9bp = 3 AA), CDS2: 2000-2008 (9bp = 3 AA)
        gene = self._make_gene("+", [(1000, 1008), (2000, 2008)])
        gene.add_domain_from_protein_coords(1, 6, "test_domain")

        domains = self._get_domains(gene)
        # イントロンをまたぐので2つの domain feature に分割
        assert len(domains) == 2
        # 最初の部分: CDS1全体 1000-1008
        assert domains[0].start == 1000
        assert domains[0].end == 1008
        # 2番目の部分: CDS2全体 2000-2008
        assert domains[1].start == 2000
        assert domains[1].end == 2008

    # --- マイナス鎖テスト ---

    def test_minus_strand_single_cds_first_aa(self):
        """マイナス鎖: 単一CDS、最初のアミノ酸(AA1)はCDSの5'末(end)に対応"""
        # CDS: 1000-1029 (30bp = 10 AA)
        # マイナス鎖では5'末はゲノム座標のend側
        gene = self._make_gene("-", [(1000, 1029)])
        gene.add_domain_from_protein_coords(1, 1, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA1 = cDNA 1-3 → ゲノム座標 1027-1029 (5'末 = ゲノム上のend側)
        assert domains[0].start == 1027
        assert domains[0].end == 1029

    def test_minus_strand_single_cds_last_aa(self):
        """マイナス鎖: 単一CDS、最後のアミノ酸(AA10)はCDSの3'末(start)に対応"""
        # CDS: 1000-1029 (30bp = 10 AA)
        gene = self._make_gene("-", [(1000, 1029)])
        gene.add_domain_from_protein_coords(10, 10, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA10 = cDNA 28-30 → ゲノム座標 1000-1002 (3'末 = ゲノム上のstart側)
        assert domains[0].start == 1000
        assert domains[0].end == 1002

    def test_minus_strand_multi_cds_domain_in_first_cds(self):
        """マイナス鎖: 複数CDS、ドメインが最初のCDS（5'末 = ゲノム上で右側）内に収まる"""
        # CDS1: 1000-1029, CDS2: 2000-2029
        # マイナス鎖ではCDS2が5'末（転写の最初）
        gene = self._make_gene("-", [(1000, 1029), (2000, 2029)])
        gene.add_domain_from_protein_coords(1, 5, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 1
        # AA1-5 = cDNA 1-15 → CDS2(5'末)内、ゲノム座標 2015-2029
        assert domains[0].start == 2015
        assert domains[0].end == 2029

    def test_minus_strand_multi_cds_domain_spans_intron(self):
        """マイナス鎖: 複数CDS、ドメインがイントロンをまたぐ"""
        # CDS1: 1000-1008 (9bp = 3 AA), CDS2: 2000-2008 (9bp = 3 AA)
        # マイナス鎖ではCDS2が最初に処理される
        gene = self._make_gene("-", [(1000, 1008), (2000, 2008)])
        gene.add_domain_from_protein_coords(1, 6, "test_domain")

        domains = self._get_domains(gene)
        assert len(domains) == 2
        # マイナス鎖: CDS2が先（5'末）→ CDS1が後（3'末）
        # 最初の部分: CDS2全体 2000-2008
        assert domains[0].start == 2000
        assert domains[0].end == 2008
        # 2番目の部分: CDS1全体 1000-1008
        assert domains[1].start == 1000
        assert domains[1].end == 1008

    # --- エッジケース ---

    def test_domain_name_preserved(self):
        """ドメイン名がattributesに正しく保存される"""
        gene = self._make_gene("+", [(1000, 1029)])
        gene.add_domain_from_protein_coords(1, 5, "Kinase")

        domains = self._get_domains(gene)
        assert domains[0].attributes["name"] == "Kinase"

    def test_cds_order_independence(self):
        """CDS をどの順番で追加しても結果は同じ"""
        # CDS を逆順で追加
        gene1 = GeneStructure("test", "chr1", "+")
        gene1.features.append(GeneFeature("chr1", 2000, 2029, "CDS", "+", {}))
        gene1.features.append(GeneFeature("chr1", 1000, 1029, "CDS", "+", {}))
        gene1.add_domain_from_protein_coords(1, 5, "test")

        # CDS を正順で追加
        gene2 = self._make_gene("+", [(1000, 1029), (2000, 2029)])
        gene2.add_domain_from_protein_coords(1, 5, "test")

        domains1 = self._get_domains(gene1)
        domains2 = self._get_domains(gene2)
        assert len(domains1) == len(domains2)
        for d1, d2 in zip(domains1, domains2):
            assert d1.start == d2.start
            assert d1.end == d2.end
