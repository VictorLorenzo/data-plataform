#!/usr/bin/env bash
# Creates the same bucket/folder layout as minio/docker-compose.yml's createbucket
# service, but against Cloudflare R2. Requires ./.env (copy .env.example first).
set -euo pipefail
cd "$(dirname "$0")"

set -a
source .env
set +a

docker run --rm \
  -e AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
  -e AWS_EC2_METADATA_DISABLED=true \
  --entrypoint /bin/sh \
  amazon/aws-cli -c '
    set -eu
    ENDPOINT="https://'"$R2_ACCOUNT_ID${R2_JURISDICTION:+.$R2_JURISDICTION}"'.r2.cloudflarestorage.com"

    for bucket in datalake-landing datalake-bronze datalake-silver datalake-gold datalake-uc; do
      aws s3api create-bucket --bucket "$bucket" --endpoint-url "$ENDPOINT"
    done

    # S3-compatible stores have no real directories; an empty object with a
    # trailing-slash key acts as the folder marker, same as "mc mb bucket/prefix".
    aws s3api put-object --bucket datalake-landing --key spark-events/ --endpoint-url "$ENDPOINT"
    aws s3api put-object --bucket datalake-uc --key warehouse/ --endpoint-url "$ENDPOINT"
  '

echo "Done. Buckets created in R2 account $R2_ACCOUNT_ID."
