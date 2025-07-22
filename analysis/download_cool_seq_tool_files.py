"""Download Cool Seq Tool files used in the analysis"""

from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import os


BUCKET_NAME = "nch-igm-wagner-lab-public"
PREFIX = "variation-normalizer-manuscript/2025/cool_seq_tool/"
WAGS_TAIL_DIR = "wags_tails"
COOL_SEQ_TOOL_FILES = [
    "ncbi_mane_summary_1.4.txt",
    "ncbi_mane_refseq_genomic_1.4.gff",
    "ncbi_lrg_refseqgene_20250720.tsv",
    "chainfile_hg19_to_hg38_.chain",
    "chainfile_hg38_to_hg19_.chain",
]


def download_cool_seq_tool_files():
    Path(WAGS_TAIL_DIR).mkdir(exist_ok=True)
    cst_files_not_downloaded = set()

    for cst_fn in COOL_SEQ_TOOL_FILES:
        if not os.path.exists(f"{WAGS_TAIL_DIR}/{cst_fn}"):
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
                local_path = os.path.join(WAGS_TAIL_DIR, fn)
                s3.download_file(BUCKET_NAME, key, local_path)


if __name__ == "__main__":
    download_cool_seq_tool_files()
