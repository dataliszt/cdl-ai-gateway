#!/bin/bash
#
# EC2 인스턴스 프로파일 설정 스크립트
# IAM 역할을 사용하여 AWS 자격증명 없이 Secrets Manager 접근
#

set -e

echo "🚀 EC2 인스턴스 프로파일 설정 시작"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 변수 설정
ROLE_NAME="cdl-gateway-ec2-role"
INSTANCE_PROFILE_NAME="cdl-gateway-instance-profile"
POLICY_NAME="cdl-gateway-secrets-policy"
REGION="ap-northeast-2"

echo -e "${YELLOW}1. IAM 역할 생성${NC}"

# Trust relationship policy
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# IAM 역할 생성
aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --description "IAM role for CDL Gateway EC2 instances" \
    2>/dev/null || echo "역할이 이미 존재합니다."

echo -e "${YELLOW}2. IAM 정책 생성 및 연결${NC}"

# Secrets Manager 접근 정책
cat > /tmp/secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:${REGION}:*:secret:cdl/ai/env*"
      ]
    },
    {
      "Sid": "AllowListSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# 정책 생성
POLICY_ARN=$(aws iam create-policy \
    --policy-name ${POLICY_NAME} \
    --policy-document file:///tmp/secrets-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null) || \
POLICY_ARN=$(aws iam list-policies \
    --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" \
    --output text)

# 정책을 역할에 연결
aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

echo -e "${YELLOW}3. 인스턴스 프로파일 생성${NC}"

# 인스턴스 프로파일 생성
aws iam create-instance-profile \
    --instance-profile-name ${INSTANCE_PROFILE_NAME} \
    2>/dev/null || echo "인스턴스 프로파일이 이미 존재합니다."

# 역할을 인스턴스 프로파일에 추가
aws iam add-role-to-instance-profile \
    --instance-profile-name ${INSTANCE_PROFILE_NAME} \
    --role-name ${ROLE_NAME} \
    2>/dev/null || echo "역할이 이미 연결되어 있습니다."

echo -e "${GREEN}✅ IAM 설정 완료!${NC}"

echo -e "\n${YELLOW}4. EC2 인스턴스에 프로파일 연결${NC}"
echo "다음 중 하나의 방법을 사용하세요:"

echo -e "\n${GREEN}A. 새 EC2 인스턴스 생성 시:${NC}"
echo "aws ec2 run-instances \\"
echo "    --image-id ami-xxxxxxxx \\"
echo "    --instance-type t3.medium \\"
echo "    --iam-instance-profile Name=${INSTANCE_PROFILE_NAME} \\"
echo "    --key-name your-key-pair \\"
echo "    --security-group-ids sg-xxxxxxxx \\"
echo "    --subnet-id subnet-xxxxxxxx"

echo -e "\n${GREEN}B. 기존 EC2 인스턴스에 연결:${NC}"
echo "INSTANCE_ID=i-xxxxxxxx"
echo "aws ec2 associate-iam-instance-profile \\"
echo "    --iam-instance-profile Name=${INSTANCE_PROFILE_NAME} \\"
echo "    --instance-id \$INSTANCE_ID"

echo -e "\n${GREEN}C. AWS 콘솔에서:${NC}"
echo "1. EC2 콘솔 → 인스턴스 선택"
echo "2. Actions → Security → Modify IAM role"
echo "3. '${INSTANCE_PROFILE_NAME}' 선택"

echo -e "\n${YELLOW}5. 테스트 명령어${NC}"
echo "# EC2 인스턴스에서 실행:"
echo "aws secretsmanager get-secret-value \\"
echo "    --secret-id cdl/ai/env \\"
echo "    --region ${REGION}"

echo -e "\n${GREEN}✅ 설정 완료!${NC}"
echo "이제 EC2 인스턴스에서 AWS 자격증명 없이 Secrets Manager에 접근할 수 있습니다."

# 임시 파일 정리
rm -f /tmp/trust-policy.json /tmp/secrets-policy.json