"""Download Cool Seq Tool files used in the analysis"""

from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import os

BUCKET_NAME = "nch-igm-wagner-lab-public"
PREFIX = "variation-normalizer-manuscript/2025/cool_seq_tool/"
WAGS_TAIL_DIR = "wags_tails"

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
Path(WAGS_TAIL_DIR).mkdir(exist_ok=True)
response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)

for obj in response["Contents"]:
    key = obj["Key"]
    if key.endswith("/"):
        continue

    fn = key.split("/")[-1]
    local_path = os.path.join(WAGS_TAIL_DIR, fn)
    s3.download_file(BUCKET_NAME, key, local_path)
