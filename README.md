# Variation Normalizer Manuscript

This repo contains analysis notebooks used in the _The Clinical Genomic Variation Landscape_ manuscript.

Small output files can be found in this repo. Larger files can be found in our public s3 bucket: `s3://nch-igm-wagner-lab-public/variation-normalizer-manuscript/`. There are notebooks that provide functions for programmatically downloading files from the s3 bucket.

After running these notebooks, users will be able to create figures such as this that demonstrate the results of this analysis.

Variant normalization allows patient data from AACR Project GENIE to be matched to normalized variants in the CIViC, MOA, and ClinVar knowledgebases.

![Patient Matching with GENIE](./analysis/genie/variant_analysis/genie_patient_matching.png)

## Set Up

Before running the notebooks, you must set up your environment.

### Install Python 3.11

Python 3.11 was used for this analysis. We recommend using [Pyenv](https://github.com/pyenv/pyenv) to install.

### Creating the virtual environment

First, create your virtual environment. The [requirements.txt](./requirements.txt) is a lockfile containing exact versions used. The [requirements-dev.txt](./requirements-dev.txt) contains the main third party packages.

From the root directory, run the following to create the venv and install exact packages:

```shell
make devready
source .venv/bin/activate
```

### Environment Variables

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
UTA_DB_URL=driver://user:password@host:port/database/schema  # replace with actual values
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_SESSION_TOKEN=dummy
TRANSCRIPT_MAPPINGS_PATH=variation-normalizer-manuscript/analysis/data/transcript_mapping.tsv  # Should be absolute path. For cool-seq-tool
MANE_SUMMARY_PATH=variation-normalizer-manuscript/analysis/data/MANE.GRCh38.v1.3.summary.txt  # Should be absolute path. For cool-seq-tool
LRG_REFSEQGENE_PATH=variation-normalizer-manuscript/analysis/data/LRG_RefSeqGene_20231114  # Should be absolute path. For cool-seq-tool
SEQREPO_ROOT_DIR=/usr/local/share/seqrepo/latest  # replace if using different path
```

In [analysis/download_s3_files.ipynb](./analysis/download_s3_files.ipynb), `transcript_mapping.tsv`, `MANE.GRCh38.v1.3.summary.txt`, and `LRG_RefSeqGene_20231114` will be downloaded to `./analysis/data` directory. You must update the associated environment variables (`TRANSCRIPT_MAPPINGS_PATH`, `MANE_SUMMARY_PATH`, `LRG_REFSEQGENE_PATH`) to use the absolute path.

### Set Up Backend Services

This analysis relies on several backend services, which you must set up yourself.

#### Biocommons SeqRepo

[Biocommons SeqRepo](https://github.com/biocommons/biocommons.seqrepo) is used for fast access to sequence data. This analysis used [2021-01-29](https://dl.biocommons.org/seqrepo/2021-01-29/) SeqRepo data.

Follow the [Quick Start Documentation](https://github.com/biocommons/biocommons.seqrepo/tree/0.6.5) for setting up SeqRepo. The VICC Gene Normalizer also provides some additional setup help [here](https://gene-normalizer.readthedocs.io/en/v0.1.39/full_install.html#seqrepo).

Update the `SEQREPO_ROOT_DIR` in the `.env` file with the path to SeqRepo. The default path is `/usr/local/share/seqrepo/latest`.

##### SeqRepo Verification

To verify, run the following inside your virtual environment:

```shell
$ python3
Python 3.11.5 (main, Aug 24 2023, 15:18:16) [Clang 14.0.3 (clang-1403.0.22.14.1)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from dotenv import load_dotenv
>>> load_dotenv()
True
>>> from os import environ
>>> from cool_seq_tool.data_sources import SeqRepoAccess
.venv/lib/python3.11/site-packages/python_jsonschema_objects/__init__.py:46: UserWarning: Schema version http://json-schema.org/draft-07/schema not recognized. Some keywords and features may not be supported.
  warnings.warn(
>>> from biocommons.seqrepo import SeqRepo
>>> sr = SeqRepo(root_dir=environ["SEQREPO_ROOT_DIR"])
>>> seqrepo_access = SeqRepoAccess(sr)
>>> seqrepo_access.get_reference_sequence("NP_004324.2", 600, 600)
('V', None)
```

##### SeqRepo Issues

If you have trouble using the default path, try creating a symlink, by running the following:

```shell
seqrepo update-latest
```

Or set `SEQREPO_ROOT_DIR` in the `.env` file to the versioned SeqRepo path, i.e. `SEQREPO_ROOT_DIR=/usr/local/share/seqrepo/latest/2021-01-29`.

Verify that this works in [SeqRepo Verification](#seqrepo-verification).

#### Gene Normalizer DynamoDB

[VICC Gene Normalizer's](https://github.com/cancervariants/gene-normalization/tree/v0.1.39) is used to normalize genes and get gene concept data. You must set up the Gene Normalizer's database. The DynamoDB instance was used in this analysis. The PostgreSQL instance is not supported for running notebooks. We provide a quick way to get the DynamoDB instance running in [Using Gene Normalizer DynamoDB in s3](#using-gene-normalizer-dynamodb-in-s3).

##### AWS Environment Variables for DynamoDB

If you do not have an AWS account, you can keep `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` as is. Local DynamoDB instances will allow dummy credentials.

##### Using Gene Normalizer DynamoDB in s3

To immediately connect to the DynamoDB instance used in this analysis, [download the instance](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/shared-local-instance.db.zip) and extract. You will then [download the local archive](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html) (Download DynamoDB local v1.x was used), extract the contents, and move the `shared-local-instance.db` inside the `dynamodb_local_latest` directory (the relative path should be `dynamodb_local_latest/shared-local-instance.db`). Follow the [documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html) on how to start the database (you can skip steps 4 and 5).

When starting the DynamoDB database using the default configs, you should see the following:

```shell
Initializing DynamoDB Local with the following configuration:
Port:   8000
InMemory:       false
DbPath: null
SharedDb:       true
shouldDelayTransientStatuses:   false
CorsParams:     *

ERROR StatusLogger Log4j2 could not find a logging implementation. Please add log4j-core to the classpath. Using SimpleLogger to log to the console...
```

If your output looks a little different, you can verify the installation [here](#dynamodb-verification).

**Keep the database connected when running the notebooks.**

##### Gene Normalizer ETL files

The source files used during ETL methods have been uploaded to the public s3 bucket:

* Ensembl
  * [ensembl_110.gff3.zip](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/ensembl_110.gff3.zip)
* NCBI
  * [ncbi_GRCh38.p14.gff.zip](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/ncbi_GRCh38.p14.gff.zip)
  * [ncbi_history_20231114.tsv.zip](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/ncbi_history_20231114.tsv.zip)
  * [ncbi_info_20231114.tsv.zip](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/ncbi_info_20231114.tsv.zip)
* HGNC
  * [hgnc_20231114.json.zip](https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/gene-normalizer/hgnc_20231114.json.zip)

##### DynamoDB Verification

To verify, run the following inside your virtual environment:

```shell
$ python3
Python 3.11.5 (main, Aug 24 2023, 15:18:16) [Clang 14.0.3 (clang-1403.0.22.14.1)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from dotenv import load_dotenv
>>> load_dotenv()
True
>>> from gene.query import QueryHandler
.venv/lib/python3.11/site-packages/python_jsonschema_objects/__init__.py:46: UserWarning: Schema version http://json-schema.org/draft-07/schema not recognized. Some keywords and features may not be supported.
  warnings.warn(
>>> from gene.database import create_db
>>> q = QueryHandler(create_db())
***Using Gene Database Endpoint: http://localhost:8000***
>>> result = q.normalize("BRAF")
>>> result.gene_descriptor.gene_id
'hgnc:1097'
```

#### Biocommons UTA Database

[Biocommons UTA](https://github.com/biocommons/uta) is used to get transcript alignment data. You must set up the UTA database for [Cool-Seq-Tool](https://github.com/GenomicMedLab/cool-seq-tool/tree/v0.1.14-dev1). This analysis used the [uta_20210129](https://dl.biocommons.org/uta/uta_20210129.pgd.gz) version.

More information for a local UTA database installation can be found [here](https://github.com/GenomicMedLab/cool-seq-tool/tree/v0.1.14-dev1#uta-database-installation). A local installation was used when running this analysis.

You can also install with Docker (faster set up) as described [here](https://github.com/biocommons/uta#installing-with-docker-preferred). The [uta_20210129b](https://hub.docker.com/layers/biocommons/uta/uta_20210129b/images/sha256-eee31414e43d794e88883e0c0c98e01ed525c7cbb98d072baced45f936d33255?context=explore) image should be used. This option was not used when running this analysis.

Once set up, you must update the `UTA_DB_URL` environment variable in the `.env` file with your credentials. If following the [Local Installation README](https://github.com/GenomicMedLab/cool-seq-tool/tree/v0.1.14-dev1#local-installation), your `UTA_DB_URL` would be set to `postgresql://uta_admin@localhost:5432/uta/uta_20210129`.

**_Note: Cool-Seq-Tool creates a new `genomic` table. To create, follow all of the steps in [UTA Verification](#uta-verification) section._**

##### UTA Verification

To verify, run the following inside your virtual environment:

```shell
python3 -m asyncio
asyncio REPL 3.11.5 (main, Aug 24 2023, 15:18:16) [Clang 14.0.3 (clang-1403.0.22.14.1)] on darwin
Use "await" directly instead of "asyncio.run()".
Type "help", "copyright", "credits" or "license" for more information.
>>> import asyncio
>>> from dotenv import load_dotenv
>>> load_dotenv()
True
>>> from cool_seq_tool.data_sources import UTADatabase
.venv/lib/python3.11/site-packages/python_jsonschema_objects/__init__.py:46: UserWarning: Schema version http://json-schema.org/draft-07/schema not recognized. Some keywords and features may not be supported.
  warnings.warn(
>>> uta_db = await UTADatabase.create()
>>> await uta_db.get_ac_from_gene("BRAF")
['NC_000007.14', 'NC_000007.13']
```

## Running Notebooks

This section provides information about the notebooks and the order that they should be run in.

1. Run the following notebook:
    * [analysis/download_s3_files.ipynb](./analysis/download_s3_files.ipynb)
      * Downloads files from public s3 bucket that are needed for the notebooks.
        * cool-seq-tool: `LRG_RefSeqGene_20231114`, `MANE.GRCh38.v1.3.summary.txt`, `transcript_mapping.tsv`
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
    * [analysis/civic/variation_analysis/transcript_variation_analysis.ipynb](./analysis/civic/variation_analysis/transcript_variation_analysis.ipynb)
      * Analysis on CIViC variants in the Transcript category
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

### Running Notebooks in Visual Studio Code (VS Code)

[VS Code](https://code.visualstudio.com/) is a lightweight source code editor for Windows, Linux, and macOS.

1. Download VS Code [here](https://code.visualstudio.com/Download)
2. Open a notebook and click `Select Kernel` at the top right. Select the option where the path is `venv/3.11/bin/python`. See [here](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management) for more information on managing Jupyter Kernels in VS Code.
3. Run the notebooks

## Analysis with macOS Environments

These notebooks were run using these macOS specs:

| Model Year | CPU Architecture | Total RAM | Hard drive capacity |
| --- | --- | --- | --- |
| 2019 | 2.6 GHz 6-Core Intel Core i7 | 32 GB | 1 TB |
| 2021 | M1 Pro | 32 GB | 1 TB |

## Help

If you have any questions or problems, please [make an issue](https://github.com/GenomicMedLab/variation-normalizer-manuscript/issues/new) in the repo and our team will be happy to assist.
