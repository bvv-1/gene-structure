# Response to Reviewer #1

We are grateful to the reviewer for the constructive and insightful comments on our manuscript. We have carefully considered each point and have implemented several new features in both the CLI and web-based versions of **geneSTRUCTURE / geneSTRUCTURE+** to address the concerns raised. Below is our point-by-point response.

## Major Comments

### 1. Comparison with existing tools
**Comment:** *Please provide a comparison with existing tools (GSDS 2.0, JBrowse, IGV).*
**Response:** We agree that a clear comparison is essential to highlight the unique strengths of our tool. We have added a feature comparison table (Table 1) to the revised manuscript. While genome browsers like JBrowse and IGV are excellent for multi-omic data integration, geneSTRUCTURE specializes in the **rapid, high-quality visualization of individual gene models and their variants** (SNPs, InDels, protein domains) with a focus on publication-ready output. Unlike GSDS 2.0, our tool supports local execution (CLI), interactive web editing, and physical (chromosome) coordinate modes.

### 2. Discussion of technical details
**Comment:** *The discussion of React in the final section is somewhat too technical. Focus on biological use cases and future extensibility.*
**Response:** This is an important point, and we agree that the discussion should focus more on biological applications. We have significantly revised this section, moving technical implementation details regarding React to the Supplementary Materials. The revised Discussion now highlights biological use cases, such as visualizing allelic differences in QTL candidate genes, and discusses future extensibility (e.g., VCF/BED format support).

### 3. Feature Enhancements and Functionality
**Comment:** *Chromosome-level coordinates and scale information should be shown.*
**Response:** As suggested by the reviewer, we have implemented a coordinate scale bar in both the CLI and Web interfaces to facilitate better biological interpretation. Users can now see tick marks and scale labels (bp/kb) indicating the gene length and variant positions.
@todo@ (Figure: Scale bar implementation)

**Comment:** *Input data types and coordinate levels (Transcript vs. Chromosome).*
**Response:** We agree that supporting chromosome-level coordinates makes the tool much more convenient for practical use. In addition to transcript-relative coordinates, users can now specify positions using chromosome-level coordinates.
@todo@ (Figure: Absolute coordinate mode visualization)

**Comment:** *Predicted effects on amino acid sequence and side-by-side allele comparison.*
**Response:** This is an excellent suggestion for enhancing the biological utility of the tool. To address this, we have added **customizable color-coding for variants**, allowing users to assign specific colors based on predicted effects (e.g., red for stop-gained).
@todo@ (Figure: Variant color-coding and dynamic legend)

**Comment:** *Representative QTL/GWAS candidate regions.*
**Response:** We agree that using realistic examples makes the manuscript more compelling. We have replaced the generic examples in Figure 2 with well-characterized allelic differences (e.g., *Sdr4* or other representative rice/Arabidopsis genes) to better demonstrate practical use cases in QTL/GWAS studies.

**Comment:** *Visual representation of insertion/deletion length.*
**Response:** We agree that representing the scale of InDels visually adds significant value. We have modified the drawing logic so that the width of the triangle (for insertions) or the gap (for deletions) now scales proportionally to the actual base-pair length.
@todo@ (Figure: Proportional InDel length visualization)

## Minor Comments

1. **CLI CSV Specification:** We have addressed this by adding a detailed description of the CSV input format, including column headers and expected values, to both the main text and the GitHub README.
2. **Web SNP Information:** We are grateful for the reviewer's effort in testing the web application. The option to enter SNP information has been added to the Web UI, allowing users to input SNP positions and colors directly.
3. **English Documentation:** We fully agree with the need for better accessibility. We have provided a full English version of the documentation and README on our GitHub repository to ensure its utility for the international research community.

---
We believe these improvements significantly enhance the utility of geneSTRUCTURE and address all the concerns raised. We hope the revised manuscript is now suitable for publication.
