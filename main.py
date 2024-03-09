import os

import ipaddress
import json

from cdktf import App, TerraformStack, S3Backend, S3BackendEndpointConfig
from constructs import Construct

from imports.cloudflare.provider import CloudflareProvider
from imports.cloudflare.record import Record

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            key, value = line.strip().split("=")
            os.environ[key] = value

CLOUDFLARE_API_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ZONE_ID = os.getenv("ZONE_ID")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")

with open("records.json") as f:
    target_mapping = json.load(f)


def verify(name, record):
    if not ipaddress.ip_address(record).is_private:
        return False
    return True


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        CloudflareProvider(self, "cloudflare", api_token=CLOUDFLARE_API_TOKEN)
        S3Backend(self,
                  bucket=S3_BUCKET,
                  key="terraform.tfstate",
                  encrypt=True,
                  endpoints=S3BackendEndpointConfig(
                      s3=S3_ENDPOINT
                  ),
                  access_key=S3_ACCESS_KEY,
                  secret_key=S3_SECRET_KEY,
                  region="us-east-01",
                  skip_s3_checksum=True,
                  skip_requesting_account_id=True,
                  skip_metadata_api_check=True,
                  skip_region_validation=True,
                  skip_credentials_validation=True,
                  )

        for name, record in target_mapping.items():
            if not verify(name, record):
                print(f"ERROR: {name}:{record} is not private ip")
                exit(-1)

        for name, record in target_mapping.items():
            Record(self, id_=f"record_{name}", zone_id=ZONE_ID, name=name, type="A", value=record)


app = App()
MyStack(app, "homeinfra_subdomains")
app.synth()
