#!/usr/bin/env python3
"""
서울 상권 지도 분석 앱 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    """지도 앱 실행"""
    print("🗺️ 서울 상권 지도 분석 앱을 시작합니다...")
    
    # 필요한 패키지 설치 확인
    try:
        import streamlit
        import folium
        import plotly
        print("✅ 필요한 패키지가 설치되어 있습니다.")
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령어로 패키지를 설치하세요:")
        print("pip install streamlit folium plotly streamlit-folium")
        return
    
    # 환경 변수 확인
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        print("⚠️  GOOGLE_MAPS_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Google Maps API 키를 설정하면 더 정확한 지도를 사용할 수 있습니다.")
        print("env.example 파일을 참고하여 .env 파일을 생성하세요.")
    
    # Streamlit 앱 실행
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app_map.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 앱이 종료되었습니다.")
    except Exception as e:
        print(f"❌ 앱 실행 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
