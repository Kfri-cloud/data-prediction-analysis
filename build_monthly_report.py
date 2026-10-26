from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def section():
    r=json.loads((ROOT/'results/monthly_results.json').read_text());rows=''
    for month,a in r['months'].items():
        change=-a['index_improvement_pct'];status='진행 중 · 1개 대기' if not a['calendar_month_complete'] else '집계 완료'
        rows+=f'<tr><td>{month}</td><td>{a["n"]}</td><td>{a["mae_pp"]["D1"]:.4f}</td><td>{a["mae_pp"]["DM"]:.4f}</td><td>{change:+.2f}%</td><td>{a["last_target_end"]}</td><td>{status}</td></tr>'
    return f'''<section id="monthly"><h2>월별 비교: 2025년 10월~2026년 10월</h2>
<div class="notice"><strong>13개월, 결과가 확인된 22회 예측을 월별로 비교했다.</strong><br>전체 기간에서 네 지수 추가 모델의 평균 오차는 환율 기준선보다 4.67% 컸다. 월마다 1~2회뿐이므로 특정 달의 개선·악화를 안정적인 성능으로 해석하지 않는다.</div>
<p><strong>이 표는 기존 12개 환율 관측치 예측을 ‘예측 시작 월’로 묶은 것이다.</strong> 예측 기간 자체를 한 달로 바꿔 다음 달 평균을 예측한 실험은 아니다. 목표 종료가 다음 달인 경우도 원래 예측을 시작한 달에 포함했다. 표의 오차는 월간 시장 수익률도 아니다.</p>
<div class="table"><table><tr><th>예측 시작 월</th><th>평가 횟수</th><th>환율 기준선 MAE</th><th>네 지수 추가 MAE</th><th>오차 증감</th><th>마지막 목표 종료일</th><th>상태</th></tr>{rows}</table></div>
<p class="meta">MAE 단위는 변화율의 퍼센트포인트(pp). 오차 증감이 음수이면 지수 추가가 개선, 양수이면 악화다. 기준 오차가 작고 표본이 적으면 상대 증감률이 매우 커질 수 있어 MAE와 횟수를 함께 봐야 한다.</p>
<h3>2026년 10월은 아직 끝나지 않았다</h3>
<p>2026년 10월에는 10월 4일 시작·10월 19일 목표 종료인 1개 구간만 평가했다. 10월 20일 시작 구간은 저장된 자료로 목표가 완성되지 않아 대기로 표시했다. 남은 10월과 이후 결과를 추정값으로 채우지 않았다. 이 페이지는 자동 갱신되는 실시간 서비스가 아니다.</p>
<p>자료 기준 UTC: <code>{r['snapshot_asof_utc']}</code>. 기존 지수·환율 스냅샷을 재사용했으며 원자료의 최초 공개시각과 수정 이력은 여전히 미확인이다.</p>
<h3>이전 결과와의 연결</h3>
<p>모델·특징·학습 규칙은 10개년 실험과 동일하다. 저장된 기존 예측 21개를 다시 계산해 모두 일치하는지 확인했다. 이전 연도 합계에서 2026년을 침범한다는 이유로 제외했던 2025년 12월 19일 시작 구간 1개를 이번에는 포함했다. 이 구간의 목표는 2026년 1월 7일에 끝난다. 해당 복원은 월별 집계 범위를 맞춘 것이며 모델을 결과에 맞춰 조정한 것이 아니다.</p>
<p>전체 22회에서 변화 없음 기준선 MAE는 1.1573pp, 환율 기준선은 1.1493pp, 지수 추가 모델은 1.2030pp다. 지수 추가는 13개월 중 5개월에서 오차를 줄였지만, 이 비율을 미래 성공확률로 해석하지 않는다. 같은 데이터의 재집계이며 새로운 독립 검증이 아니다.</p>
<p>이번 월별 표는 숫자·지수 비교다. 해당 기간 전체를 덮는 뉴스 원문·공개시각 자료가 없어 뉴스 효과 또는 투자자별 수급 효과를 검증한 표로 볼 수 없다. 월별 표본이 적어 월별 유의성 검사나 성공확률은 제시하지 않는다.</p>
<p><a href="monthly_protocol.json">월별 집계 기준</a> · <a href="results/monthly_results.json">월별 전체 결과</a> · <a href="results/monthly_predictions.csv">22개 개별 예측</a> · <a href="decade_report.html">10개년 원래 실험</a></p></section>'''

def main():
    style='body{font:16px/1.8 system-ui,sans-serif;background:#f4f7fb;color:#172b45;margin:auto;max-width:1180px;padding:30px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap}.notice{padding:20px;background:#fff4d6;border-left:5px solid #b7791f}.meta{color:#61718a}.table{overflow:auto}a{color:#1d54b9}'
    (ROOT/'monthly_report.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>데이터예측분석 | 13개월 비교</title><style>'+style+'</style><body>'+section()+'</body></html>',encoding='utf8')
if __name__=='__main__':main()
