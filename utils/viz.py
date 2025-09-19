"""
시각화 모듈
PRD TASK1: Plotly 기반 시각화 함수 스텁
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = None) -> Optional[go.Figure]:
    """
    라인 차트 생성 함수
    
    Args:
        df: 데이터프레임
        x_col: X축 컬럼명
        y_col: Y축 컬럼명
        title: 차트 제목
        
    Returns:
        Plotly Figure 객체
    """
    try:
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            logger.warning("데이터가 없거나 컬럼이 존재하지 않습니다.")
            return None
        
        # 기본 제목 설정
        if not title:
            title = f"{y_col} by {x_col}"
        
        # 라인 차트 생성
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col, y_col: y_col}
        )
        
        # 레이아웃 설정
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            hovermode='x unified',
            showlegend=True
        )
        
        logger.info(f"라인 차트 생성 완료: {title}")
        return fig
        
    except Exception as e:
        logger.error(f"라인 차트 생성 실패: {str(e)}")
        return None

def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = None) -> Optional[go.Figure]:
    """
    바 차트 생성 함수
    
    Args:
        df: 데이터프레임
        x_col: X축 컬럼명
        y_col: Y축 컬럼명
        title: 차트 제목
        
    Returns:
        Plotly Figure 객체
    """
    try:
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            logger.warning("데이터가 없거나 컬럼이 존재하지 않습니다.")
            return None
        
        # 기본 제목 설정
        if not title:
            title = f"{y_col} by {x_col}"
        
        # 바 차트 생성
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col, y_col: y_col}
        )
        
        # 레이아웃 설정
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            hovermode='x unified',
            showlegend=True
        )
        
        logger.info(f"바 차트 생성 완료: {title}")
        return fig
        
    except Exception as e:
        logger.error(f"바 차트 생성 실패: {str(e)}")
        return None

def create_pie_chart(df: pd.DataFrame, names_col: str, values_col: str, title: str = None) -> Optional[go.Figure]:
    """
    파이 차트 생성 함수
    
    Args:
        df: 데이터프레임
        names_col: 이름 컬럼명
        values_col: 값 컬럼명
        title: 차트 제목
        
    Returns:
        Plotly Figure 객체
    """
    try:
        if df.empty or names_col not in df.columns or values_col not in df.columns:
            logger.warning("데이터가 없거나 컬럼이 존재하지 않습니다.")
            return None
        
        # 기본 제목 설정
        if not title:
            title = f"{values_col} Distribution"
        
        # 파이 차트 생성
        fig = px.pie(
            df, 
            names=names_col, 
            values=values_col,
            title=title
        )
        
        # 레이아웃 설정
        fig.update_layout(
            hovermode='x unified',
            showlegend=True
        )
        
        logger.info(f"파이 차트 생성 완료: {title}")
        return fig
        
    except Exception as e:
        logger.error(f"파이 차트 생성 실패: {str(e)}")
        return None

def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None, title: str = None) -> Optional[go.Figure]:
    """
    산점도 생성 함수
    
    Args:
        df: 데이터프레임
        x_col: X축 컬럼명
        y_col: Y축 컬럼명
        color_col: 색상 구분 컬럼명 (선택사항)
        title: 차트 제목
        
    Returns:
        Plotly Figure 객체
    """
    try:
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            logger.warning("데이터가 없거나 컬럼이 존재하지 않습니다.")
            return None
        
        # 기본 제목 설정
        if not title:
            title = f"{y_col} vs {x_col}"
        
        # 산점도 생성
        if color_col and color_col in df.columns:
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col,
                color=color_col,
                title=title,
                labels={x_col: x_col, y_col: y_col}
            )
        else:
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col,
                title=title,
                labels={x_col: x_col, y_col: y_col}
            )
        
        # 레이아웃 설정
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            hovermode='closest',
            showlegend=True
        )
        
        logger.info(f"산점도 생성 완료: {title}")
        return fig
        
    except Exception as e:
        logger.error(f"산점도 생성 실패: {str(e)}")
        return None