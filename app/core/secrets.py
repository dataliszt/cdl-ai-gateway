#!/usr/bin/env python3
"""
향상된 AWS Secrets Manager 로더
EC2 인스턴스 프로파일, ECS 태스크 역할, 환경변수 순으로 자격증명 시도
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any


class SecretsManager:
    """AWS Secrets Manager 통합 클래스"""
    
    def __init__(self, secret_name: str = "cdl/ai/env", region: str = "ap-northeast-2"):
        self.secret_name = secret_name
        self.region = region
        self.client = None
        self.is_loaded = False
        
    def _get_client(self) -> Optional[boto3.client]:
        """다양한 방법으로 boto3 클라이언트 생성 시도"""
        
        # 1. EC2 인스턴스 프로파일 / ECS 태스크 역할 사용 (프로덕션)
        try:
            print("🔍 IAM 역할 기반 인증 시도 중...")
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=self.region
            )
            # 테스트 호출로 권한 확인
            client.list_secrets(MaxResults=1)
            print("✅ IAM 역할 인증 성공!")
            return client
        except Exception as e:
            print(f"ℹ️ IAM 역할 사용 불가: {str(e)[:50]}...")
            
        # 2. 환경변수에서 자격증명 확인 (개발/테스트)
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            try:
                print("🔍 환경변수 자격증명 사용 중...")
                client = boto3.client(
                    service_name='secretsmanager',
                    region_name=self.region,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                print("✅ 환경변수 인증 성공!")
                return client
            except Exception as e:
                print(f"❌ 환경변수 인증 실패: {e}")
                
        # 3. AWS CLI 프로파일 사용 (로컬 개발)
        try:
            print("🔍 AWS CLI 기본 프로파일 시도 중...")
            session = boto3.Session(profile_name='default')
            client = session.client(
                service_name='secretsmanager',
                region_name=self.region
            )
            print("✅ AWS CLI 프로파일 인증 성공!")
            return client
        except Exception:
            pass
            
        return None
        
    def load_secrets(self) -> bool:
        """시크릿을 로드하여 환경변수로 설정"""
        
        if self.is_loaded:
            print("ℹ️ 시크릿이 이미 로드되었습니다.")
            return True
            
        # 클라이언트 획득
        self.client = self._get_client()
        if not self.client:
            print("\n❌ AWS 인증 실패!")
            print("\n다음 방법 중 하나를 사용하세요:")
            print("1. EC2/ECS에서 실행: IAM 역할 자동 사용")
            print("2. 환경변수 설정:")
            print("   export AWS_ACCESS_KEY_ID=xxx")
            print("   export AWS_SECRET_ACCESS_KEY=xxx")
            print("3. AWS CLI 설정: aws configure")
            return False
            
        try:
            # 시크릿 조회
            print(f"🔍 시크릿 조회 중: {self.secret_name}")
            response = self.client.get_secret_value(SecretId=self.secret_name)
            secret_string = response['SecretString']
            
            # JSON 파싱
            secret_data = json.loads(secret_string)
            print(f"✅ 시크릿 로드 성공: {len(secret_data)}개 항목")
            
            # 환경변수 설정
            for key, value in secret_data.items():
                os.environ[key] = str(value)
                
                # 민감 정보 마스킹
                if any(sensitive in key.lower() for sensitive in ['key', 'password', 'secret', 'token']):
                    display_value = '***' + str(value)[-4:] if len(str(value)) > 4 else '****'
                else:
                    display_value = value
                    
                print(f"  📝 {key} = {display_value}")
                
            self.is_loaded = True
            print(f"✅ 총 {len(secret_data)}개 환경변수 설정 완료")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"❌ 시크릿을 찾을 수 없습니다: {self.secret_name}")
            elif error_code == 'AccessDeniedException':
                print(f"❌ 접근 권한이 없습니다: {self.secret_name}")
                print("\nIAM 정책에 다음 권한이 필요합니다:")
                print("- secretsmanager:GetSecretValue")
                print(f"- Resource: arn:aws:secretsmanager:{self.region}:*:secret:{self.secret_name}*")
            else:
                print(f"❌ AWS 오류: {e}")
            return False
            
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
            
    def get_secret(self, key: str) -> Optional[str]:
        """특정 시크릿 값 조회"""
        return os.getenv(key)
        

# 싱글톤 인스턴스
_secrets_manager = None


def get_secrets_manager() -> SecretsManager:
    """싱글톤 SecretsManager 인스턴스 반환"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def load_secrets_to_env() -> bool:
    """하위 호환성을 위한 래퍼 함수"""
    manager = get_secrets_manager()
    return manager.load_secrets()


if __name__ == "__main__":
    print("🚀 향상된 AWS Secrets Manager 로더")
    print("=" * 60)
    
    manager = get_secrets_manager()
    
    if manager.load_secrets():
        print("\n🎉 환경변수 로드 완료!")
        
        # 주요 환경변수 확인
        print("\n📋 주요 환경변수 확인:")
        check_vars = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
            'RABBITMQ_USER', 'RABBITMQ_HOSTNAME', 'RABBITMQ_PORT',
            'AWS_REGION', 'LOG_LEVEL', 'ENVIRONMENT'
        ]
        for var in check_vars:
            value = manager.get_secret(var)
            if value:
                if 'KEY' in var or 'PASSWORD' in var:
                    value = '***' + value[-4:] if len(value) > 4 else '****'
                print(f"  {var}: {value}")
            else:
                print(f"  {var}: NOT_SET")
    else:
        print("\n💥 환경변수 로드 실패!")
        sys.exit(1)