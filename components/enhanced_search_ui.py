"""
Enhanced Search UI Components for External Web Search (Naver Style)
"""

import streamlit as st
from retrieval.web_search import search_web, search_images, search_videos
from typing import Dict, List, Any

class EnhancedSearchUI:
    """
    A class to render a Naver-style UI for web, image, and video search.
    """

    @staticmethod
    def _render_styles():
        """Renders the CSS for the Naver-style search UI."""
        st.markdown("""
        <style>
            /* Main container for the search section */
            .search-container {
                max-width: 800px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: #ffffff;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            }

            /* Search bar */
            .search-bar-wrapper {
                display: flex;
                align-items: center;
                border: 3px solid #03C75A;
                border-radius: 30px;
                padding: 5px;
                margin-bottom: 1.5rem;
            }
            .search-bar-wrapper .stTextArea textarea {
                border: none;
                height: 40px !important;
                padding-left: 15px;
                font-size: 1.1rem;
            }
            .search-bar-wrapper .stTextArea textarea:focus {
                box-shadow: none;
                outline: none;
            }
            .search-bar-wrapper .stButton button {
                background-color: #03C75A;
                color: white;
                border: none;
                border-radius: 25px;
                width: 50px;
                height: 50px;
                font-size: 1.5rem;
                line-height: 1;
            }
            .search-bar-wrapper .stButton button:hover {
                background-color: #02b350;
            }

            /* Search type buttons */
            .search-types {
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-bottom: 2rem;
            }
            .search-types .stButton button {
                border-radius: 20px;
                border: 1px solid #e0e0e0;
                background-color: #f8f9fa;
                color: #5f6368;
                font-weight: 500;
                transition: all 0.2s;
            }
            .search-types .stButton button:hover {
                background-color: #e9ecef;
                border-color: #ced4da;
            }
            .search-types .stButton button.active {
                background-color: #03C75A;
                color: white;
                border-color: #03C75A;
            }

            /* Results styling */
            .results-container {
                margin-top: 2rem;
            }
            .result-item {
                margin-bottom: 1.5rem;
                padding: 1rem;
                border-radius: 12px;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
            }
            .result-item a {
                text-decoration: none;
                color: #1a0dab;
                font-size: 1.2rem;
                font-weight: 600;
            }
            .result-item a:hover {
                text-decoration: underline;
            }
            .result-item p {
                color: #4d5156;
                font-size: 0.95rem;
            }
            .result-item .url {
                color: #006621;
                font-size: 0.9rem;
            }
            
            /* Image grid */
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 1rem;
            }
            .image-item {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                cursor: pointer;
            }
            .image-item:hover {
                transform: scale(1.03);
            }
            .image-item img {
                width: 100%;
                height: 150px;
                object-fit: cover;
            }
            .image-item .caption {
                padding: 0.5rem;
                font-size: 0.8rem;
                text-align: center;
                background: white;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            /* Video grid */
            .video-item {
                border-radius: 12px;
                overflow: hidden;
                background: #fff;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            .video-item a {
                text-decoration: none;
            }
            .video-item img {
                width: 100%;
                height: auto;
                display: block;
            }
            .video-info {
                padding: 0.8rem;
            }
            .video-title {
                font-weight: 600;
                color: #212529;
                font-size: 1rem;
                margin-bottom: 0.3rem;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .video-source {
                font-size: 0.85rem;
                color: #03C75A;
            }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def _render_web_results(results: List[Dict[str, Any]]):
        """Renders web search results in a list."""
        if not results:
            st.info("웹 검색 결과가 없습니다.")
            return
        
        for item in results:
            st.markdown(f"""
            <div class="result-item">
                <a href="{item['url']}" target="_blank">{item['title']}</a>
                <p class="url">{item['url']}</p>
                <p>{item.get('snippet', '내용 요약 없음')}</p>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def _render_image_results(results: List[Dict[str, Any]]):
        """Renders image search results in a grid."""
        if not results:
            st.info("이미지 검색 결과가 없습니다.")
            return

        cols = st.columns(4)
        for i, item in enumerate(results):
            with cols[i % 4]:
                st.markdown(f"""
                <a href="{item['url']}" target="_blank">
                    <div class="image-item">
                        <img src="{item['imageUrl']}" alt="{item['title']}">
                        <div class="caption">{item['title']}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

    @staticmethod
    def _render_video_results(results: List[Dict[str, Any]]):
        """Renders video search results in a grid."""
        if not results:
            st.info("동영상 검색 결과가 없습니다.")
            return

        cols = st.columns(3)
        for i, item in enumerate(results):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="video-item">
                    <a href="{item['url']}" target="_blank">
                        <img src="{item['thumbnailUrl']}" alt="{item['title']}">
                        <div class="video-info">
                            <div class="video-title">{item['title']}</div>
                            <div class="video-source">{item['source']} | {item['duration']}</div>
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def render_main_ui():
        """Renders the entire Naver-style search UI."""
        EnhancedSearchUI._render_styles()

        if 'search_type' not in st.session_state:
            st.session_state.search_type = 'web'
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ''

        st.markdown('<div class="search-container">', unsafe_allow_html=True)

        # --- Search Bar ---
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            query = st.text_area(
                "Search",
                placeholder="검색어를 입력하세요",
                label_visibility="collapsed",
                key="search_input"
            )
        with col2:
            search_clicked = st.button("🔍")

        if search_clicked:
            st.session_state.search_query = query
        
        # --- Search Type Buttons ---
        search_types = {"web": "🌐 통합검색", "images": "🖼️ 이미지", "videos": "🎬 동영상"}
        
        cols = st.columns(len(search_types))
        for i, (key, value) in enumerate(search_types.items()):
            with cols[i]:
                is_active = st.session_state.search_type == key
                if st.button(value, use_container_width=True, type="secondary"):
                    st.session_state.search_type = key
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Search Execution and Results ---
        if st.session_state.search_query:
            st.markdown('<div class="results-container">', unsafe_allow_html=True)
            search_type = st.session_state.search_type
            query = st.session_state.search_query
            
            st.markdown(f"### '{query}'에 대한 {search_types[search_type]} 결과")

            with st.spinner(f"{search_types[search_type]} 검색 중..."):
                try:
                    if search_type == 'web':
                        results = search_web(query)
                        EnhancedSearchUI._render_web_results(results)
                    elif search_type == 'images':
                        results = search_images(query)
                        EnhancedSearchUI._render_image_results(results)
                    elif search_type == 'videos':
                        results = search_videos(query)
                        EnhancedSearchUI._render_video_results(results)
                except Exception as e:
                    st.error(f"검색 중 오류가 발생했습니다: {e}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# Example of how to use it in the main app.py
# from components.enhanced_search_ui import EnhancedSearchUI
#
# st.title("외부 데이터 검색")
# EnhancedSearchUI.render_main_ui()
