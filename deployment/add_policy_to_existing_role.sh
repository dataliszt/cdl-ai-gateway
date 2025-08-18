#!/bin/bash
#
# 기존 IAM 역할에 Secrets Manager 권한 추가 스크립트
# 이미 EC2/ECS에 역할이 연결되어 있을 때 사용
#

set -e

echo "🔧 기존 IAM 역할에 Secrets Manager 권한 추가"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 현재 인스턴스의 역할 확인 (EC2에서 실행 시)
echo -e "\n${YELLOW}1. 현재 역할 확인${NC}"

# EC2 메타데이터에서 역할 이름 가져오기 (EC2에서만 동작)
if curl -s http://169.254.169.254/latest/meta-data/ > /dev/null 2>&1; then
    CURRENT_ROLE=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    if [ ! -z "$CURRENT_ROLE" ]; then
        echo -e "${GREEN}현재 EC2 인스턴스 역할: ${CURRENT_ROLE}${NC}"
        ROLE_NAME=$CURRENT_ROLE
    fi
else
    echo "EC2 인스턴스가 아니거나 메타데이터 접근 불가"
    echo -n "역할 이름을 입력하세요: "
    read ROLE_NAME
fi

# 2. 역할 존재 확인
echo -e "\n${YELLOW}2. 역할 정보 확인${NC}"
aws iam get-role --role-name $ROLE_NAME > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 역할 확인됨: $ROLE_NAME${NC}"
else
    echo -e "${RED}❌ 역할을 찾을 수 없습니다: $ROLE_NAME${NC}"
    exit 1
fi

# 3. 현재 연결된 정책 확인
echo -e "\n${YELLOW}3. 현재 연결된 정책 확인${NC}"
echo "Managed Policies:"
aws iam list-attached-role-policies --role-name $ROLE_NAME \
    --query 'AttachedPolicies[*].[PolicyName,PolicyArn]' \
    --output table

echo -e "\nInline Policies:"
aws iam list-role-policies --role-name $ROLE_NAME \
    --query 'PolicyNames' \
    --output json

# 4. Secrets Manager 정책 생성
echo -e "\n${YELLOW}4. Secrets Manager 정책 생성${NC}"

POLICY_NAME="CDLGatewaySecretsAccess"
REGION="ap-northeast-2"

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

# 5. 정책을 역할에 추가 (Inline Policy로)
echo -e "\n${YELLOW}5. 정책을 역할에 추가${NC}"

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name $POLICY_NAME \
    --policy-document file:///tmp/secrets-policy.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 정책이 성공적으로 추가되었습니다!${NC}"
else
    echo -e "${RED}❌ 정책 추가 실패${NC}"
    exit 1
fi

# 6. 권한 테스트
echo -e "\n${YELLOW}6. 권한 테스트${NC}"

# 시크릿 접근 테스트
echo "Secrets Manager 접근 테스트..."
aws secretsmanager get-secret-value \
    --secret-id cdl/ai/env \
    --region $REGION \
    --query 'Name' \
    --output text > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Secrets Manager 접근 성공!${NC}"
else
    echo -e "${YELLOW}⚠️ 시크릿이 없거나 접근 실패 (시크릿이 아직 생성되지 않았을 수 있음)${NC}"
fi

# 7. 애플리케이션 재시작 안내
echo -e "\n${GREEN}=========================================="
echo "✅ 설정 완료!"
echo "=========================================="
echo -e "${NC}"
echo "이제 애플리케이션을 재시작하면 자동으로 Secrets Manager에서"
echo "환경변수를 로드합니다."
echo ""
echo "재시작 명령어:"
echo "  docker restart cdl-gateway"
echo "  또는"
echo "  systemctl restart cdl-gateway"

# 임시 파일 정리
rm -f /tmp/secrets-policy.json