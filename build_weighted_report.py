from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
def main():
    data=json.loads((ROOT/'results/weighted_results.json').read_text(encoding='utf8'))['results'];rows=[];details=[]
    for r in data:
        s=r['summary'];m=s['mae'];w=r['mean_weights'];lo,hi=s['delta_interval'];last=r['latest']
        rows.append(f'<tr><th>{r["name"]}</th><td>{s["n"]}</td><td>{w["nasdaq"]:.0%}</td><td>{w["outcome"]:.0%}</td><td>{m["Cavg"]:.3f}</td><td>{m["Weighted"]:.3f}</td><td>{s["improvement_old_pct"]:+.2f}%</td><td>{s["improvement_B1_pct"]:+.2f}%</td><td>[{lo:+.3f}, {hi:+.3f}]</td></tr>')
        years=' / '.join(f'{y}: {v["improvement_old_pct"]:+.2f}%' for y,v in r['years'].items())
        details.append(f'<article><h2>{r["name"]}</h2><p>기존 조합 대비 연도별 오차 감소율: {years}. 결과형 후보 {r["outcome_clauses"]}/{r["total_clauses"]}개 문장.</p><p>MAE 비교: 숫자 B1 {m["B1"]:.3f}, 기존 50:50 {m["Cavg"]:.3f}, 지수 쪽만 변경 {m["IndexOnly"]:.3f}, 뉴스 쪽만 변경 {m["NewsOnly"]:.3f}, 양쪽 변경 {m["Weighted"]:.3f}, 비중 제한 없는 비교군 {m["Unconstrained"]:.3f} pp.</p><p>비중 제한 없는 비교군 평균: 나스닥 {w["nasdaq_free"]:.1%}, 결과형 뉴스 {w["outcome_free"]:.1%}. 집중 비중이 높게 나온 것만으로 중요성이 입증되지는 않습니다. 집중 모델에는 최소 50% 제약이 있습니다.</p><p>마지막 과거 재현 {last["date"]}: 나스닥 {last["nasdaq"]:.0%}, 다른 지수 {1-last["nasdaq"]:.0%}; 결과형 뉴스 {last["outcome"]:.0%}, 나머지 뉴스 {1-last["outcome"]:.0%}. 지수 예측 {last["Windex"]:+.3f}% × 0.5 + 뉴스 예측 {last["Wnews"]:+.3f}% × 0.5 = {last["Weighted"]:+.3f}%. 실제 {last["actual"]:+.3f}%. 가중치 선택에 사용한 과거 예측 {last["weight_validation_n"]}회.</p></article>')
    body='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>내부 가중치 후 50:50 실험</title><style>body{font:16px/1.8 system-ui;max-width:1400px;margin:auto;padding:28px;background:#f4f7fb;color:#16263c}article,.note{padding:20px;background:white;border:1px solid #d7e0ec;margin:18px 0;border-radius:12px}table{border-collapse:collapse;background:white;width:100%}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:right}.scroll{overflow:auto}a{color:#175bb8}</style><body><h1>내부 가중치를 정한 뒤 50:50으로 결합</h1>
<p>금·은을 포함한 기존 상품 10개에 동일한 절차를 적용했습니다. 나스닥에 집중하는 지수 측 예측과 실제 발표·발생 결과 표현에 집중하는 뉴스 측 예측을 만든 뒤, 최종 비중은 50:50으로 유지했습니다. 금·은은 예측 대상이며 추가 입력으로 넣은 것은 아닙니다. 나스닥은 직접적인 대중심리 지수가 아닙니다.</p>
<div class="note"><b>과거 학습 구간에서만 가중치 선택. 실전 타당성은 미입증.</b><p>과거 결과를 본 뒤 설계한 추가 탐색입니다. 최초 공개시각이 없는 뉴스 요약을 사용하므로 미래 정보 혼입을 배제하지 못합니다. 가중치는 인과적 영향력이나 성공 확률이 아닙니다.</p></div>
<h2>계산 방법</h2><p>지수 쪽 = a×(B1+나스닥 모델) + (1−a)×(B1+S&amp;P 500·KOSPI·KOSDAQ 모델). 뉴스 쪽 = b×(B1+결과형 뉴스 모델) + (1−b)×(B1+나머지 뉴스 모델). 최종 = 지수 쪽×0.5 + 뉴스 쪽×0.5.</p>
<p>a와 b는 50%, 75%, 100% 중 각각 선택했습니다. 예측 시점보다 먼저 결과가 확정된 과거 예측 8회 이상에서 MAE가 가장 작은 비중을 고릅니다. 과거 예측도 해당 시점 이전 자료로만 학습합니다. 부족하면 50%로 시작합니다. 비교군은 0%, 25%도 허용합니다. 각 예측 시점마다 다시 선택하며 상품별로 별도 학습합니다.</p>
<p>결과형 문장은 reported·released·approved·rose·fell 같은 표현을 포함하고 예상·부정 표현을 제외한 규칙 기반 후보입니다. 사람의 사실 검증을 거치지 않았고 혼합 문장 누락도 가능합니다. 나머지 문장이 모두 심리 뉴스인 것은 아닙니다. 기존 숫자 기준선과 뉴스 사전은 유지했습니다.</p>
<h2>473회 비교 결과</h2><p>가중치는 평가 시점별 평균입니다. MAE 단위는 변화율의 pp, 감소율은 양수가 개선입니다. 구간은 기존 조합 오차−새 조합 오차의 기술적 블록 부트스트랩 95% 구간입니다. 다중 비교 보정이 없으므로 구간이 양수여도 확증 결과가 아닙니다.</p>
<div class="scroll"><table><tr><th>대상</th><th>평가 수</th><th>나스닥 평균 비중</th><th>결과 뉴스 평균 비중</th><th>기존 MAE</th><th>새 MAE</th><th>기존 대비 감소</th><th>B1 대비 감소</th><th>차이 구간(pp)</th></tr>'''+''.join(rows)+'''</table></div>'''+''.join(details)+'''<p><a href="results/weighted_predictions.csv">모든 예측·가중치 CSV</a> · <a href="results/weighted_results.json">결과 JSON</a> · <a href="weighted_protocol.json">실험 설계</a> · <a href="indicator_report.html">기존 50:50 실험</a></p></body></html>'''
    (ROOT/'weighted_report.html').write_text(body,encoding='utf8')
if __name__=='__main__':main()
