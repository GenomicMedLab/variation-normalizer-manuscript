"""Module containing utility functions and enums"""
import json
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import List, Dict
import requests
from pathlib import Path

from civicpy import civic as civicpy


ROOT_PATH = Path(__file__).resolve().parent


class MoaItemType(StrEnum):
    """Create enum for the kind of MOA items that will be analyzed."""

    FEATURE = "feature"
    ASSERTION = "assertion"


class NotSupportedVariantCategory(StrEnum):
    """Create enum for the kind of variants that are not supported by the variation-normalizer.
    Note: Order matters for performance final figure.
    """

    SEQUENCE_VARS = "Sequence Variants"
    GENOTYPES_AND_HAPLOTYPES = "Genotypes/Haplotypes"
    FUSION = "Fusion Variants"
    REARRANGEMENTS = "Rearrangement Variants"
    EPIGENETIC_MODIFICATION = "Epigenetic Modification"
    COPY_NUMBER = "Copy Number Variants"
    EXPRESSION = "Expression Variants"
    GENE_FUNC = "Gene Function Variants"
    REGION_DEFINED_VAR = "Region-Defined Variants"
    GENOME_FEATURES = "Genome Features"
    OTHER = "Other Variants"
    TRANSCRIPT_VAR = "Transcript Variants"  # no attempt to normalize these ones, since there is no query we could use


NOT_SUPPORTED_VARIANT_CATEGORY_VALUES = [
    v.value for v in NotSupportedVariantCategory.__members__.values()
]


def load_civicpy_cache() -> None:
    """Load latest civicpy cache zip"""
    latest_cache_zip_path = sorted(Path(f"{ROOT_PATH}/civic").glob("cache-*.pkl.zip"))[
        -1
    ]
    print(f"Using {latest_cache_zip_path.name[:-4]} for civicpy cache")

    with zipfile.ZipFile(latest_cache_zip_path, "r") as zip_ref:
        zip_ref.extractall(f"{ROOT_PATH}/civic")

    civicpy.load_cache(
        local_cache_path=Path(f"{ROOT_PATH}/civic/cache.pkl"), on_stale="ignore"
    )


def load_latest_moa_zip(item_type: MoaItemType) -> List[Dict]:
    """Load MOA items from latest zip file

    :item_type: Type of items to retrieve
    :return: List of MOA items
    """
    if item_type == MoaItemType.FEATURE:
        latest_zip_path = sorted(
            Path(f"{ROOT_PATH}/moa/feature_analysis").glob("moa_features_*.zip")
        )[-1]
    else:
        latest_zip_path = sorted(
            Path(f"{ROOT_PATH}/moa/assertion_analysis").glob("moa_assertions_*.zip")
        )[-1]
    json_fn = latest_zip_path.name[:-4]
    print(f"Using {json_fn} for MOA {item_type.value}s")

    with zipfile.ZipFile(latest_zip_path, "r") as zip_ref:
        zip_ref.extractall()

    with open(json_fn, "r") as f:
        items = json.load(f)

    return items

MANUSCRIPT_S3_URL = "https://nch-igm-wagner-lab-public.s3.us-east-2.amazonaws.com/variation-normalizer-manuscript/2025"

def download_s3(url: str, outfile_path: Path) -> None:
    """Download objects from public s3 bucket

    :param url: URL for file in s3 bucket
    :param outfile_path: Path where file should be saved
    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(outfile_path, "wb") as h:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    h.write(chunk)

base_dir = Path(__file__).parent.resolve()
clinvar_dir = base_dir / "clinvar"
clinvar_dir.mkdir(exist_ok=True)

url = f"{MANUSCRIPT_S3_URL}/clinvar/vi-normalized-with-liftover.jsonl.gz"
outfile_path = clinvar_dir / "vi-normalized-with-liftover.jsonl.gz"
download_s3(url, outfile_path)
