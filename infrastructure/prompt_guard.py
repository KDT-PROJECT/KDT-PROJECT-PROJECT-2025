"""
프롬프트 인젝션 보호 가드
악의적인 프롬프트 인젝션을 감지하고 차단
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PromptInjectionGuard:
    """프롬프트 인젝션 보호 가드 클래스"""
    
    def __init__(self):
        """프롬프트 가드 초기화"""
        # 프롬프트 인젝션 패턴
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything',
            r'you\s+are\s+now',
            r'pretend\s+to\s+be',
            r'act\s+as\s+if',
            r'roleplay\s+as',
            r'system\s+prompt',
            r'jailbreak',
            r'bypass',
            r'override',
            r'ignore\s+all\s+rules',
            r'disregard\s+instructions',
            r'new\s+instructions',
            r'override\s+system',
            r'break\s+character',
            r'act\s+out\s+of\s+character'
        ]
        
        # 한국어 프롬프트 인젝션 패턴
        self.korean_injection_patterns = [
            r'이전\s+지시사항\s+무시',
            r'모든\s+것\s+잊어',
            r'이제\s+너는',
            r'~인\s+척\s+해',
            r'~처럼\s+행동',
            r'역할\s+놀이',
            r'시스템\s+프롬프트',
            r'탈옥',
            r'우회',
            r'덮어쓰기',
            r'모든\s+규칙\s+무시',
            r'지시사항\s+무시',
            r'새로운\s+지시사항',
            r'시스템\s+덮어쓰기',
            r'캐릭터\s+깨기',
            r'캐릭터\s+벗어나기'
        ]
        
        # 의심스러운 키워드
        self.suspicious_keywords = [
            'hack', 'exploit', 'vulnerability', 'backdoor',
            'admin', 'root', 'sudo', 'privilege',
            'injection', 'payload', 'malware', 'virus',
            '해킹', '취약점', '백도어', '관리자',
            '권한', '인젝션', '페이로드', '악성코드'
        ]
    
    def is_safe(self, text: str) -> bool:
        """
        텍스트가 안전한지 확인
        
        Args:
            text: 확인할 텍스트
            
        Returns:
            bool: 안전하면 True, 인젝션 시도시 False
        """
        try:
            if not text or not isinstance(text, str):
                return True
            
            text_lower = text.lower()
            
            # 영어 프롬프트 인젝션 패턴 검사
            for pattern in self.injection_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    logger.warning(f"프롬프트 인젝션 패턴 감지: {pattern}")
                    return False
            
            # 한국어 프롬프트 인젝션 패턴 검사
            for pattern in self.korean_injection_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.warning(f"한국어 프롬프트 인젝션 패턴 감지: {pattern}")
                    return False
            
            # 의심스러운 키워드 검사
            for keyword in self.suspicious_keywords:
                if keyword in text_lower:
                    logger.warning(f"의심스러운 키워드 감지: {keyword}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"프롬프트 인젝션 검사 중 오류: {e}")
            return False
    
    def detect_injection(self, text: str) -> Dict[str, List[str]]:
        """
        텍스트에서 프롬프트 인젝션 패턴을 감지
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            Dict[str, List[str]]: 감지된 패턴과 매치된 문자열들
        """
        detected = {
            'english_patterns': [],
            'korean_patterns': [],
            'suspicious_keywords': []
        }
        
        try:
            if not text or not isinstance(text, str):
                return detected
            
            text_lower = text.lower()
            
            # 영어 패턴 검사
            for pattern in self.injection_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    detected['english_patterns'].extend(matches)
            
            # 한국어 패턴 검사
            for pattern in self.korean_injection_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    detected['korean_patterns'].extend(matches)
            
            # 의심스러운 키워드 검사
            for keyword in self.suspicious_keywords:
                if keyword in text_lower:
                    detected['suspicious_keywords'].append(keyword)
            
            return detected
            
        except Exception as e:
            logger.error(f"프롬프트 인젝션 감지 중 오류: {e}")
            return detected
    
    def sanitize_text(self, text: str) -> str:
        """
        텍스트에서 프롬프트 인젝션 패턴을 제거
        
        Args:
            text: 정화할 텍스트
            
        Returns:
            str: 정화된 텍스트
        """
        try:
            if not text or not isinstance(text, str):
                return text
            
            sanitized = text
            
            # 영어 패턴 제거
            for pattern in self.injection_patterns:
                sanitized = re.sub(pattern, '[제거됨]', sanitized, flags=re.IGNORECASE)
            
            # 한국어 패턴 제거
            for pattern in self.korean_injection_patterns:
                sanitized = re.sub(pattern, '[제거됨]', sanitized, flags=re.IGNORECASE)
            
            # 의심스러운 키워드 마스킹
            for keyword in self.suspicious_keywords:
                sanitized = sanitized.replace(keyword, '[마스킹됨]')
            
            return sanitized
            
        except Exception as e:
            logger.error(f"텍스트 정화 중 오류: {e}")
            return text


def get_prompt_guard() -> PromptInjectionGuard:
    """프롬프트 가드 인스턴스 반환"""
    return PromptInjectionGuard()
