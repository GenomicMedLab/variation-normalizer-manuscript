"""Module containing utility functions and enums"""
import json
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import List, Dict

from civicpy import civic as civicpy


ROOT_PATH = Path(__file__).resolve().parent


class MoaItemType(StrEnum):
    """Create enum for the kind of MOA items that will be analyzed."""

    FEATURE = "feature"
    ASSERTION = "assertion"


class NotSupportedVariantCategory(StrEnum):
    """Create enum for the kind of variants that are not supported by the variation-normalizer."""

    EXPRESSION = "Expression Variants"
    EPIGENETIC_MODIFICATION = "Epigenetic Modification"
    FUSION = "Fusion Variants"
    SEQUENCE_VARS = "Sequence Variants"
    GENE_FUNC = "Gene Function Variants"
    REARRANGEMENTS = "Rearrangement Variants"
    COPY_NUMBER = "Copy Number Variants"
    OTHER = "Other Variants"
    GENOTYPES = "Genotype Variants"
    REGION_DEFINED_VAR = "Region Defined Variants"
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
