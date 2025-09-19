"""
ETL 파이프라인 - CSV 데이터를 MySQL로 적재
"""

import logging

import pandas as pd

from utils.database import DatabaseManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL 파이프라인 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        """
        ETL 파이프라인 초기화

        Args:
            db_manager: 데이터베이스 매니저 인스턴스
        """
        self.db_manager = db_manager

        # 업종 매핑 딕셔너리
        self.industry_mapping = {
            "음식점": "restaurant",
            "소매업": "retail",
            "서비스업": "service",
            "숙박업": "accommodation",
            "운수업": "transportation",
            "건설업": "construction",
            "제조업": "manufacturing",
            "기타": "others",
        }

        # 지역 매핑 딕셔너리 (예시)
        self.region_mapping = {
            "강남구": "Gangnam",
            "강동구": "Gangdong",
            "강북구": "Gangbuk",
            "강서구": "Gangseo",
            "관악구": "Gwanak",
            "광진구": "Gwangjin",
            "구로구": "Guro",
            "금천구": "Geumcheon",
            "노원구": "Nowon",
            "도봉구": "Dobong",
            "동대문구": "Dongdaemun",
            "동작구": "Dongjak",
            "마포구": "Mapo",
            "서대문구": "Seodaemun",
            "서초구": "Seocho",
            "성동구": "Seongdong",
            "성북구": "Seongbuk",
            "송파구": "Songpa",
            "양천구": "Yangcheon",
            "영등포구": "Yeongdeungpo",
            "용산구": "Yongsan",
            "은평구": "Eunpyeong",
            "종로구": "Jongno",
            "중구": "Jung",
            "중랑구": "Jungnang",
        }

    def load_csv_data(self, file_path: str) -> pd.DataFrame | None:
        """
        CSV 파일 로드

        Args:
            file_path: CSV 파일 경로

        Returns:
            로드된 DataFrame 또는 None
        """
        try:
            # 다양한 인코딩 시도
            encodings = ["utf-8", "cp949", "euc-kr", "utf-8-sig"]

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(
                        f"CSV 파일이 성공적으로 로드되었습니다: {file_path} (인코딩: {encoding})"
                    )
                    return df
                except UnicodeDecodeError:
                    continue

            logger.error(f"CSV 파일 로드 실패: {file_path}")
            return None

        except Exception as e:
            logger.error(f"CSV 파일 로드 중 오류 발생: {e}")
            return None

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 정제

        Args:
            df: 원본 DataFrame

        Returns:
            정제된 DataFrame
        """
        try:
            # 복사본 생성
            cleaned_df = df.copy()

            # 결측값 처리
            cleaned_df = cleaned_df.fillna(
                {"sales_amt": 0, "sales_cnt": 0, "visitors": 0}
            )

            # 숫자형 컬럼 변환
            numeric_columns = ["sales_amt", "sales_cnt", "visitors"]
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    # 문자열에서 숫자만 추출
                    cleaned_df[col] = (
                        cleaned_df[col]
                        .astype(str)
                        .str.replace(r"[^\d.-]", "", regex=True)
                    )
                    cleaned_df[col] = pd.to_numeric(
                        cleaned_df[col], errors="coerce"
                    ).fillna(0)

            # 날짜 컬럼 처리
            if "date" in cleaned_df.columns:
                cleaned_df["date"] = pd.to_datetime(cleaned_df["date"], errors="coerce")

            # 지역명 정제
            if "region" in cleaned_df.columns:
                cleaned_df["region"] = cleaned_df["region"].str.strip()
                cleaned_df["region"] = cleaned_df["region"].str.replace(
                    r"\s+", " ", regex=True
                )

            # 업종명 정제
            if "industry" in cleaned_df.columns:
                cleaned_df["industry"] = cleaned_df["industry"].str.strip()
                cleaned_df["industry"] = cleaned_df["industry"].str.replace(
                    r"\s+", " ", regex=True
                )

            # 이상치 제거 (매출이 음수인 경우)
            if "sales_amt" in cleaned_df.columns:
                cleaned_df = cleaned_df[cleaned_df["sales_amt"] >= 0]

            logger.info(f"데이터 정제 완료: {len(cleaned_df)} 행")
            return cleaned_df

        except Exception as e:
            logger.error(f"데이터 정제 중 오류 발생: {e}")
            return df

    def extract_regions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        지역 정보 추출 및 정규화

        Args:
            df: 원본 DataFrame

        Returns:
            지역 정보 DataFrame
        """
        try:
            if "region" not in df.columns:
                logger.warning("지역 컬럼이 없습니다.")
                return pd.DataFrame()

            # 고유 지역 추출
            unique_regions = df["region"].unique()
            regions_data = []

            for region in unique_regions:
                if pd.isna(region) or region == "":
                    continue

                # 구/동 분리 (예: "강남구 역삼동" -> "강남구", "역삼동")
                parts = str(region).split()
                if len(parts) >= 2:
                    gu = parts[0]
                    dong = " ".join(parts[1:])
                else:
                    gu = parts[0] if parts else region
                    dong = ""

                regions_data.append(
                    {
                        "name": region,
                        "gu": gu,
                        "dong": dong,
                        "adm_code": self._generate_adm_code(gu, dong),
                    }
                )

            regions_df = pd.DataFrame(regions_data)
            regions_df = regions_df.drop_duplicates(subset=["name"])

            logger.info(f"지역 정보 추출 완료: {len(regions_df)} 개 지역")
            return regions_df

        except Exception as e:
            logger.error(f"지역 정보 추출 중 오류 발생: {e}")
            return pd.DataFrame()

    def extract_industries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        업종 정보 추출 및 정규화

        Args:
            df: 원본 DataFrame

        Returns:
            업종 정보 DataFrame
        """
        try:
            if "industry" not in df.columns:
                logger.warning("업종 컬럼이 없습니다.")
                return pd.DataFrame()

            # 고유 업종 추출
            unique_industries = df["industry"].unique()
            industries_data = []

            for industry in unique_industries:
                if pd.isna(industry) or industry == "":
                    continue

                # 업종 카테고리 매핑
                category = self._map_industry_category(industry)

                industries_data.append(
                    {
                        "name": industry,
                        "nace_kor": self._generate_nace_code(industry),
                        "category": category,
                    }
                )

            industries_df = pd.DataFrame(industries_data)
            industries_df = industries_df.drop_duplicates(subset=["name"])

            logger.info(f"업종 정보 추출 완료: {len(industries_df)} 개 업종")
            return industries_df

        except Exception as e:
            logger.error(f"업종 정보 추출 중 오류 발생: {e}")
            return pd.DataFrame()

    def transform_sales_data(
        self, df: pd.DataFrame, regions_df: pd.DataFrame, industries_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        매출 데이터 변환 (ID 매핑)

        Args:
            df: 원본 매출 DataFrame
            regions_df: 지역 정보 DataFrame
            industries_df: 업종 정보 DataFrame

        Returns:
            변환된 매출 DataFrame
        """
        try:
            # 지역 ID 매핑
            region_mapping = dict(
                zip(regions_df["name"], regions_df["region_id"], strict=False)
            )
            df["region_id"] = df["region"].map(region_mapping)

            # 업종 ID 매핑
            industry_mapping = dict(
                zip(industries_df["name"], industries_df["industry_id"], strict=False)
            )
            df["industry_id"] = df["industry"].map(industry_mapping)

            # 필요한 컬럼만 선택
            sales_columns = [
                "region_id",
                "industry_id",
                "date",
                "sales_amt",
                "sales_cnt",
                "visitors",
            ]
            available_columns = [col for col in sales_columns if col in df.columns]

            sales_df = df[available_columns].copy()

            # 결측값 제거
            sales_df = sales_df.dropna(subset=["region_id", "industry_id"])

            logger.info(f"매출 데이터 변환 완료: {len(sales_df)} 행")
            return sales_df

        except Exception as e:
            logger.error(f"매출 데이터 변환 중 오류 발생: {e}")
            return pd.DataFrame()

    def load_to_database(
        self,
        regions_df: pd.DataFrame,
        industries_df: pd.DataFrame,
        sales_df: pd.DataFrame,
    ) -> bool:
        """
        데이터베이스에 데이터 로드

        Args:
            regions_df: 지역 데이터
            industries_df: 업종 데이터
            sales_df: 매출 데이터

        Returns:
            성공 여부
        """
        try:
            success = True

            # 지역 데이터 로드
            if not regions_df.empty:
                success &= self.db_manager.insert_dataframe(
                    regions_df, "regions", "replace"
                )

            # 업종 데이터 로드
            if not industries_df.empty:
                success &= self.db_manager.insert_dataframe(
                    industries_df, "industries", "replace"
                )

            # 매출 데이터 로드
            if not sales_df.empty:
                success &= self.db_manager.insert_dataframe(
                    sales_df, "sales_2024", "replace"
                )

            if success:
                logger.info("모든 데이터가 성공적으로 데이터베이스에 로드되었습니다.")
            else:
                logger.error("데이터 로드 중 일부 실패가 발생했습니다.")

            return success

        except Exception as e:
            logger.error(f"데이터베이스 로드 중 오류 발생: {e}")
            return False

    def run_etl_pipeline(self, csv_file_path: str) -> bool:
        """
        전체 ETL 파이프라인 실행

        Args:
            csv_file_path: CSV 파일 경로

        Returns:
            성공 여부
        """
        try:
            logger.info(f"ETL 파이프라인 시작: {csv_file_path}")

            # 1. CSV 데이터 로드
            df = self.load_csv_data(csv_file_path)
            if df is None:
                return False

            # 2. 데이터 정제
            cleaned_df = self.clean_data(df)

            # 3. 지역 정보 추출
            regions_df = self.extract_regions(cleaned_df)

            # 4. 업종 정보 추출
            industries_df = self.extract_industries(cleaned_df)

            # 5. 매출 데이터 변환
            sales_df = self.transform_sales_data(cleaned_df, regions_df, industries_df)

            # 6. 데이터베이스에 로드
            success = self.load_to_database(regions_df, industries_df, sales_df)

            if success:
                logger.info("ETL 파이프라인이 성공적으로 완료되었습니다.")
            else:
                logger.error("ETL 파이프라인 실행 중 오류가 발생했습니다.")

            return success

        except Exception as e:
            logger.error(f"ETL 파이프라인 실행 중 오류 발생: {e}")
            return False

    def _generate_adm_code(self, gu: str, dong: str) -> str:
        """행정구역 코드 생성"""
        # 실제로는 서울시 행정구역 코드를 사용해야 함
        gu_codes = {
            "강남구": "11680",
            "강동구": "11740",
            "강북구": "11305",
            "강서구": "11500",
            "관악구": "11620",
            "광진구": "11215",
            "구로구": "11530",
            "금천구": "11545",
            "노원구": "11350",
            "도봉구": "11320",
            "동대문구": "11230",
            "동작구": "11590",
            "마포구": "11440",
            "서대문구": "11410",
            "서초구": "11650",
            "성동구": "11200",
            "성북구": "11290",
            "송파구": "11710",
            "양천구": "11470",
            "영등포구": "11560",
            "용산구": "11170",
            "은평구": "11380",
            "종로구": "11110",
            "중구": "11140",
            "중랑구": "11260",
        }
        return gu_codes.get(gu, "00000")

    def _map_industry_category(self, industry: str) -> str:
        """업종 카테고리 매핑"""
        industry_lower = industry.lower()

        if any(
            keyword in industry_lower
            for keyword in ["음식", "식당", "카페", "레스토랑"]
        ):
            return "음식점"
        elif any(
            keyword in industry_lower for keyword in ["소매", "판매", "상점", "마트"]
        ):
            return "소매업"
        elif any(
            keyword in industry_lower for keyword in ["서비스", "미용", "세탁", "수리"]
        ):
            return "서비스업"
        elif any(keyword in industry_lower for keyword in ["숙박", "호텔", "펜션"]):
            return "숙박업"
        elif any(keyword in industry_lower for keyword in ["운수", "택시", "버스"]):
            return "운수업"
        else:
            return "기타"

    def _generate_nace_code(self, industry: str) -> str:
        """NACE 코드 생성 (예시)"""
        # 실제로는 한국표준산업분류를 사용해야 함
        industry_codes = {
            "음식점": "5610",
            "소매업": "4711",
            "서비스업": "9601",
            "숙박업": "5510",
            "운수업": "4921",
            "기타": "9999",
        }

        category = self._map_industry_category(industry)
        return industry_codes.get(category, "9999")
