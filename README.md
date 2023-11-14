# Variation Normalizer Manuscript

This repo contains analysis notebooks used in the _The Clinical Genomic Variation Landscape_ manuscript.

## Set Up

Before running the notebooks, you must set up your environment.

### Creating the virtual environment

First, create your virtual environment. The [requirements.txt](./requirements.txt) is a lockfile containing exact versions used. The [requirements-dev.txt](./requirements-dev.txt) contains the main third party packages.

From the root directory, run the following to create the venv and install exact packages:

```shell
make devready
source .venv/bin/activate
```

### Environment Variables and Installing Dependencies

We use [python-dotenv](https://pypi.org/project/python-dotenv/) to load environment variables needed for analysis notebooks that run the [Variation Normalizer](https://github.com/cancervariants/variation-normalization/tree/0.6.0-dev0).

If you are running any of the following notebooks, this section is required:

* [analysis/civic/variation_analysis/civic_variation_analysis.ipynb](./analysis/civic/variation_analysis/civic_variation_analysis.ipynb)
* [analysis/cnvs/parse_prep_normalize_nch_cnvs.ipynb](./analysis/cnvs/parse_prep_normalize_nch_cnvs.ipynb)
* [analysis/genie/pre_variant_analysis/genie_pre_variant_analysis.ipynb](./analysis/genie/pre_variant_analysis/genie_pre_variant_analysis.ipynb)
* [analysis/moa/feature_analysis/moa_feature_analysis.ipynb](./analysis/moa/feature_analysis/moa_feature_analysis.ipynb)

In the analysis notebooks, you will see:

```python
from dotenv import load_dotenv

load_dotenv()
```

This will load environment variables from the `.env` file in the root directory. You will need to create this file yourself. The structure will look like:

```markdown
.
├── analysis
├── .env
└── README.md
```

The environment variables that will need to be set inside the `.env` file:

```env
GENE_NORM_DB_URL=http://localhost:8000
UTA_DB_URL=driver://user:password@host:port/database/schema
AWS_ACCESS_KEY_ID=dummy  # only required if using gene-normalizer dynamodb
AWS_SECRET_ACCESS_KEY=dummy  # only required if using gene-normalizer dynamodb
AWS_SESSION_TOKEN=dummy  # only required if using gene-normalizer dynamodb
TRANSCRIPT_MAPPINGS_PATH=variation-normalizer-manuscript/analysis/data/transcript_mapping.tsv  # Should be absolute path. For cool-seq-tool
MANE_SUMMARY_PATH=variation-normalizer-manuscript/analysis/data/MANE.GRCh38.v1.3.summary.txt  # Should be absolute path. For cool-seq-tool
LRG_REFSEQGENE_PATH=variation-normalizer-manuscript/analysis/data/LRG_RefSeqGene_20231114  # Should be absolute path. For cool-seq-tool

```

#### Gene Normalizer Installation

You must set up [VICC Gene Normalizer](https://github.com/cancervariants/gene-normalization/tree/v0.1.39).

Note: If you do not have an AWS account, you can keep `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` as is. Local DynamoDB instances will allow dummy credentials. If using gene-normalizer with PostgreSQL database instance, you do not need to set these environment variables.

#### Cool-Seq-Tool installation

You must set up [Cool-Seq-Tool](https://github.com/GenomicMedLab/cool-seq-tool/tree/v0.1.14-dev1) UTA database. This analysis used the `uta_20210129` version. More information can be found [here](https://github.com/GenomicMedLab/cool-seq-tool/tree/v0.1.14-dev1#uta-database-installation).

#### SeqRepo

Gene Normalizer and Cool-Seq-Tool provide steps for downloading [Biocommons SeqRepo](https://github.com/biocommons/biocommons.seqrepo) data. This analysis used `2021-01-29` SeqRepo data.

## Notebooks

This section provides information about the notebooks and the order that they should be run in.

1. Run the following notebook:
    * [analysis/download_cool_seq_tool_data.ipynb](./analysis/download_cool_seq_tool_data.ipynb)
      * Downloads `LRG_RefSeqGene_20231114`, `MANE.GRCh38.v1.3.summary.txt`, `transcript_mapping.tsv`
    * [analysis/cnvs/download_data_for_cnv_analysis_data.ipynb](./analysis/cnvs/download_data_for_cnv_analysis_data.ipynb)
      * Downloads ClinVar CNV, MANE Ensembl GFF, and NCH CNV data
      * The following notebooks were used to create the files that are downloaded in this notebook (order does not matter):
        * [analysis/cnvs/prep_clinvar_cnvs.ipynb](./analysis/cnvs/prep_clinvar_cnvs.ipynb)
          * Creates `ClinVar-CNVs-normalized.csv`
        * [analysis/cnvs/parse_prep_normalize_nch_cnvs.ipynb](./analysis/cnvs/parse_prep_normalize_nch_cnvs.ipynb)
          * Creates `NCH-microarray-CNVs-cleaned.csv`
2. Run the following notebooks (order does not matter):
   * [analysis/civic/variation_analysis/civic_variation_analysis.ipynb](./analysis/civic/variation_analysis/civic_variation_analysis.ipynb)
     * Runs CIViC variant data through the Variation Normalizer
   * [analysis/clinvar/clinvar_variation_analysis.ipynb](./analysis/clinvar/clinvar_variation_analysis.ipynb)
     * Analysis on ClinVar variant data
   * [analysis/genie/pre_variant_analysis/genie_pre_variant_analysis.ipynb](./analysis/genie/pre_variant_analysis/genie_pre_variant_analysis.ipynb)
     * Runs GENIE variant data through the Variation Normalizer
   * [analysis/moa/feature_analysis/moa_feature_analysis.ipynb](./analysis/moa/feature_analysis/moa_feature_analysis.ipynb)
     * Runs MOA feature data through the Variation Normalizer
3. Run the following notebooks (order does not matter):
    * [analysis/civic/evidence_analysis/civic_evidence_analysis.ipynb](./analysis/civic/evidence_analysis/civic_evidence_analysis.ipynb)
      * Analysis on CIViC evidence items
    * [analysis/cnvs/query_match_nch_clinvar_cnvs.ipynb](./analysis/cnvs/query_match_nch_clinvar_cnvs.ipynb)
      * Analysis on feature overlap in NCH and ClinVar CNVs
    * [analysis/genie/variant_analysis/genie_search_analysis.ipynb](./analysis/genie/variant_analysis/genie_search_analysis.ipynb)
      * Analysis on matched normalized GENIE variants and normalized variants from CIViC, MOA, and ClinVar
    * [analysis/moa/assertion_analysis/moa_assertion_analysis.ipynb](./analysis/moa/assertion_analysis/moa_assertion_analysis.ipynb)
      * Analysis on MOA assertions
4. Run the following notebook:
    * [analysis/merged_moa_civic/merged_moa_civic_evidence_analysis.ipynb](./analysis/merged_moa_civic/merged_moa_civic_evidence_analysis.ipynb)
      * Combined analysis on CIViC evidence items and MOA assertions
5. Run the following notebook:
    * [analysis/performance_analysis/merged_performance_analysis.ipynb](./analysis/performance_analysis/merged_performance_analysis.ipynb)
      * Analysis on Variation Normalizer performance on CIViC, MOA, and ClinVar

## Help

If you have any questions or problems, please make an issue in the repo and our team will be happy to assist.
