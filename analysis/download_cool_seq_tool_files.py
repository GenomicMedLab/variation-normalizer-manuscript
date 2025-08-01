"""Download Cool Seq Tool files used in the analysis"""

from pathlib import Path
from types import MappingProxyType
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import os


BUCKET_NAME = "nch-igm-wagner-lab-public"
PREFIX = "variation-normalizer-manuscript/2025/cool_seq_tool/"
WAGS_TAIL_DIR = Path("wags_tails")
# Cool-Seq-Tool file name to environment variable path and subdirectory
CST_MAPPINGS = MappingProxyType(
    {
        "ncbi_mane_summary_1.4.txt": ("MANE_SUMMARY_PATH", "ncbi_mane_summary"),
        "ncbi_mane_refseq_genomic_1.4.gff": (
            "MANE_REFSEQ_GENOMIC_PATH",
            "ncbi_mane_refseq_genomic",
        ),
        "ncbi_lrg_refseqgene_20250720.tsv": (
            "LRG_REFSEQGENE_PATH",
            "ncbi_lrg_refseqgene",
        ),
        "chainfile_hg19_to_hg38_.chain": ("LIFTOVER_CHAIN_37_TO_38", "ucsc-chainfile"),
        "chainfile_hg38_to_hg19_.chain": ("LIFTOVER_CHAIN_38_TO_37", "ucsc-chainfile"),
    }
)


def download_cool_seq_tool_files(is_docker_env: bool = True) -> None:
    """Download cool seq tool files from public s3 bucket and set env vars

    :param is_docker_env: Whether or not docker environment is being used
    """
    if is_docker_env:
        wags_tails_dir = WAGS_TAIL_DIR
    else:
        wags_tails_dir = Path.home() / ".local" / "share" / "wags_tails"

    wags_tails_dir.mkdir(exist_ok=True, parents=True)
    cst_files_not_downloaded = set()

    for cst_fn, v in CST_MAPPINGS.items():
        env_var, subdir = v
        wags_tails_subdir = wags_tails_dir / subdir
        wags_tails_subdir.mkdir(exist_ok=True, parents=True)
        filepath = f"{wags_tails_subdir}/{cst_fn}"

        if not is_docker_env:
            os.environ[env_var] = filepath

        if not os.path.exists(filepath):
            cst_files_not_downloaded.add(cst_fn)

    if cst_files_not_downloaded:
        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)

        for obj in response["Contents"]:
            key = obj["Key"]

            if key.endswith("/"):
                continue

            fn = key.split("/")[-1]

            if fn in cst_files_not_downloaded:
                _dir = wags_tails_dir / CST_MAPPINGS[fn][1]
                local_path = os.path.join(_dir, fn)
                s3.download_file(BUCKET_NAME, key, local_path)


if __name__ == "__main__":
    download_cool_seq_tool_files(is_docker_env=True)
