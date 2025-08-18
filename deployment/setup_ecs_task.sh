#!/bin/bash
#
# ECS 태스크 역할 설정 스크립트
# Fargate/ECS에서 AWS 자격증명 없이 Secrets Manager 접근
#

set -e

echo "🚀 ECS 태스크 역할 설정 시작"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 변수 설정
TASK_ROLE_NAME="cdl-gateway-ecs-task-role"
EXECUTION_ROLE_NAME="cdl-gateway-ecs-execution-role"
POLICY_NAME="cdl-gateway-secrets-policy"
REGION="ap-northeast-2"

echo -e "${YELLOW}1. ECS 태스크 역할 생성${NC}"

# ECS 태스크 Trust relationship
cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 태스크 역할 생성
aws iam create-role \
    --role-name ${TASK_ROLE_NAME} \
    --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
    --description "Task role for CDL Gateway ECS tasks" \
    2>/dev/null || echo "태스크 역할이 이미 존재합니다."

# 실행 역할 생성 (컨테이너 이미지 풀 및 로그 전송용)
aws iam create-role \
    --role-name ${EXECUTION_ROLE_NAME} \
    --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
    --description "Execution role for CDL Gateway ECS tasks" \
    2>/dev/null || echo "실행 역할이 이미 존재합니다."

echo -e "${YELLOW}2. 태스크 역할에 Secrets Manager 정책 연결${NC}"

# Secrets Manager 접근 정책
cat > /tmp/task-secrets-policy.json <<EOF
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

# 정책 생성 또는 가져오기
POLICY_ARN=$(aws iam create-policy \
    --policy-name ${POLICY_NAME} \
    --policy-document file:///tmp/task-secrets-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null) || \
POLICY_ARN=$(aws iam list-policies \
    --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" \
    --output text)

# 태스크 역할에 정책 연결
aws iam attach-role-policy \
    --role-name ${TASK_ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

echo -e "${YELLOW}3. 실행 역할에 필수 정책 연결${NC}"

# 실행 역할에 AWS 관리형 정책 연결
aws iam attach-role-policy \
    --role-name ${EXECUTION_ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 실행 역할에도 Secrets Manager 정책 연결 (환경변수로 시크릿 주입 시 필요)
aws iam attach-role-policy \
    --role-name ${EXECUTION_ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

echo -e "${GREEN}✅ IAM 역할 설정 완료!${NC}"

echo -e "\n${YELLOW}4. ECS 태스크 정의 예제${NC}"

cat > /tmp/task-definition.json <<EOF
{
  "family": "cdl-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/${TASK_ROLE_NAME}",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/${EXECUTION_ROLE_NAME}",
  "containerDefinitions": [
    {
      "name": "cdl-gateway",
      "image": "YOUR_ECR_URI/cdl-gateway:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "AWS_REGION",
          "value": "${REGION}"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${REGION}:YOUR_ACCOUNT_ID:secret:cdl/ai/env:OPENAI_API_KEY::"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${REGION}:YOUR_ACCOUNT_ID:secret:cdl/ai/env:ANTHROPIC_API_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cdl-gateway",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

echo -e "${GREEN}태스크 정의 예제가 /tmp/task-definition.json에 생성되었습니다.${NC}"

echo -e "\n${YELLOW}5. 태스크 정의 등록${NC}"
echo "# 계정 ID 확인"
echo "ACCOUNT_ID=\$(aws sts get-caller-identity --query Account --output text)"
echo ""
echo "# 태스크 정의 파일 수정 (YOUR_ACCOUNT_ID 교체)"
echo "sed -i \"s/YOUR_ACCOUNT_ID/\$ACCOUNT_ID/g\" /tmp/task-definition.json"
echo ""
echo "# 태스크 정의 등록"
echo "aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json"

echo -e "\n${YELLOW}6. 서비스 생성 예제${NC}"
echo "aws ecs create-service \\"
echo "    --cluster your-cluster-name \\"
echo "    --service-name cdl-gateway \\"
echo "    --task-definition cdl-gateway:1 \\"
echo "    --desired-count 2 \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration \"awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}\""

echo -e "\n${GREEN}✅ 설정 완료!${NC}"
echo "이제 ECS/Fargate에서 AWS 자격증명 없이 Secrets Manager에 접근할 수 있습니다."

# 임시 파일 정리
rm -f /tmp/ecs-trust-policy.json /tmp/task-secrets-policy.json