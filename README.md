# 데이터예측분석

뉴스·사건 정보를 추가하면 수치 예측이 개선되는지 검증하는 연구 기록입니다.

**[배포된 보고서 보기](https://kfri-cloud.github.io/data-prediction-analysis/)**

## 현재 결과

[사회문제 10선](https://kfri-cloud.github.io/data-prediction-analysis/social_report.html)은 [한국](https://kfri-cloud.github.io/data-prediction-analysis/social_korea_report.html)과 [미국](https://kfri-cloud.github.io/data-prediction-analysis/social_usa_report.html)을 별도로 분석했습니다. **최종 50:50 방법은 두 지역 모두 미실행**입니다. 뉴스·공개시각·관련 지표가 부족합니다. 숫자 기준선은 한국 6개, 미국 7개 실행했고, 2025년까지 자료가 있는 각 3개에만 2026년 조건부 숫자 외삽을 제시했습니다. 최종방법의 예측으로 해석하면 안 됩니다.


[후보 조합 보고서](https://kfri-cloud.github.io/data-prediction-analysis/combination_report.html): 같은 47개 시점에서 키워드·방향 모델과 네 지수 모델의 고정 50:50 평균이 숫자 기준선보다 MAE 2.94% 감소했습니다. 2025년에는 악화했고 구간 추정도 0을 포함하므로 검증 완료가 아닙니다. 과거 결과로 고른 조합의 추가 탐색이며 다음 독립 검증의 후보입니다.


[2025-10~2026-10 월별 비교](https://kfri-cloud.github.io/data-prediction-analysis/monthly_report.html): 기존 12관측치 예측을 시작 월별로 묶은 13개월·22회 집계입니다. 전체 오차는 지수 추가 시 4.67% 증가했습니다. 달마다 1~2회뿐이며 2026년 10월은 진행 중입니다. 한 달 예측으로 학습 목표를 바꾼 모델이나 뉴스 효과 검증이 아닙니다.


[10개년 보고서](https://kfri-cloud.github.io/data-prediction-analysis/decade_report.html): 2016~2025년 216회 예측에서 지수 추가 시 오차 2.71% 증가. 2021~2025년만 보면 0.43% 감소하나 확실한 개선은 미확인. 이 확장은 숫자·지수 비교이며 10년 전체 뉴스 실험은 자료 부족으로 미실행입니다. 기존 TimesX와 출처·목표 시점·기준 입력이 다릅니다.


TimesX 원·달러 환율의 47개 시점 탐색 실험에서 기존 단어 해시 모델의 평균 절대오차는 기본 모델보다 **5.07% 증가**했습니다. 후속 키워드 8개 주제 모델은 **0.32% 증가**하여 해시 방식보다는 나았지만 숫자 기준선을 개선하지 못했습니다. 전체 맥락 언어모델은 시험하지 않았습니다. 키워드 비교는 이미 본 데이터를 다시 쓴 추가 탐색이며 새 보류 구간이 아닙니다.

[키워드 비교 보고서](https://kfri-cloud.github.io/data-prediction-analysis/keyword_report.html)

후속 사건 특징 실험에서는 방향만 추가한 모델의 전체 오차가 숫자 기준선보다 **0.53% 감소**했으나 2025년에는 악화됐습니다. 방향·주체·예상 차이를 모두 추가하면 **3.34% 증가**했습니다. 키워드 대비 주비교도 실패했습니다. 반복 탐색이며 정식 검증 통과가 아닙니다.

[방향·주체·예상 차이 보고서](https://kfri-cloud.github.io/data-prediction-analysis/event_report.html)

네 지수(S&P 500·나스닥 100·코스피·코스닥) 추가 시 전체 MAE는 **0.29% 감소**, 그 지수 모델에 뉴스까지 추가하면 **1.51% 증가**했습니다. 2025년에는 지수 추가도 악화돼 반복 개선은 미확인입니다. 현재 지수 스냅샷도 제공하지만 실시간 환율 예측이나 투자자별 수급 분석은 아닙니다.

[네 지수와 뉴스 비교](https://kfri-cloud.github.io/data-prediction-analysis/market_report.html)

기사별 공개시각·원문 스냅샷과 수치 최초 발표 버전을 검증하지 못했습니다. 따라서 **정식 타당성은 미입증**이며, 서울 소상공인 매출·폐업 예측을 검증한 결과가 아닙니다. 실시간 예측 서비스나 3D 경고 기능도 아직 없습니다.

## 구성

- `docs/`: GitHub Pages에 배포하는 보고서와 실험 결과
- `results/`: 기간별 지표, 시점별 예측, 입력·코드 해시
- `pilot_protocol.json`: 결과 확인 전에 고정한 탐색 실험 설계
- `protocol.json`: 원래 목표인 서울 매출 검증 설계
- `run_pilot.py`: 시간순 학습과 비교군 실험
- `PILOT_README.md`: 재현 방법과 데이터 한계

## 재현

Python 환경에서 아래 명령을 사용합니다. 원본 연구 데이터는 이 저장소에 재배포하지 않습니다. 다운로드된 자료의 이용조건은 각 원출처를 따릅니다.

```sh
python -m pip install -r requirements.txt
python fetch_sources.py
python fetch_pilot_source.py
python -m unittest -v test_audit.py test_pilot.py test_keywords.py test_events.py test_market.py test_decade.py test_combinations.py test_social.py
python run_pilot.py
python run_keywords.py
python run_events.py
python build_pilot_report.py
python build_keyword_report.py
python build_event_report.py
python build_report.py
```

고정 입력·코드 해시가 달라지면 실험 재실행을 거절합니다. 공개 보고서는 `docs/`의 검토된 정적 산출물이며 분석 스크립트 실행만으로 자동 배포되지는 않습니다. 최초 배포의 17개 테스트는 구현 검증이고 예측 타당성 승인이 아닙니다.

## 원출처

- [TimesX 공식 프로젝트](https://haoxin1998.github.io/TimesX-project/)
- [TimesX 고정 버전](https://github.com/haoxin1998/TimesX-project/tree/26bc70cfa669407c71ae1ad6ce2194be9cfe9a0b)
- [Time-MMD 공식 저장소](https://github.com/AdityaLab/Time-MMD)
- [서울 추정매출 자료](https://data.seoul.go.kr/dataList/OA-22176/S/1/datasetView.do?tab=A)

10개년 실험은 `python fetch_decade.py`, `python run_decade.py`, `python build_decade_report.py` 순서입니다. 원본 응답이 바뀌면 고정 해시 검사를 통과하지 못하므로 기존 실험을 덮어쓰지 마세요.

월별 집계는 `python run_monthly.py`, `python build_monthly_report.py`로 재현합니다. 원래 고정된 10개년 입력 스냅샷이 필요합니다.

후보 조합은 `python run_combinations.py`, `python build_combination_report.py`로 재현합니다. 기존 사건·지수 실험의 고정 스냅샷이 필요합니다.

사회문제는 `python fetch_social.py`, `python run_social.py`, `python build_social_report.py` 순서입니다. 국가별로 별도 학습하며 원자료 버전이 바뀌면 고정 해시 확인으로 실행을 중단합니다.

논문 본문과 원본 데이터 파일은 포함하지 않았습니다. 출처별 이용조건은 원문에서 확인해야 합니다.

지수 실험은 별도 `python fetch_market.py`, `python run_market.py`, `python build_market_report.py`를 사용합니다. 공급자 응답이 나중에 달라지면 고정 해시가 일치하지 않아 실행을 거절합니다. 원본 시세 스냅샷은 로컬에만 보존했으므로 새 다운로드로 동일 결과가 재현된다고 보장하지 않습니다. 고정 실험을 재튜닝하거나 해시 검사를 우회해서는 안 됩니다.

## 상품 지표 10개로 확장

[50:50 비교 보고서](https://kfri-cloud.github.io/data-prediction-analysis/indicator_report.html): 10개 상품을 별도 학습했습니다. 석탄과 대두만 B1 대비 평균 오차가 줄었고 실전 타당성은 모두 미입증입니다. `python fetch_indicators.py`, `python run_indicators.py`, `python build_indicator_report.py`로 실행합니다. 기존 지수 원본 스냅샷과 고정 의존 코드가 필요하며, 뉴스 공개시각은 검증되지 않았습니다.

[내부 가중치 후 50:50](https://kfri-cloud.github.io/data-prediction-analysis/weighted_report.html): 나스닥 및 결과형 뉴스 비중을 과거 OOF 오차로 선택하는 추가 탐색. `python run_weighted.py`, `python build_weighted_report.py`. 최초 공개시각과 새 미래 기간의 검증은 미완료입니다.

[5개 분야 × 3개 대표 지표](https://kfri-cloud.github.io/data-prediction-analysis/diverse_report.html): 에너지·농산물 가격과 기술·여가/여행·소비 검색 관심도를 따로 평가했습니다. 심리 표현 우선 가중치는 균등 우선도보다 개선되지 않았습니다. 주간 검색의 비중복 평가 표본은 각 4회뿐이며 인과/실전 검증이 아닙니다. `python fetch_diverse.py`, `python run_diverse.py`, `python build_diverse_report.py`. 원자료와 기존 지수 스냅샷이 필요합니다.

[유사 사례 예측](https://kfri-cloud.github.io/data-prediction-analysis/analogue_report.html): 결과를 가린 과거 조건 거리로 최대 5개 사례를 고르고 단순 기준의 오차 중앙값을 보정합니다. 시간순 학습·사례 기간 중복 배제, 15개 지표 383회 탐색이며 실전 검증은 아닙니다. `python run_analogue.py`, `python build_analogue_report.py`.

[사회문제 방법별 비교](https://kfri-cloud.github.io/data-prediction-analysis/social_transfer_report.html): 국가별로 현재 값 유지·추세·회귀·유사 사례를 재검증합니다. 과거 예측 오차로 시점마다 방법을 선택하며, 한국 6개·미국 7개 실행 및 각 3개 조건부 2026년 연간 추정을 제공합니다. 실제 공개일·수정 이력 미검증이며 뉴스 50:50은 미실행입니다. `python run_social_transfer.py`, `python build_social_transfer_report.py`.
