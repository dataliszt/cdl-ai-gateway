#!/usr/bin/env python3
"""
AWS Secrets Manager에서 환경변수 로드
액세스 키로 시크릿을 가져와서 환경변수로 설정
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def load_secrets_to_env():
    """AWS Secrets Manager에서 시크릿을 가져와서 환경변수로 설정"""
    
    secret_name = "cdl/ai/env"
    region_name = "ap-northeast-2"
    
    try:
        # AWS 자격증명으로 boto3 클라이언트 생성 
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        # 시크릿 값 가져오기
        print(f"🔍 시크릿 조회 중: {secret_name}")
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        
        # JSON 파싱
        secret_data = json.loads(secret_string)
        print(f"✅ 시크릿 로드 성공: {len(secret_data)}개 항목")
        
        # 환경변수로 설정 (AWS 시크릿이 우선순위)
        for key, value in secret_data.items():
            # 기존 환경변수가 있어도 AWS 시크릿으로 덮어쓰기
            old_value = os.environ.get(key, 'NOT_SET')
            os.environ[key] = str(value)
            
            # 패스워드는 마스킹해서 출력
            display_value = '*' * len(str(value)) if 'password' in key.lower() or 'secret' in key.lower() or 'key' in key.lower() else value
            
            if old_value != 'NOT_SET' and old_value != str(value):
                print(f"  🔄 {key} = {display_value} (overridden)")
            else:
                print(f"  📝 {key} = {display_value}")
        
        print(f"✅ 총 {len(secret_data)}개 환경변수 설정 완료")
        return True
        
    except NoCredentialsError:
        print("❌ AWS 자격 증명을 찾을 수 없습니다.")
        print("\n환경변수로 AWS 자격증명을 설정하세요:")
        print("export AWS_ACCESS_KEY_ID=your_access_key")
        print("export AWS_SECRET_ACCESS_KEY=your_secret_key")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ 시크릿을 찾을 수 없습니다: {secret_name}")
        elif error_code == 'AccessDeniedException':
            print(f"❌ 접근 권한이 없습니다: {secret_name}")
        else:
            print(f"❌ AWS 오류: {e}")
        return False
        
    except json.JSONDecodeError:
        print(f"❌ 시크릿이 올바른 JSON 형식이 아닙니다: {secret_name}")
        return False
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


if __name__ == "__main__":
    print("🚀 AWS Secrets Manager에서 환경변수 로드 중...")
    
    if load_secrets_to_env():
        print("🎉 환경변수 로드 완료!")
        
        # 중요 환경변수 확인
        print("\n📋 주요 환경변수 확인:")
        check_vars = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
            'RABBITMQ_USER', 'RABBITMQ_HOSTNAME', 'RABBITMQ_PORT',
            'AWS_REGION', 'LOG_LEVEL', 'ENVIRONMENT'
        ]
        for var in check_vars:
            value = os.getenv(var, 'NOT_SET')
            # API 키들은 마스킹
            if 'API_KEY' in var or 'PASSWORD' in var:
                value = '*' * 10 if value != 'NOT_SET' else 'NOT_SET'
            print(f"  {var}: {value}")
    else:
        print("💥 환경변수 로드 실패!")
        sys.exit(1)