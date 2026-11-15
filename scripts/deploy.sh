#!/usr/bin/env bash
# One-command manual deploy (no CI/CD pipeline - this is a "No Pipeline, No Problem" project).
#   ./scripts/deploy.sh                      # deploy to ap-south-1 (Mumbai, closest AWS region to Sri Lanka)
#   AWS_REGION=us-east-1 STACK=foodloop-dev ./scripts/deploy.sh
#   AUTO_APPROVE_ORGS=false ./scripts/deploy.sh   # production behaviour: admin must approve orgs
set -euo pipefail
cd "$(dirname "$0")/.."

STACK="${STACK:-foodloop}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
export SAM_CLI_TELEMETRY=0

echo "==> Backend: sam build + deploy ($STACK in $REGION)"
sam build
sam deploy --stack-name "$STACK" --region "$REGION" --resolve-s3 \
  --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset \
  --parameter-overrides "AutoApproveOrgs=${AUTO_APPROVE_ORGS:-true}"

out() { aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

echo "==> Frontend: configure, build, upload"
cat > frontend/.env.production <<ENV
VITE_API_URL=$(out ApiUrl)
VITE_REGION=$REGION
VITE_USER_POOL_CLIENT_ID=$(out UserPoolClientId)
VITE_IMAGE_BASE_URL=$(out ImageBaseUrl)
ENV
(cd frontend && npm ci && npm run build)

BUCKET="$(out FrontendBucketName)"
aws s3 sync frontend/dist "s3://$BUCKET" --delete --exclude index.html \
  --cache-control "public,max-age=31536000,immutable"
aws s3 cp frontend/dist/index.html "s3://$BUCKET/index.html" --cache-control "no-cache" --content-type "text/html"
aws cloudfront create-invalidation --distribution-id "$(out DistributionId)" --paths "/index.html" >/dev/null

echo
echo "FoodLoop is live:  $(out SiteUrl)"
echo "Next: ./scripts/seed.py --stack $STACK --region $REGION   (demo accounts + sample listings)"
