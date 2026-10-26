# 데이터예측분석

뉴스·사건 정보를 추가하면 수치 예측이 개선되는지 검증하는 연구 기록입니다.

**[배포된 보고서 보기](https://kfri-cloud.github.io/data-prediction-analysis/)**

## 현재 결과

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
python -m unittest -v test_audit.py test_pilot.py test_keywords.py test_events.py test_market.py
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

논문 본문과 원본 데이터 파일은 포함하지 않았습니다. 출처별 이용조건은 원문에서 확인해야 합니다.

지수 실험은 별도 `python fetch_market.py`, `python run_market.py`, `python build_market_report.py`를 사용합니다. 공급자 응답이 나중에 달라지면 고정 해시가 일치하지 않아 실행을 거절합니다. 원본 시세 스냅샷은 로컬에만 보존했으므로 새 다운로드로 동일 결과가 재현된다고 보장하지 않습니다. 고정 실험을 재튜닝하거나 해시 검사를 우회해서는 안 됩니다.
