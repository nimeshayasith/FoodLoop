#!/usr/bin/env bash
# Give an existing user the "admin" role (can approve businesses/charities).  ./scripts/make-admin.sh you@example.com
set -euo pipefail
EMAIL="${1:?usage: make-admin.sh <email>}"
STACK="${STACK:-foodloop}"; REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
POOL="$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)"
aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" --region "$REGION" --username "$EMAIL" --group-name admin
echo "$EMAIL is now an admin. Sign out and in again to refresh the token."
