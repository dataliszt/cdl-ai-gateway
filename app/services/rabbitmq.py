"""
RabbitMQ 클러스터 클라이언트
다중 노드 fallback, 자동 재연결, 회로 차단기 패턴 구현
"""
import ssl
import json
import pika
import logging
import time
import random
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """노드 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RabbitMQClusterClient:
    """
    RabbitMQ 클러스터 클라이언트
    - 다중 노드 자동 fallback
    - 회로 차단기 패턴
    - 연결 상태 모니터링
    - 자동 재시도 및 백오프
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.cluster_nodes = settings.get_rabbitmq_nodes()
        self.current_node_index = 0
        self.node_status = {}
        self.connection_attempts = {}
        self.last_successful_node = None
        
        # 초기화
        self._initialize_node_status()
        self._connect_to_cluster()
    
    def _initialize_node_status(self):
        """모든 노드 상태를 초기화"""
        for i, node in enumerate(self.cluster_nodes):
            node_key = f"{node['host']}:{node['port']}"
            self.node_status[node_key] = NodeStatus.UNKNOWN
            self.connection_attempts[node_key] = 0
    
    def _connect_to_cluster(self) -> bool:
        """
        클러스터 노드들을 순차적으로 시도하여 연결
        우선순위: 마지막 성공 노드 → 건강한 노드 → 모든 노드
        """
        # 1. 마지막 성공 노드부터 시도
        if self.last_successful_node is not None:
            if self._try_connect_to_node(self.last_successful_node):
                return True
        
        # 2. 건강한 노드들 시도
        healthy_nodes = [i for i, node in enumerate(self.cluster_nodes) 
                        if self._get_node_status(i) == NodeStatus.HEALTHY]
        for node_index in healthy_nodes:
            if self._try_connect_to_node(node_index):
                return True
        
        # 3. 모든 노드 시도 (실패한 노드 포함)
        for node_index in range(len(self.cluster_nodes)):
            if self._try_connect_to_node(node_index):
                return True
        
        logger.error("Failed to connect to any RabbitMQ cluster nodes")
        return False
    
    def _try_connect_to_node(self, node_index: int) -> bool:
        """특정 노드에 연결 시도"""
        node = self.cluster_nodes[node_index]
        node_key = f"{node['host']}:{node['port']}"
        
        # 회로 차단기: 너무 많이 실패한 노드는 건너뛰기
        if self.connection_attempts.get(node_key, 0) >= settings.rabbitmq_retry_attempts:
            current_time = time.time()
            # 5분마다 재시도 허용
            if not hasattr(self, '_last_circuit_reset') or current_time - self._last_circuit_reset > 300:
                self.connection_attempts[node_key] = 0
                self._last_circuit_reset = current_time
            else:
                logger.debug(f"Circuit breaker active for {node_key}")
                return False
        
        try:
            logger.info(f"Attempting to connect to RabbitMQ node: {node_key}")
            
            # 연결 파라미터 설정
            connection_params = pika.ConnectionParameters(
                host=node['host'],
                port=node['port'],
                credentials=pika.PlainCredentials(
                    username=node['user'],
                    password=node['password']
                ),
                connection_attempts=1,
                retry_delay=settings.rabbitmq_retry_delay,
                socket_timeout=settings.rabbitmq_connection_timeout,
                heartbeat=settings.rabbitmq_heartbeat,
                blocked_connection_timeout=settings.rabbitmq_connection_timeout,
            )
            
            # 연결 시도
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # 연결 성공
            self.current_node_index = node_index
            self.last_successful_node = node_index
            self.node_status[node_key] = NodeStatus.HEALTHY
            self.connection_attempts[node_key] = 0
            
            logger.info(f"Successfully connected to RabbitMQ node: {node_key}")
            return True
            
        except Exception as e:
            self.connection_attempts[node_key] = self.connection_attempts.get(node_key, 0) + 1
            self.node_status[node_key] = NodeStatus.FAILED
            
            logger.warning(
                f"Failed to connect to RabbitMQ node {node_key} "
                f"(attempt {self.connection_attempts[node_key]}): {e}"
            )
            return False
    
    def _get_node_status(self, node_index: int) -> NodeStatus:
        """노드 상태 조회"""
        node = self.cluster_nodes[node_index]
        node_key = f"{node['host']}:{node['port']}"
        return self.node_status.get(node_key, NodeStatus.UNKNOWN)
    
    def _ensure_connection(self) -> bool:
        """연결 상태 확인 및 필요시 재연결"""
        try:
            # 기존 연결이 살아있는지 확인
            if self.connection and not self.connection.is_closed:
                if self.channel and not self.channel.is_closed:
                    # 간단한 heartbeat 체크
                    self.connection.process_data_events(time_limit=1)
                    return True
            
            logger.info("Connection lost, attempting to reconnect...")
            self.close()
            return self._connect_to_cluster()
            
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            self.close()
            return self._connect_to_cluster()
    
    def queue_exists(self, queue_name: str) -> bool:
        """큐 존재 여부 확인"""
        if not self._ensure_connection():
            raise ConnectionError("Failed to establish RabbitMQ connection")
        
        try:
            # passive=True: 큐가 존재하지 않으면 예외 발생
            self.channel.queue_declare(queue=queue_name, passive=True)
            return True
        except pika.exceptions.ChannelClosedByBroker:
            # 큐가 존재하지 않음
            self.channel = self.connection.channel()  # 채널 재생성
            return False
        except Exception as e:
            logger.error(f"Error checking queue existence for {queue_name}: {e}")
            return False
    
    def declare_queue(self, queue_name: str, **kwargs) -> bool:
        """큐 선언 (Quorum Queue 사용)"""
        if not self._ensure_connection():
            raise ConnectionError("Failed to establish RabbitMQ connection")
        
        try:
            # 기본 설정: Quorum Queue, 지속성, 메시지 지속성 활성화
            default_kwargs = {
                'queue': queue_name,
                'durable': True,  # Quorum queues는 항상 durable
                'exclusive': False,  # Quorum queues는 exclusive 불가
                'auto_delete': False,  # Quorum queues는 auto_delete 불가
                'arguments': {
                    'x-queue-type': 'quorum',  # Quorum Queue 타입 지정
                    'x-quorum-initial-group-size': settings.quorum_initial_group_size,  # 초기 quorum 그룹 크기
                    'x-delivery-limit': settings.quorum_delivery_limit,  # 재배달 제한 (Dead Letter 처리용)
                    'x-max-in-memory-length': settings.quorum_max_in_memory_length,  # 메모리에 보관할 최대 메시지 수
                    'x-max-in-memory-bytes': settings.quorum_max_in_memory_bytes  # 메모리에 보관할 최대 바이트
                }
            }
            
            # 사용자 정의 arguments가 있으면 병합
            if 'arguments' in kwargs:
                default_kwargs['arguments'].update(kwargs['arguments'])
                kwargs.pop('arguments')
            
            default_kwargs.update(kwargs)
            
            self.channel.queue_declare(**default_kwargs)
            logger.info(f"Quorum queue declared: {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {e}")
            return False
    
    def send_message(
        self, 
        exchange: str, 
        routing_key: str, 
        body: Dict[str, Any], 
        priority: int = 0,
        retry_count: int = 3
    ) -> bool:
        """
        메시지 전송 (재시도 로직 포함)
        
        Args:
            exchange: 익스체인지 이름
            routing_key: 라우팅 키 (일반적으로 큐 이름)
            body: 메시지 본문
            priority: 메시지 우선순위
            retry_count: 재시도 횟수
            
        Returns:
            전송 성공 여부
        """
        for attempt in range(retry_count + 1):
            try:
                if not self._ensure_connection():
                    if attempt == retry_count:
                        raise ConnectionError("Failed to establish RabbitMQ connection after retries")
                    time.sleep(settings.rabbitmq_retry_delay * (2 ** attempt))  # 지수 백오프
                    continue
                
                # 메시지 속성 설정
                properties = pika.BasicProperties(
                    delivery_mode=2,  # 메시지 지속성
                    priority=priority,
                    timestamp=int(time.time()),
                    content_type='application/json',
                    headers={
                        'sender': 'cdl-gateway',
                        'cluster_node': f"{self.cluster_nodes[self.current_node_index]['host']}:"
                                      f"{self.cluster_nodes[self.current_node_index]['port']}"
                    }
                )
                
                # 메시지 전송
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=json.dumps(body, ensure_ascii=False),
                    properties=properties
                )
                
                logger.debug(f"Message sent to {routing_key} via node {self.current_node_index}")
                return True
                
            except Exception as e:
                logger.error(
                    f"Failed to send message to {routing_key} "
                    f"(attempt {attempt + 1}/{retry_count + 1}): {e}"
                )
                
                if attempt < retry_count:
                    # 다른 노드로 fallback 시도
                    self.close()
                    time.sleep(settings.rabbitmq_retry_delay * (2 ** attempt))
                    continue
                else:
                    return False
        
        return False
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """클러스터 상태 정보 반환"""
        status_info = {
            "total_nodes": len(self.cluster_nodes),
            "current_node_index": self.current_node_index,
            "connected": self.connection is not None and not self.connection.is_closed,
            "nodes": []
        }
        
        for i, node in enumerate(self.cluster_nodes):
            node_key = f"{node['host']}:{node['port']}"
            status_info["nodes"].append({
                "index": i,
                "host": node['host'],
                "port": node['port'],
                "status": self.node_status.get(node_key, NodeStatus.UNKNOWN).value,
                "connection_attempts": self.connection_attempts.get(node_key, 0),
                "is_current": i == self.current_node_index
            })
        
        return status_info
    
    def close(self):
        """연결 종료"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
        except Exception as e:
            logger.debug(f"Error closing channel: {e}")
        
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
        
        self.channel = None
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for connection handling"""
        try:
            if not self._ensure_connection():
                raise ConnectionError("Failed to establish RabbitMQ connection")
            yield self
        except Exception as e:
            logger.error(f"Error in connection context: {e}")
            raise
        finally:
            # 연결 유지 (재사용을 위해)
            pass


# 기존 호환성을 위한 별칭들
class MessageSender(RabbitMQClusterClient):
    """기존 MessageSender 호환성"""
    pass


class RabbitMQClient(RabbitMQClusterClient):
    """기존 RabbitMQClient 호환성"""
    pass


# 싱글톤 인스턴스 (선택적 사용)
_cluster_client_instance = None


def get_rabbitmq_client() -> RabbitMQClusterClient:
    """
    RabbitMQ 클러스터 클라이언트 싱글톤 인스턴스 반환
    멀티스레드 환경에서는 각 스레드별로 별도 인스턴스 사용 권장
    """
    global _cluster_client_instance
    if _cluster_client_instance is None:
        _cluster_client_instance = RabbitMQClusterClient()
    return _cluster_client_instance