from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def section():
    r=json.loads((ROOT/'results/market_results.json').read_text());a=r['all']
    labels={'B1':'기존 숫자','M':'숫자 + 네 지수','K1':'숫자 + 뉴스 키워드','MK':'숫자 + 네 지수 + 뉴스 키워드'}
    rows=''.join(f'<tr><td>{label}</td><td>{a["mae_pp"][k]:.4f}</td><td>{a["direction_accuracy"][k]*100:.1f}%</td></tr>' for k,label in labels.items())
    blocks=''
    for b,label in [('development','2024'),('confirmation','2025'),('latest_holdout','2026년 1~3월')]:
        x=r['blocks'][b];blocks+=f'<tr><td>{label}</td><td>{x["n"]}</td><td>{-x["index_improvement_pct"]:+.2f}%</td><td>{-x["news_given_indices_improvement_pct"]:+.2f}%</td></tr>'
    names={'sp500':'S&P 500','nasdaq100':'나스닥 100','kospi':'코스피','kosdaq':'코스닥'}
    current=''
    for x in r['current_snapshot']:
        feat=x['lagged_returns_1_5_20_and_volatility_pct']
        values=''.join(f'<td>{v:+.2f}%</td>' for v in feat[:3]) if feat else '<td colspan="3">오래된 자료·사용 불가</td>'
        current+=f'<tr><td>{names[x["index"]]}</td><td>{x["latest_observed_timestamp_utc"][:10]}</td><td>{(x["eligible_latest_timestamp_utc"] or "미확인")[:10]}</td>{values}</tr>'
    return f'''<section id="market"><h2>네 주가지수와 뉴스 결합 비교</h2>
<div class="notice"><strong>네 지수 추가 시 전체 오차는 0.29% 감소했으나 기간별로 일관되지 않았다.</strong><br>지수 모델에 뉴스를 추가하면 오차가 1.51% 증가했다. 이번 설정에서는 시장 지표를 알고도 뉴스가 더 도움이 된다는 근거를 얻지 못했다.</div>
<p>S&P 500·나스닥 100·코스피·코스닥의 1·5·20거래 관측치 수익률과 20개 일간 수익률의 표준편차를 추가했다. 뉴스는 기존 8개 주제 키워드와 사건 건수로 고정했다. 원·달러의 다음 12영업일 평균 변화율을 예측하며 네 지수 자체의 수익률 예측을 평가한 것은 아니다.</p>
<div class="table"><table><tr><th>모델</th><th>MAE (pp)</th><th>방향 적중률</th></tr>{rows}</table></div>
<p class="meta">같은 47개 시점·동일한 학습 구간·고정 회귀 설정으로 비교했다. MAE는 작을수록 좋다. 주비교는 ‘지수 추가 모델’ 대 ‘지수+뉴스 모델’이다. 방향 적중률은 보조 지표다.</p>
<div class="table"><table><tr><th>기간</th><th>시점 수</th><th>지수 추가의 오차 변화<br>기존 숫자 대비</th><th>뉴스 추가의 오차 변화<br>지수 모델 대비</th></tr>{blocks}</table></div>
<p>뉴스의 추가 효과에 대한 MAE 차이(지수−지수+뉴스)는 −0.01197pp, 설명용 95% 시간 블록 부트스트랩 구간은 −0.05451~+0.03747pp로 0을 포함한다. 지수 추가 자체의 구간도 −0.13703~+0.10926pp로 0을 포함한다. 2026년은 4개뿐이다. 같은 자료에서 여러 방법을 탐색했으므로 확증 통계로 해석하지 않는다.</p>
<h3>예측 시간과 시장 시간의 정렬</h3>
<p>Yahoo Finance 일간 자료를 내려받아 지수별 <strong>4개씩, 합계 16개 특징</strong>을 만들었다. 예측 날짜의 한국시간 00:00을 보수적인 기준으로 가정하고, 일간 봉 타임스탬프로부터 48시간이 지난 값만 사용했다. 264개 지수-예측시점 연결의 최소 간격은 48.5시간이었다. 미래 값 채우기는 하지 않았고, 21개 관측치 미만이거나 최신 봉이 14일보다 오래되면 실행을 중단하도록 했다.</p>
<p>이 48시간은 실제 공개시각을 확인했다는 뜻이 아니다. 일간 봉 타임스탬프는 종가 발표시각과 다를 수 있다. 여유를 둔 사용 규칙 때문에 당시 이용 가능했던 최신 정보 일부를 놓칠 수도 있다. 원자료의 수치 수정 이력과 기존 환율·뉴스 입력의 당시 공개 가능성도 여전히 미확인이다.</p>
<h3>현재 자료 스냅샷</h3>
<p>수집·점검 기준 UTC: <code>{r['current_snapshot_asof_utc']}</code>. 아래 값은 자동 갱신되지 않는 저장 당시 자료다. 마지막 열 세 개는 48시간 규칙으로 사용 가능한 종가까지의 수익률이며 최신 수집일의 실시간 수익률이 아니다.</p>
<div class="table"><table><tr><th>지수</th><th>최신 수집 봉 날짜</th><th>48시간 규칙 사용 봉 날짜</th><th>1관측치 수익률</th><th>5관측치 수익률</th><th>20관측치 수익률</th></tr>{current}</table></div>
<p>현재 환율·뉴스 입력까지 동일 시각으로 맞추지 않았으므로 현재 환율 예측은 발행하지 않았다. 과거 실험의 평가 결과와 현재 자료의 수집 상태는 별개다.</p>
<h3>대중·큰손 가설에 관하여</h3>
<p>네 지수는 시장 반응을 나타내는 입력 후보이지만, 그 움직임만으로 개인·기관·외국인 중 누가 움직였는지 판별할 수는 없다. 투자자별 순매수는 별도 자료가 필요하다. <a href="https://data.krx.co.kr/">KRX 공식 데이터 서비스</a>에 투자자별 거래실적 항목이 있는 것은 확인했지만 이번 실험에는 해당 시계열을 확보·검증해 넣지 않았다. 지수 거래량이나 투자자별 수급을 사용한 결과로 해석하면 안 된다.</p>
<p>뉴스 추가 이득이 없다는 결과만으로 ‘뉴스가 이미 가격에 완전히 반영됐다’고 입증할 수도 없다. 작은 표본, 뉴스 표현 방식, 시간 정렬, 모델 능력의 영향도 있을 수 있다. 이번 비교 역시 새로운 미사용 평가 기간이 없는 탐색 실험이다.</p>
<p>출처: <a href="https://finance.yahoo.com/quote/%5EGSPC/history/">S&P 500</a> · <a href="https://finance.yahoo.com/quote/%5ENDX/history/">나스닥 100</a> · <a href="https://finance.yahoo.com/quote/%5EKS11/history/">코스피</a> · <a href="https://finance.yahoo.com/quote/%5EKQ11/history/">코스닥</a>. 원본 시세 JSON은 재배포하지 않고 로컬에 보존했다. 공급자 응답은 나중에 바뀔 수 있어 재다운로드의 해시 일치는 보장되지 않는다.</p>
<p><a href="market_protocol.json">실험 설계</a> · <a href="results/market_results.json">전체 결과</a> · <a href="results/market_predictions.csv">시점별 예측</a> · <a href="results/market_alignment.csv">시간 연결 감사표</a> · <a href="results/market_sources.json">출처·수집시각</a> · <a href="results/market_lock.json">고정 해시</a></p></section>'''

def main():
    style='body{font:16px/1.8 system-ui,sans-serif;background:#f4f7fb;color:#172b45;margin:auto;max-width:1080px;padding:30px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left}.notice{padding:20px;background:#fff4d6;border-left:5px solid #b7791f}.meta{color:#61718a}.table{overflow:auto}a{color:#1d54b9}'
    (ROOT/'market_report.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>데이터예측분석 | 네 지수와 뉴스</title><style>'+style+'</style><body>'+section()+'</body></html>',encoding='utf8')

if __name__=='__main__':main()
