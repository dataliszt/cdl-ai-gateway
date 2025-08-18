# AWS Secrets Manager IAM 역할 설정 가이드

## 1. EC2 인스턴스용 IAM 역할 생성

### AWS 콘솔에서 설정

1. **IAM 콘솔 접속**
   - https://console.aws.amazon.com/iam/
   - 좌측 메뉴에서 "역할(Roles)" 클릭

2. **역할 생성**
   - "역할 만들기" 버튼 클릭
   - 신뢰할 수 있는 엔터티 유형: "AWS 서비스"
   - 사용 사례: "EC2" 선택
   - 다음 버튼 클릭

3. **권한 정책 연결**
   - "정책 생성" 버튼 클릭하여 새 정책 생성
   - JSON 탭 선택 후 아래 정책 입력:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-2:*:secret:cdl/ai/env*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
```

4. **역할 이름 지정**
   - 역할 이름: `cdl-gateway-secrets-role`
   - 설명: "CDL Gateway용 Secrets Manager 접근 역할"

5. **EC2 인스턴스에 역할 연결**
   - EC2 콘솔로 이동
   - 대상 인스턴스 선택
   - 작업 → 보안 → IAM 역할 수정
   - `cdl-gateway-secrets-role` 선택

## 2. ECS Task용 IAM 역할 (ECS 사용 시)

### Task Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-2:*:secret:cdl/ai/env*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## 3. AWS CLI로 테스트

```bash
# IAM 역할 확인
aws sts get-caller-identity

# 시크릿 조회 테스트
aws secretsmanager get-secret-value \
  --secret-id cdl/ai/env \
  --region ap-northeast-2

# 컨테이너 내에서 테스트
docker exec -it cdl-gateway-blue python scripts/test-secrets.py
```

## 4. 문제 해결

### 권한 오류 발생 시
1. CloudTrail에서 AccessDenied 이벤트 확인
2. IAM 역할 정책 검토
3. 시크릿 ARN이 정확한지 확인

### 자격증명 오류 발생 시
1. EC2 메타데이터 서비스 활성화 확인
2. Docker 컨테이너가 host 네트워크 모드가 아닌지 확인
3. AWS_REGION 환경변수 설정 확인

## 5. Docker Compose 환경변수 설정

`.env` 파일 (개발/테스트용):
```bash
# AWS 설정
AWS_REGION=ap-northeast-2
AWS_DEFAULT_REGION=ap-northeast-2

# 개발 환경에서만 사용 (프로덕션에서는 IAM 역할 사용)
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
```

## 6. 배포 체크리스트

- [ ] IAM 역할 생성 및 정책 연결
- [ ] EC2/ECS 인스턴스에 IAM 역할 연결
- [ ] AWS Secrets Manager에 `cdl/ai/env` 시크릿 생성
- [ ] 시크릿에 필요한 모든 환경변수 추가
- [ ] `scripts/test-secrets.py`로 연결 테스트
- [ ] Docker 컨테이너 재시작