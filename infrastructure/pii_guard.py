"""
PII (개인정보) 보호 가드
개인정보가 포함된 질의를 감지하고 차단
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PIIGuard:
    """개인정보 보호 가드 클래스"""
    
    def __init__(self):
        """PII 가드 초기화"""
        # 개인정보 패턴 정의
        self.pii_patterns = {
            'korean_phone': r'01[0-9]-\d{4}-\d{4}',
            'korean_phone_alt': r'01[0-9]\d{8}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\d{6}-\d{7}',
            'credit_card': r'\d{4}-\d{4}-\d{4}-\d{4}',
            'korean_name': r'[가-힣]{2,4}(?=\s|$|[^\w가-힣])',  # 실제 개인명만 (예: 홍길동, 김철수)
            'specific_address': r'[가-힣]+(시|구|동|로|길)\s*[0-9-]+',  # 구체적인 주소만 (예: 강남구 테헤란로 123)
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        }
        
        # 민감한 키워드
        self.sensitive_keywords = [
            '주민등록번호', '주민번호', '생년월일', '생일',
            '전화번호', '휴대폰', '핸드폰', '연락처',
            '이메일', '메일', '주소', '거주지',
            '신용카드', '계좌번호', '카드번호',
            '개인정보', '신상정보', '본인정보'
        ]
    
    def is_safe(self, text: str) -> bool:
        """
        텍스트가 안전한지 확인
        
        Args:
            text: 확인할 텍스트
            
        Returns:
            bool: 안전하면 True, 개인정보 포함시 False
        """
        try:
            if not text or not isinstance(text, str):
                return True
            
            text_lower = text.lower()
            
            # 상권 분석 관련 키워드가 포함된 경우 더 관대하게 검사
            commercial_keywords = [
                '매출', '상권', '지역', '구', '동', '업종', '매장', '점포',
                '분석', '데이터', '통계', '보고서', '스타벅스', '맥도날드',
                '강남구', '서초구', '송파구', '마포구', '용산구', '중구',
                '서초동', '역삼동', '논현동', '도곡동', '개포동', '모두의연구소',
                '카페', '음식점', '상점', '쇼핑', '업무', '사무실', '오피스'
            ]
            
            has_commercial_context = any(keyword in text_lower for keyword in commercial_keywords)
            
            # 상권 분석 맥락에서는 대부분의 질의를 허용
            if has_commercial_context:
                # 실제 개인정보만 차단 (전화번호, 이메일, 주민번호 등)
                real_pii_patterns = {
                    'korean_phone': r'01[0-9]-\d{4}-\d{4}',
                    'korean_phone_alt': r'01[0-9]\d{8}',
                    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'ssn': r'\d{6}-\d{7}',
                    'credit_card': r'\d{4}-\d{4}-\d{4}-\d{4}',
                    'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                }
                
                # 실제 개인정보 패턴만 검사
                for pattern_name, pattern in real_pii_patterns.items():
                    matches = re.findall(pattern, text)
                    if matches:
                        logger.warning(f"실제 PII 패턴 감지 ({pattern_name}): {matches}")
                        return False
                
                # 민감한 키워드 중 실제 개인정보만 차단
                real_sensitive_keywords = [
                    '주민등록번호', '주민번호', '생년월일', '생일',
                    '전화번호', '휴대폰', '핸드폰', '연락처',
                    '이메일', '메일', '신용카드', '계좌번호', '카드번호',
                    '개인정보', '신상정보', '본인정보'
                ]
                
                for keyword in real_sensitive_keywords:
                    if keyword in text_lower:
                        logger.warning(f"실제 민감한 키워드 감지: {keyword}")
                        return False
                
                return True
            
            # 상권 분석 맥락이 아닌 경우 기존 검사 수행
            for keyword in self.sensitive_keywords:
                if keyword in text_lower:
                    logger.warning(f"민감한 키워드 감지: {keyword}")
                    return False
            
            for pattern_name, pattern in self.pii_patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    logger.warning(f"PII 패턴 감지 ({pattern_name}): {matches}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"PII 검사 중 오류: {e}")
            return False
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        텍스트에서 개인정보 패턴을 감지
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            Dict[str, List[str]]: 감지된 패턴과 매치된 문자열들
        """
        detected = {}
        
        try:
            if not text or not isinstance(text, str):
                return detected
            
            # PII 패턴 검사
            for pattern_name, pattern in self.pii_patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    detected[pattern_name] = matches
            
            # 민감한 키워드 검사
            text_lower = text.lower()
            keyword_matches = []
            for keyword in self.sensitive_keywords:
                if keyword in text_lower:
                    keyword_matches.append(keyword)
            
            if keyword_matches:
                detected['sensitive_keywords'] = keyword_matches
            
            return detected
            
        except Exception as e:
            logger.error(f"PII 감지 중 오류: {e}")
            return detected
    
    def sanitize_text(self, text: str) -> str:
        """
        텍스트에서 개인정보를 마스킹
        
        Args:
            text: 마스킹할 텍스트
            
        Returns:
            str: 마스킹된 텍스트
        """
        try:
            if not text or not isinstance(text, str):
                return text
            
            sanitized = text
            
            # PII 패턴 마스킹
            for pattern_name, pattern in self.pii_patterns.items():
                sanitized = re.sub(pattern, '[마스킹됨]', sanitized)
            
            # 민감한 키워드 마스킹
            for keyword in self.sensitive_keywords:
                sanitized = sanitized.replace(keyword, '[마스킹됨]')
            
            return sanitized
            
        except Exception as e:
            logger.error(f"텍스트 마스킹 중 오류: {e}")
            return text


def get_pii_guard() -> PIIGuard:
    """PII 가드 인스턴스 반환"""
    return PIIGuard()
