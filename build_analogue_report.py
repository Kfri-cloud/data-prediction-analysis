from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
def main():
    data=json.loads((ROOT/'results/analogue_results.json').read_text(encoding='utf8'))['results'];sections=[]
    for field in dict.fromkeys(r['field'] for r in data):
        rows=[];details=[]
        for r in [x for x in data if x['field']==field]:
            s=r['summary'];m=s['mae'];lo,hi=s['interval'];p=r['latest'];unit='변화율 pp' if r['kind']=='price' else '검색지수 점'
            rows.append(f'<tr><th>{r["name"]}</th><td>{s["n"]}/{r["nonoverlap"]["n"]}</td><td>{m["Naive"]:.3f}</td><td>{m["History"]:.3f}</td><td>{m["Analog5"]:.3f}</td><td>{m["News5"]:.3f}</td><td>{s["improvement"]["Naive"]:+.2f}%</td><td>{s["improvement"]["History"]:+.2f}%</td><td>[{lo:+.3f},{hi:+.3f}]</td></tr>')
            cases=''.join(f'<tr><td>{n["neighbor_origin"]}~{n["neighbor_end"]}</td><td>{n["distance"]:.3f}</td><td>{n["actual"]:+.3f}</td><td>{n["naive"]:+.3f}</td><td>{n["residual"]:+.3f}</td></tr>' for n in r['latest_neighbors'])
            years=' / '.join(f'{y}: {v["improvement"]["Naive"]:+.2f}%' for y,v in r['years'].items())
            details.append(f'<details><summary>{r["name"]} — 실제로 선택한 유사 사례와 결과</summary><p>단위 {unit}. 연도별 단순 기준 대비 오차 감소율: {years}. 비중복 평가만 남긴 감소율 {r["nonoverlap"]["improvement"]["Naive"]:+.2f}%.</p><p>추가 비교 MAE: 숫자 회귀 B1 {m["B1"]:.3f}, 보정 없이 사례 결과 중앙값 {m["Raw5"]:.3f}, 사례 3개 보정 {m["Analog3"]:.3f}. 후보를 여러 개 본 뒤 가장 좋은 것만 확증 결과로 선택하면 안 됩니다.</p><p>마지막 과거 예측 {p["date"]}~{p["target_end"]}: 단순 예측 {p["Naive"]:+.3f}에 과거 사례 오차 중앙값을 더해 <b>{p["Analog5"]:+.3f}</b>, 실제 {p["actual"]:+.3f}. 사례 보정값의 25~75% 범위를 현재 단순 예측에 더하면 [{p["case_q25"]:+.3f}, {p["case_q75"]:+.3f}]. 이는 보정된 확률 구간이 아닙니다.</p><p>선택된 사례 보정값의 가장 많은 부호 비율 {p["residual_sign_agreement"]:.0%}. 성공 확률이 아니며 소수 표본의 기술 통계입니다. 거리는 작을수록 상대적으로 가까울 뿐, 충분히 비슷하다는 절대 기준은 검증하지 않았습니다.</p><div class="scroll"><table><tr><th>과거 사례 기간</th><th>거리</th><th>실제 변화</th><th>당시 단순 예측</th><th>보정값</th></tr>{cases}</table></div></details>')
        sections.append(f'<section><h2>{field}</h2><div class="scroll"><table><tr><th>대상</th><th>평가/비중복</th><th>단순 MAE</th><th>과거 전체 보정 MAE</th><th>유사 5개 MAE</th><th>뉴스 포함 유사 MAE</th><th>단순 대비 감소</th><th>전체 보정 대비 감소</th><th>단순 대비 차이 구간</th></tr>{"".join(rows)}</table></div>{"".join(details)}</section>')
    improved=sum(r['summary']['improvement']['Naive']>0 for r in data)
    body=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>비슷한 상황에서 비슷한 결과 — 유사 사례 검증</title><style>body{{font:16px/1.8 system-ui;max-width:1450px;margin:auto;padding:28px;background:#f5f7fb;color:#17283d}}section,.note{{background:white;padding:22px;margin:20px 0;border:1px solid #d7e0eb;border-radius:12px}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;text-align:right;border-bottom:1px solid #ddd}}.scroll{{overflow:auto}}details{{padding:14px;background:#f4f7fa;margin:12px 0}}a{{color:#1459b3}}</style><body><nav><a href="index.html">전체 기록</a> · <a href="diverse_report.html">이전 15개 지표</a></nav><h1>비슷한 상황이면 이후 결과도 비슷할까?</h1><div class="note"><b>15개 지표·383회 과거 예측. 단순 기준보다 평균 오차 감소 {improved}/15개. 실전 타당성 미입증.</b><p>결과를 보지 않고 과거 조건만으로 사례를 선택했습니다. 다만 이 실험 자체는 이미 여러 번 살펴본 데이터의 추가 탐색이며, 뉴스·요약 수치의 실제 공개시각은 미검증입니다.</p></div>
<h2>상황을 어떻게 비교했나</h2><p>같은 지표의 과거 중 결과 기간이 이미 끝난 사례만 후보로 삼았습니다. 가격/관심의 추세·변동성, 월의 계절성, 원자료의 관련 지표 요약, 48시간 지연한 네 주가지수를 네 묶음으로 나누고 각 묶음의 거리를 동일 비중으로 합쳤습니다. 표준화는 후보 과거 자료만 이용합니다. 예측 결과값은 거리와 사례 선택에 사용하지 않습니다. 뉴스 비교군만 키워드·방향 특징을 다섯 번째 묶음으로 추가합니다.</p>
<p>가까운 순서로 최대 5개를 선택하되 사례들의 결과 기간이 서로 겹치면 제외합니다. 3개 미만이면 단순 기준으로 돌아갑니다. 최근접 사례도 실제로 닮지 않았을 수 있습니다. 공급·재고·발표 전 예상치 등은 확보된 것이 아니므로 완전한 상황 일치를 검증한 실험은 아닙니다.</p>
<h2>단순 예측을 넘어서는지 검증</h2><p>가격은 현재 값 유지, 검색은 전년 같은 12주 평균이 단순 기준입니다. 주모델은 <b>현재 단순 예측 + 유사 사례들의 과거 예측 오차 중앙값</b>입니다. 과거 결과를 그대로 평균내는 대신 계절성 기준이 과거 비슷한 상황에서 얼마나 빗나갔는지 보정합니다. 유사도를 쓰지 않는 과거 전체 오차 중앙값도 비교해 사례 선택 자체의 가치를 확인합니다.</p>
<p>가격 목표는 다음 12개 일별 관측치 평균의 변화율, 검색 목표는 다음 12주 평균과 직전 검색지수의 차이입니다. 서로 다른 단위의 오차를 합산하지 않습니다. 검색은 매출·이용자 수가 아니며 지역 미확인·2025년 중반 이후 보정 확장 자료입니다. 주간 평가는 11회지만 겹치지 않는 기간은 각 4회뿐입니다.</p>
<p>표는 MAE입니다. 감소율 양수가 개선이며 95% 구간은 단순 오차−유사 사례 오차의 기술적 블록 부트스트랩 구간입니다. 다중 비교 보정과 독립 미래 검증이 없어 확증이나 성공 확률로 해석할 수 없습니다.</p>{''.join(sections)}
<p>각 펼침 항목의 사례는 마지막 과거 재현 기준입니다. 2026년 10월 현재의 미래 예측은 발행하지 않았습니다.</p><p><a href="results/analogue_predictions.csv">시점별 예측</a> · <a href="results/analogue_neighbors.csv">모든 선택 사례</a> · <a href="results/analogue_results.json">계산 결과</a> · <a href="analogue_protocol.json">고정 설계</a></p></body></html>'''
    (ROOT/'analogue_report.html').write_text(body,encoding='utf8')
if __name__=='__main__':main()
