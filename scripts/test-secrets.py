#!/usr/bin/env python3
"""
AWS Secrets Manager 연결 테스트 스크립트
EC2/ECS 환경에서 실행하여 IAM 역할 및 권한을 검증합니다.
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_aws_connectivity():
    """AWS 연결 및 권한 테스트"""
    print("=" * 60)
    print("🔍 AWS Secrets Manager 연결 테스트")
    print("=" * 60)
    
    # 1. 환경 정보 출력
    print("\n📋 환경 정보:")
    print(f"  Python: {sys.version}")
    print(f"  Boto3: {boto3.__version__}")
    print(f"  AWS_REGION: {os.getenv('AWS_REGION', 'not set')}")
    print(f"  AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION', 'not set')}")
    
    # 자격증명 확인 (값은 마스킹)
    if os.getenv('AWS_ACCESS_KEY_ID'):
        print(f"  AWS_ACCESS_KEY_ID: ***{os.getenv('AWS_ACCESS_KEY_ID')[-4:]}")
    else:
        print("  AWS_ACCESS_KEY_ID: not set")
    
    if os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("  AWS_SECRET_ACCESS_KEY: [SET]")
    else:
        print("  AWS_SECRET_ACCESS_KEY: not set")
    
    if os.getenv('AWS_SESSION_TOKEN'):
        print("  AWS_SESSION_TOKEN: [SET]")
    else:
        print("  AWS_SESSION_TOKEN: not set")
    
    # 2. IAM 역할 확인
    print("\n🔐 IAM 역할 확인:")
    try:
        sts_client = boto3.client('sts', region_name='ap-northeast-2')
        identity = sts_client.get_caller_identity()
        print(f"  ✅ 현재 자격증명:")
        print(f"     Account: {identity['Account']}")
        print(f"     UserId: {identity['UserId']}")
        print(f"     Arn: {identity['Arn']}")
        
        # EC2 인스턴스 역할인지 확인
        if 'assumed-role' in identity['Arn']:
            role_name = identity['Arn'].split('/')[1]
            print(f"  📌 사용 중인 IAM 역할: {role_name}")
        elif 'user' in identity['Arn']:
            user_name = identity['Arn'].split('/')[-1]
            print(f"  📌 사용 중인 IAM 사용자: {user_name}")
            
    except NoCredentialsError:
        print("  ❌ AWS 자격증명을 찾을 수 없습니다")
        print("     - EC2/ECS: IAM 역할이 연결되어 있는지 확인하세요")
        print("     - 로컬: AWS CLI가 구성되어 있는지 확인하세요")
        return False
    except Exception as e:
        print(f"  ❌ IAM 확인 실패: {e}")
        return False
    
    # 3. Secrets Manager 권한 테스트
    print("\n🔑 Secrets Manager 권한 테스트:")
    secret_name = "cdl/ai/env"
    region = os.getenv('AWS_REGION', 'ap-northeast-2')
    
    try:
        sm_client = boto3.client('secretsmanager', region_name=region)
        
        # 시크릿 목록 조회 권한 테스트
        print("  테스트 1: 시크릿 목록 조회...")
        try:
            response = sm_client.list_secrets(MaxResults=1)
            print(f"  ✅ 시크릿 목록 조회 가능 ({len(response.get('SecretList', []))}개 확인)")
        except ClientError as e:
            print(f"  ⚠️ 시크릿 목록 조회 실패: {e.response['Error']['Code']}")
        
        # 특정 시크릿 조회 권한 테스트
        print(f"\n  테스트 2: 시크릿 '{secret_name}' 조회...")
        try:
            response = sm_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            print(f"  ✅ 시크릿 조회 성공! ({len(secret_data)}개 키 포함)")
            
            # 주요 키 확인 (값은 표시하지 않음)
            expected_keys = [
                'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
                'RABBITMQ_USER', 'RABBITMQ_PASSWORD', 'RABBITMQ_HOSTNAME'
            ]
            
            print("\n  📋 시크릿 키 확인:")
            for key in expected_keys:
                if key in secret_data:
                    print(f"     ✅ {key}: [존재]")
                else:
                    print(f"     ❌ {key}: [누락]")
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"  ❌ 시크릿 '{secret_name}'을 찾을 수 없습니다")
                print("     해결방법: AWS Secrets Manager에서 시크릿을 생성하세요")
            elif error_code == 'AccessDeniedException':
                print(f"  ❌ 시크릿 '{secret_name}'에 대한 접근 권한이 없습니다")
                print("\n  💡 필요한 IAM 정책:")
                print("  {")
                print('    "Version": "2012-10-17",')
                print('    "Statement": [')
                print('      {')
                print('        "Effect": "Allow",')
                print('        "Action": [')
                print('          "secretsmanager:GetSecretValue"')
                print('        ],')
                print('        "Resource": [')
                print(f'          "arn:aws:secretsmanager:{region}:*:secret:{secret_name}*"')
                print('        ]')
                print('      }')
                print('    ]')
                print('  }')
            else:
                print(f"  ❌ 시크릿 조회 실패: {error_code}")
                print(f"     메시지: {e.response['Error']['Message']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Secrets Manager 연결 실패: {e}")
        return False
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    success = test_aws_connectivity()
    
    if success:
        print("\n✅ AWS Secrets Manager 연결 테스트 성공!")
        print("   컨테이너가 정상적으로 시크릿을 로드할 수 있습니다.")
    else:
        print("\n❌ AWS Secrets Manager 연결 테스트 실패!")
        print("\n💡 해결 방법:")
        print("1. EC2/ECS 인스턴스에 적절한 IAM 역할 연결")
        print("2. IAM 역할에 secretsmanager:GetSecretValue 권한 추가")
        print("3. 시크릿 'cdl/ai/env'가 존재하는지 확인")
        sys.exit(1)