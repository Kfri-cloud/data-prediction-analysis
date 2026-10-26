from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parent
def main():
    data=json.loads((ROOT/'results/indicator_results.json').read_text(encoding='utf8'))['results']
    sources={s['id']:s for s in json.loads((ROOT/'results/indicator_sources.json').read_text(encoding='utf8'))}
    rows=[];details=[]
    for r in data:
        s=r['summary'];m=s['mae_pp'];lo,hi=s['descriptive_interval_pp']
        yr=' / '.join(f'{y}: {v["improvement_pct"]:+.2f}% (n={v["n"]})' for y,v in r['years'].items())
        rows.append(f'<tr><th>{r["name"]}</th><td>{r["samples"]} / {s["n"]}</td><td>{m["B0"]:.3f}</td><td>{m["B1"]:.3f}</td><td>{m["M"]:.3f}</td><td>{m["Sdir"]:.3f}</td><td>{m["Cavg"]:.3f}</td><td>{s["improvement_pct"]:+.2f}%</td><td>[{lo:+.3f}, {hi:+.3f}]</td><td>{s["direction_hits"]}/{s["n"]}</td></tr>')
        p=r['latest_replay']
        details.append(f'<article><h2>{r["name"]} — 탐색 결과, 실전 타당성 미입증</h2><p>평가 기간 {r["first"]}~{r["last"]}. 연도별 B1 대비 오차 감소율: {yr}.</p><p>50:50은 지수 모델 M보다 {s["versus_M_pct"]:+.2f}%, 뉴스 모델 Sdir보다 {s["versus_Sdir_pct"]:+.2f}% 오차 감소. 음수는 악화입니다. 숫자 선별 기준: {"통과" if r["numerical_screen_pass"] else "미통과"}. 이 기준은 타당성 승인이나 확률이 아닙니다.</p><p>마지막 과거 재현 ({p["date"]}~{p["target_end"]}): M {p["M"]:+.3f}% × 0.5 + Sdir {p["Sdir"]:+.3f}% × 0.5 = <b>{p["Cavg"]:+.3f}%</b>. 실제 변화 {p["actual"]:+.3f}%. 현재 예측이 아닙니다.</p><a href="{html.escape(sources[r["id"]]["url"])}">고정 원자료</a></article>')
    improved=sum(r['summary']['improvement_pct']>0 for r in data)
    body=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>자료가 풍부한 지표 10선 — 50:50 검증</title>
<style>body{{font:16px/1.75 system-ui;background:#f5f7fb;color:#16263c;max-width:1450px;margin:auto;padding:28px}}h1{{font-size:34px}}article,.note{{background:white;border:1px solid #d8e2ee;padding:22px;margin:20px 0;border-radius:12px}}table{{border-collapse:collapse;background:white;width:100%;font-size:14px}}th,td{{padding:11px;border-bottom:1px solid #dce3eb;text-align:right}}th:first-child{{text-align:left}}.scroll{{overflow:auto}}a{{color:#155ab6}}</style><body>
<h1>사회문제에서 상품가격 지표 10개로 확장</h1>
<p>뉴스 요약·가격 이력·관련 수치가 함께 있는 TimesX 상품 자료를 사용했습니다. 국제 상품가격 벤치마크이며 한국 소매가격이나 국내 물가 예측은 아닙니다. 기존 사회문제 보고서는 별도로 보존합니다.</p>
<div class="note"><b>50:50 실제 계산 완료: 10개. B1보다 평균 오차 감소: {improved}개. 실전 타당성 입증: 0개.</b><p>뉴스 공개시각·원문 스냅샷·과거 자료 버전이 검증되지 않아 미래 정보 혼입을 배제할 수 없습니다. 개선율을 성공 확률로 읽으면 안 됩니다.</p></div>
<h2>무엇을 예측했나</h2><p>직전 가격 대비 다음 12개 관측치 평균의 변화율(%). 각 상품을 별도로 학습했습니다. B0=변화 없음, B1=가격 이력·동종 상품 수치, M=B1+S&amp;P 500·나스닥 100·KOSPI·KOSDAQ, Sdir=B1+뉴스 키워드·방향. <b>Cavg=0.5×M+0.5×Sdir</b>. 예측값의 비중이며 뉴스 정보가 정확히 50%라는 뜻은 아닙니다.</p>
<p>2024년부터 2026년 3월까지 가능한 시점에, 결과가 이미 확정된 과거 표본 16개 이상으로만 학습합니다. 지수에는 48시간 지연 규칙을 적용했습니다. 기존 환율 실험의 사전·모델·가중치를 바꾸지 않고 전이했습니다. 원자재 특화 뉴스 추출 정확도는 미측정이며, 관련 상품 요약 통계의 시각도 미검증입니다.</p>
<h2>오차와 타당성 근거</h2><p>MAE 단위는 변화율의 퍼센트포인트(pp). 개선율은 B1 대비 오차 감소율로 양수가 좋습니다. 구간은 B1 오차−50:50 오차의 기술적 블록 부트스트랩 95% 구간이며 0을 포함하면 개선 방향이 불확실합니다. 10개 동시 비교의 다중검정 보정은 하지 않았으므로 확증 검정이 아닙니다. 방향 적중은 확률 보정 결과가 아닙니다.</p>
<div class="scroll"><table><thead><tr><th>지표</th><th>전체/평가 표본</th><th>B0 MAE</th><th>B1 MAE</th><th>M MAE</th><th>Sdir MAE</th><th>50:50 MAE</th><th>개선율</th><th>차이 95% 구간(pp)</th><th>방향 적중</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>숫자 선별 조건은 전체 오차 5% 이상 감소, 차이 구간 하한 양수, 2024·2025년 각각 개선입니다. 이를 모두 충족해도 실제 공개시각과 새로운 미래 기간 검증이 추가로 필요합니다. 지표 선택은 자료 결합 가능성에 따른 것이며, 전 세계 자료량을 조사해 정한 순위는 아닙니다.</p>
{''.join(details)}<p><a href="results/indicator_predictions.csv">모든 시점의 예측 CSV</a> · <a href="results/indicator_results.json">계산 결과 JSON</a> · <a href="indicator_protocol.json">고정 실험 설계</a> · <a href="social_report.html">이전 사회문제 결과</a></p></body></html>'''
    (ROOT/'indicator_report.html').write_text(body,encoding='utf8')
if __name__=='__main__':main()
