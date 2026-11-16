#!/usr/bin/env bash
# Delete everything FoodLoop created (stops all cost). Buckets must be emptied first.
set -euo pipefail
STACK="${STACK:-foodloop}"; REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
out() { aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
read -r -p "Delete stack '$STACK' in $REGION and ALL its data? [y/N] " ok; [ "$ok" = "y" ] || exit 1
for b in "$(out FrontendBucketName)" "$(out ImageBucketName)"; do aws s3 rm "s3://$b" --recursive --region "$REGION" || true; done
aws cloudformation delete-stack --stack-name "$STACK" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK" --region "$REGION"
echo "Deleted."
