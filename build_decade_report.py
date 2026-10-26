from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
def section():
    r=json.loads((ROOT/'results/decade_results.json').read_text());rows=''
    for year,a in r['by_year'].items():
        rows+=f'<tr><td>{year}{" (별도 최신 구간)" if year=="2026" else ""}</td><td>{a["n"]}</td><td>{a["mae_pp"]["D1"]:.4f}</td><td>{a["mae_pp"]["DM"]:.4f}</td><td>{-a["index_improvement_pct"]:+.2f}%</td></tr>'
    period=''
    for key,label in [('ten_year','2016~2025 전체'),('2016_2020','2016~2020'),('2021_2025','2021~2025')]:
        a=r[key];period+=f'<tr><td>{label}</td><td>{a["n"]}</td><td>{-a["index_improvement_pct"]:+.2f}%</td></tr>'
    return f'''<section id="decade"><h2>완결된 10개년 비교: 2016~2025</h2>
<div class="notice"><strong>216회 예측에서 네 지수 추가 시 평균 오차가 2.71% 증가했다.</strong><br>2021~2025년 부분 구간은 0.43% 감소했으나, 확실한 개선 근거는 부족하다. 이 결과는 숫자·지수 비교이며 10년 전체 뉴스 효과 검증은 미실행이다.</div>
<p>2011년부터 원·달러와 S&P 500·나스닥 100·코스피·코스닥 자료를 확보했다. 2011년은 특징 준비, 2012~2015년은 초기 학습에 활용하고 2016~2025년을 평가했다. 2026년의 결과가 확인된 17개 구간은 별도로 표시한다.</p>
<div class="table"><table><tr><th>기간</th><th>예측 횟수</th><th>네 지수 추가의 오차 증감</th></tr>{period}</table></div>
<p class="meta">음수이면 오차 감소, 양수이면 증가. 2021년 구분은 사용자가 지정한 분석 경계이며 AI의 출범 또는 인과효과를 검증한 경계가 아니다.</p>
<div class="table"><table><tr><th>연도</th><th>횟수</th><th>환율 기준선 MAE</th><th>지수 추가 MAE</th><th>오차 증감</th></tr>{rows}</table></div>
<p>MAE 단위는 변화율의 퍼센트포인트(pp)다. 10년 전체에서 변화 없음 기준선은 0.9824pp, 환율 과거·달력 기준선은 0.9761pp, 네 지수 추가 모델은 1.0026pp였다. 전체 차이(환율 기준선−지수 추가)의 설명용 95% 시간 블록 부트스트랩 구간은 −0.08625~+0.02306pp로 0을 포함한다. 2021~2025년의 구간도 −0.03751~+0.05634pp로 0을 포함한다. 여러 연도와 모델을 탐색했으므로 일부 연도의 좋은 결과를 확증으로 선택하지 않는다.</p>
<h3>앞선 실험과 달라진 점</h3>
<p>이전 TimesX 실험은 뉴스와 다른 환율 지표가 갖춰진 47개 시점이었다. 이번에는 Yahoo의 일간 USD/KRW 자료로 별도 216개 평가 시점을 만들었고, 기준 모델은 환율 자체의 1·5·20관측치 수익률·변동성·월 주기로 구성했다. 지수 모델은 네 지수의 같은 수익률·변동성 16개 특징을 추가했다. 출처·평가 날짜·기준 입력이 달라 이전 실험과 점수를 직접 비교할 수 없다.</p>
<p>12개 환율 관측치마다 예측하고, 다음 12개 일간 값의 평균을 마지막 사용 가능한 과거 환율과 비교했다. 예측 목표 구간은 서로 겹치지 않는다. 예측시각은 한국시간 00:00으로 가정하고 입력 봉은 타임스탬프 이후 48시간이 지난 것만 사용했다. 학습 정답도 마지막 목표 봉 이후 48시간이 지나야 사용했다. 같은 릿지 회귀·동일한 학습 구간·학습 전용 표준화를 적용했다.</p>
<p>10년 평가의 첫 예측일은 2016-01-05, 마지막 목표 종료일은 2025-12-18이다. 2025-12-19 시작 구간은 목표가 2026년으로 넘어가므로 사전 규칙에 따라 10년 합계에서 제외했다. 데이터 부족이나 오래된 입력으로 제외된 구간은 0개였다. 입력 타임스탬프의 최소 간격은 48.5시간이었다. 48시간 규칙은 실제 역사적 공개시각 또는 수정 이력이 확인됐다는 뜻이 아니다.</p>
<h3>뉴스 검증은 어디까지 되었나</h3>
<p>현재 확보한 사건 자료는 2023년부터다. 2016~2022년을 빈 뉴스로 채우거나 현재 AI가 과거 뉴스를 만들어내게 하지 않았다. 따라서 ‘숫자 / 숫자+지수 / 숫자+뉴스 / 숫자+지수+뉴스’의 10년 전체 비교는 아직 완료하지 않았다. <a href="market_report.html">기존 47회 네 비교군 실험</a>은 별도 기록으로 보존했다.</p>
<p>이 결과만으로 AI 보급 이후 예측이 쉬워졌다거나 뉴스가 무의미하다고 결론 내릴 수 없다. 10년 뉴스 효과를 검증하려면 해당 기간 원문·발표시각·수정 이력을 확보해야 한다. 투자자별 순매수와 현재 환율 예측도 이번 실험에 포함하지 않았다.</p>
<p>출처: <a href="https://finance.yahoo.com/quote/KRW%3DX/history/">Yahoo USD/KRW</a> 및 <a href="results/decade_sources.json">네 지수 다운로드 출처·시각</a>. 원본 공급자 스냅샷은 로컬 보존하며 재배포하지 않는다.</p>
<p><a href="decade_protocol.json">고정 실험 설계</a> · <a href="results/decade_results.json">전체 지표</a> · <a href="results/decade_predictions.csv">시점별 예측</a> · <a href="results/decade_lock.json">고정 해시</a></p></section>'''
def main():
    style='body{font:16px/1.8 system-ui,sans-serif;background:#f4f7fb;color:#172b45;margin:auto;max-width:1080px;padding:30px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left}.notice{padding:20px;background:#fff4d6;border-left:5px solid #b7791f}.meta{color:#61718a}.table{overflow:auto}a{color:#1d54b9}'
    (ROOT/'decade_report.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>데이터예측분석 | 10개년 비교</title><style>'+style+'</style><body>'+section()+'</body></html>',encoding='utf8')
if __name__=='__main__':main()
