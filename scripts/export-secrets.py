#!/usr/bin/env python3
"""
AWS Secrets Manager에서 환경변수를 로드하고 export 형식으로 출력
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError

# Add app to path
sys.path.insert(0, '/app')

def load_and_export_secrets():
    """시크릿을 로드하고 export 형식으로 출력"""
    
    secret_name = "cdl/ai/env"
    region = "ap-northeast-2"
    
    # boto3 클라이언트 생성 (IAM 역할 사용)
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        
        # 시크릿 조회
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        
        # JSON 파싱
        secret_data = json.loads(secret_string)
        
        # export 형식으로 출력
        for key, value in secret_data.items():
            # 쉘에서 안전하게 사용할 수 있도록 값을 인용
            safe_value = str(value).replace("'", "'\\''")
            print(f"export {key}='{safe_value}'")
            
        return True
            
    except Exception as e:
        print(f"# Error loading secrets: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if not load_and_export_secrets():
        sys.exit(1)
