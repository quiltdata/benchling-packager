#!/bin/bash

set -euo pipefail

error() {
    echo $@ 2>&1
    exit 1
}

[ "$#" -eq 0 ] || error "Usage: $0"

zip_file="benchling-packager-layer.$(python -c 'import hashlib, pathlib; print(hashlib.sha256(pathlib.Path("requirements.txt").read_bytes()).hexdigest())').zip"
exec_dir=$(realpath .)
work_dir=$(realpath "$(mktemp -d)")
echo "Using $work_dir as a work directory."
cd "$work_dir"

echo "Installing packages..."
python3 -m pip install \
    --platform manylinux2014_x86_64 \
    --target=./python/lib/python3.9/site-packages \
    --implementation cp \
    --python 3.9 \
    --no-deps \
    --no-compile \
    -r $exec_dir/requirements.txt

echo "Compressing..."
zip -9 -r "$zip_file" "."

primary_region=us-east-1
regions=$(aws ec2 describe-regions --query "Regions[].{Name:RegionName}" --output text)

s3_key="benchling-packager/$zip_file"

echo "Uploading to $primary_region..."
aws s3 cp --acl public-read "$zip_file" "s3://quilt-lambda-$primary_region/$s3_key"

cd ..
rm -rf "$work_dir"

for region in $regions
do
    if [ "$region" != "$primary_region" ]
    then
        echo "Copying to $region..."
        aws s3 cp --acl public-read "s3://quilt-lambda-$primary_region/$s3_key" "s3://quilt-lambda-$region/$s3_key" --region "$region" --source-region "$primary_region"
    fi
done

echo "Deployed $s3_key"
