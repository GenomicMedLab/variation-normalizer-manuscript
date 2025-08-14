"""Module containing utility functions and enums"""

import json
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import List, Dict
import ast
import pandas as pd

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

    SEQUENCE = "Sequence"
    GENOTYPE_AND_HAPLOTYPE = "Genotype/Haplotype"
    FUSION = "Fusion"
    REARRANGEMENT = "Rearrangement"
    EPIGENETIC_MODIFICATION = "Epigenetic Modification"
    COPY_NUMBER = "Copy Number"
    EXPRESSION = "Expression"
    GENE_FUNCTION = "Gene Function"
    REGION_DEFINED = "Region-Defined"
    GENOME_FEATURE = "Genome Feature"
    OTHER = "Other"
    TRANSCRIPT = "Transcript"  # no attempt to normalize these ones, since there is no query we could use


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
            Path(f"{ROOT_PATH}/moa/feature_analysis").glob("moa_assertions_*.zip")
        )[-1]
    json_fn = latest_zip_path.name[:-4]
    print(f"Using {json_fn} for MOA {item_type.value}s")

    with zipfile.ZipFile(latest_zip_path, "r") as zip_ref:
        zip_ref.extractall()

    with open(json_fn, "r") as f:
        items = json.load(f)

    return items


def get_errors(errors: str) -> str:
    """Takes the values for the errors and represents them as a string
    :param errors: A string representation of a list of errors or None
    :return: string or list representing error. If None, the string "Success"
        is returned
    """
    if pd.isna(errors):
        return "Success"

    # Parse if it's a stringified list/dict
    try:
        errors = ast.literal_eval(errors)
    except Exception:
        return errors  # return raw string if not a valid list or dict

    errors_out = []

    # Normalize to list
    if not isinstance(errors, list):
        errors = [errors]

    for e in errors:
        if isinstance(e, str):
            errors_out.append(e)
        elif isinstance(e, dict):
            for k, v in e.items():
                if k not in ["msg", "response-errors"]:
                    continue
                if isinstance(v, str):
                    errors_out.append(v)
                elif isinstance(v, list):
                    errors_out.extend(v)  # multiple error messages
    return "; ".join(errors_out)
