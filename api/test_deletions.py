
import pytest
from api.models import GeneStructure, GeneFeature, Deletion, Snp, Insertion

def test_update_features_with_deletions_all_types():
    # Setup
    gene = GeneStructure("test_gene", "chr1", "+")
    
    # Structural features
    gene.add_feature(GeneFeature("chr1", 100, 500, "exon", "+", {}))
    gene.add_feature(GeneFeature("chr1", 200, 300, "CDS", "+", {}))
    
    # Annotational features
    gene.add_domains([{"start": 150, "end": 250, "name": "Domain1", "color": "green"}])
    
    # Point features
    gene.add_snps([Snp(position=220, ref="A", alt="T")])
    gene.add_insertions([Insertion(position=230, length=10)])
    
    # Deletion: 200-240
    # Overlaps with:
    # - exon 100-500 -> truncate to 100-199 and 241-500
    # - CDS 200-300 -> truncate to 241-300 (200-240 is deleted)
    # - Domain1 150-250 -> Should be REMOVED (or truncated? user says "other elements...hide")
    # - SNP at 220 -> Should be REMOVED
    # - Insertion at 230 -> Should be REMOVED
    
    deletions = [Deletion(start=200, end=240)]
    gene.update_features_with_deletions(deletions)
    
    # Verify deletion_regions are stored
    assert len(gene.deletion_regions) == 1
    assert gene.deletion_regions[0].start == 200
    
    # Verify Structural Features (Truncated)
    exons = [f for f in gene.features if f.feature_type == 'exon']
    assert len(exons) == 2
    assert (exons[0].start, exons[0].end) == (100, 199)
    assert (exons[1].start, exons[1].end) == (241, 500)
    
    cdss = [f for f in gene.features if f.feature_type == 'CDS']
    assert len(cdss) == 1
    assert (cdss[0].start, cdss[0].end) == (241, 300)
    
    # Verify Annotational Features (Removed according to my interpretation of "表示を消す")
    domains = [f for f in gene.features if f.feature_type == 'domain']
    assert len(domains) == 0, f"Expected domain to be removed, but got {domains}"
    
    # Verify Point Features (Removed)
    assert len(gene.snps) == 0, f"Expected SNP to be removed, but got {gene.snps}"
    assert len(gene.insertions) == 0, f"Expected Insertion to be removed, but got {gene.insertions}"

def test_deletion_no_overlap():
    gene = GeneStructure("test_gene", "chr1", "+")
    gene.add_feature(GeneFeature("chr1", 100, 200, "exon", "+", {}))
    gene.add_snps([Snp(position=150, ref="A", alt="T")])
    
    deletions = [Deletion(start=300, end=400)]
    gene.update_features_with_deletions(deletions)
    
    assert len([f for f in gene.features if f.feature_type == 'exon']) == 1
    assert len(gene.snps) == 1
