from pathlib import Path
import json,csv,html
from build_evidence_summary import LABEL
ROOT=Path(__file__).resolve().parent
MLABEL={'Last':'현재 값 유지','Seasonal':'전년 같은 달','Drift':'12개월 평균 변화','Ridge':'숫자 회귀','Analog':'유사 사례 5개','Selected':'이전 24회 성적으로 방법 선택'}
def main():
    old=json.loads((ROOT/'results/evidence_summary.json').read_text(encoding='utf8'))
    monthly=json.loads((ROOT/'results/monthly_domains_results.json').read_text(encoding='utf8'))['results']
    # Assert the earlier model comparisons really share the same targets.
    diverse={(r['indicator'],r['date']):r for r in csv.DictReader((ROOT/'results/diverse_predictions.csv').read_text().splitlines())}
    analog={(r['indicator'],r['date']):r for r in csv.DictReader((ROOT/'results/analogue_predictions.csv').read_text().splitlines())}
    assert diverse.keys()==analog.keys()
    for key in diverse:
        for metric in ['actual','Naive','B1']:assert abs(float(diverse[key][metric])-float(analog[key][metric]))<1e-9
    entries=[]
    for r in old['all']:
        cs=r['candidates']
        if not cs:entries.append(dict(name=r['name'],category='자료 부족',method='미실행',reason=r['status'],source='social_report.html'));continue
        best=min(cs,key=lambda x:x['mae']);passed=[x for x in cs if x['passes']]
        if passed:
            best=min(passed,key=lambda x:x['mae']);category='근거 강화 후보';reason='기존 사후 선별 기준 통과. 독립 미래 검증 아님'
        elif best['improvement_pct']>=10:
            category='추가 검증';reason='개선폭은 있으나 표본 또는 기술적 구간 기준 미충족'
        else:
            category='단순 기준 유지';reason='추가 방법이 더 나쁘거나 개선이 작음. 단순 기준이 항상 최선이라는 증명은 아님'
        method=LABEL[best['model']] if category!='단순 기준 유지' else ('전년 같은 기간' if '검색' in r['name'] else '현재 값 유지')
        entries.append(dict(name=r['name'],category=category,method=method,reason=reason,source=r['source'],best_posthoc=LABEL[best['model']],improvement_pct=best['improvement_pct'],n=best['n'],nonoverlap_n=best['nonoverlap_n']))
    for r in monthly:
        s=r['summary'];category='근거 강화 후보' if r['screen_pass'] else '추가 검증' if s['improvement']['Last']>0 and s['intervals']['Last'][0]>0 else '단순 기준 유지'
        entries.append(dict(name='미국 월별 '+r['name'],category=category,method='이전 24회 성적으로 방법 선택' if category!='단순 기준 유지' else '현재 값 유지',reason='새 월별 기준 통과' if r['screen_pass'] else '기준 전체 미충족; 양의 구간이어도 10% 미달이면 보류' if category=='추가 검증' else '주모델이 현재 값 유지보다 악화',source='field_guide.html',improvement_pct=s['improvement']['Last'],n=s['n'],nonoverlap_n=s['n'],best_posthoc=MLABEL[r['best_posthoc']]))
    counts={c:sum(r['category']==c for r in entries) for c in ['근거 강화 후보','추가 검증','단순 기준 유지','자료 부족']}
    result=dict(status='EXPLORATORY_CLASSIFICATION_NOT_PRODUCTION_APPROVAL',counts=counts,entries=entries,monthly=monthly,alignment_audit='383 targets and baseline predictions matched exactly')
    (ROOT/'results/field_guide.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    tables=[];md=['# 분야별 예측 기준 검증 기록','', '2026-10-26. 한국 중심의 기존 결과와 미국 추가 월별 결과를 분리했습니다. 모든 분류는 실전 인증이 아닌 추가 검증 우선순위입니다.','']
    for category in counts:
        rows=[];md+=['## '+category,'','| 분야·대상 | 다음 검증/유지 방식 | 감소율 | 평가/비중복 수 | 근거 |','|---|---|---:|---:|---|']
        for r in [x for x in entries if x['category']==category]:
            gain=f'{r["improvement_pct"]:+.2f}%' if 'improvement_pct' in r else '—';n=f'{r["n"]}/{r["nonoverlap_n"]}' if 'n' in r else '—'
            rows.append(f'<tr><th><a href="{r["source"]}">{r["name"]}</a></th><td>{r["method"]}</td><td>{gain}</td><td>{n}</td><td>{r["reason"]}</td></tr>')
            md.append(f'| {r["name"]} | {r["method"]} | {gain} | {n} | {r["reason"]} |')
        tables.append(f'<section><h2>{category} · {counts[category]}개</h2><div class="scroll"><table><tr><th>분야·대상</th><th>다음 검증/유지 방식</th><th>후보 감소율</th><th>평가/비중복 수</th><th>판단 근거</th></tr>{"".join(rows)}</table></div></section>')
    monthly_rows=[];detail=[]
    for r in monthly:
        s=r['summary'];m=s['mae'];lo,hi=s['intervals']['Last'];halves=r['halves'];selection=' · '.join(f'{MLABEL[k]} {v}회' for k,v in s['selection_counts'].items())
        monthly_rows.append(f'<tr><th>{r["name"]}</th><td>{s["n"]}</td><td>{m["Last"]:.3f}</td><td>{m["Seasonal"]:.3f}</td><td>{m["Selected"]:.3f}</td><td>{s["improvement"]["Last"]:+.2f}%</td><td>{halves["2016-2020"]["improvement"]["Last"]:+.2f}%</td><td>{halves["2021-2025"]["improvement"]["Last"]:+.2f}%</td><td>[{lo:+.3f},{hi:+.3f}]</td></tr>')
        best=r['best_posthoc'];detail.append(f'<details><summary>{r["name"]} — 기준과 데이터 확인</summary><p>단위 {r["unit"]}. {selection}. 사후 최소 MAE 후보는 {MLABEL[best]} ({m[best]:.3f})이며 주평가는 미리 고정한 시점별 선택 모델입니다. 결과를 본 뒤 최저 모델로 주평가를 교체하지 않았습니다.</p><p>누락 관측월: {", ".join(r["missing_months"]) or "없음"}. 제외된 예측 대상월: {", ".join(r["excluded_target_months"]) or "없음"}.</p><a href="{r["source"]}">FRED 지표 정의·공식 원출처</a></details>')
    body=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>분야별 예측 기준 검증 지도</title><style>body{{font:16px/1.8 system-ui;max-width:1500px;margin:auto;padding:28px;background:#f5f7fb;color:#17283d}}section,.note{{background:white;padding:22px;border:1px solid #d7e0eb;border-radius:12px;margin:20px 0}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}.scroll{{overflow:auto}}details{{padding:12px;background:#f4f7fa;margin:12px 0}}a{{color:#155bb5}}</style><body><nav><a href="index.html">전체 기록</a> · <a href="evidence_summary.html">기존 3개 선별 기록</a></nav><h1>분야를 넓히고 기준을 다시 검증했습니다</h1><div class="note"><b>기존 35개 국가·지표 조합 + 미국 월별 5개 = 40개 판단 기록</b><p>근거 강화 후보 {counts['근거 강화 후보']}개 · 추가 검증 {counts['추가 검증']}개 · 단순 기준 유지 {counts['단순 기준 유지']}개 · 자료 부족 {counts['자료 부족']}개. 이는 서로 독립된 40개 분야가 아니며 국가별 같은 지표도 포함합니다.</p></div>
<p>자료가 적은 검색 지표에서 과거 최저 오차를 고르는 것만으로 채택하지 않았습니다. 새로 고용·실업·소비·생산·주택공급 월별 자료를 수집해 597회 예측을 추가했습니다. 한국 자료와 미국 월별 결과를 혼합 학습하지 않았습니다.</p>
<h2>분류 기준과 읽는 법</h2><p>기존 결과는 10% 개선·비중복 평가 8회·기술적 구간 하한 양수라는 사후 선별을 유지합니다. 새 월별 실험은 결과 실행 전에 현재 값 유지와 전년 같은 달보다 각각 10% 이상 개선, 두 구간 하한 양수, 앞·뒤 5년 모두 개선, 24회 이상 평가를 정했습니다. 표의 기존 감소율은 여러 후보 중 사후 최저 MAE, 새 월별 감소율은 이전 자료만으로 방법을 고르는 고정 주모델의 결과입니다. 둘의 근거 수준은 동일하지 않습니다.</p><p>‘단순 기준 유지’의 작은 양수는 최선 후보의 이득이 작아 우선 유지한다는 뜻이며, 단순 모델이 수학적으로 최적이라는 뜻은 아닙니다. ‘비중복’은 예측 대상 기간이 겹치지 않는다는 뜻이지 통계적 독립을 보장하지 않습니다. 성능 순위를 정하기 위해 서로 다른 단위의 MAE를 합산하지 않습니다.</p>
{''.join(tables)}<section id="monthly"><h2>새 월별 5개 지표 — 2016~2025년, 다음 한 달 예측</h2><p>2000~2025년 자료, 학습 최소 60개 완료 월. 현재 값·전년 같은 달·12개월 평균 변화·숫자 회귀·유사 사례 5개 중 이전 최대 24개 예측의 MAE로 다음 방법을 고릅니다. 예측 당시 관측월까지의 값만 계산에 사용했지만, 원자료는 현재 수정 버전입니다. 실제 최초 발표일·발표 지연을 재현한 결과는 아닙니다.</p><p>모두 계절조정된 지표이므로 전년 같은 달은 계절성이 남아 있다는 가정이 아닌 추가 비교군입니다. 특히 큰 전년 대비 개선만으로 통과시키지 않고 현재 값 유지도 이겨야 합니다. 주택착공은 연율로 표시된 월별 값으로 실제 해당 월 착공 건수와 다릅니다. 소매판매는 명목 금액이며 실질 소비량이 아닙니다.</p><div class="scroll"><table><tr><th>지표</th><th>평가 수</th><th>현재 유지 MAE</th><th>전년 동월 MAE</th><th>선택 모델 MAE</th><th>유지 대비 감소</th><th>2016~20 감소</th><th>2021~25 감소</th><th>차이 95% 구간</th></tr>{''.join(monthly_rows)}</table></div>{''.join(detail)}<p>실업률의 2025-10 결측으로 최초 실행이 중단됐습니다. 원본 코드·해시를 남기고 v2에서 결측이 필요한 구간을 제외했습니다. 모델·가중치·판정 기준은 바꾸지 않았습니다. 관측치 보간은 하지 않았습니다.</p></section>
<p>모든 구간은 기술적 블록 부트스트랩이며 다중 비교를 보정하지 않았습니다. 기존 결과는 반복 탐색, 신규 월별 자료도 과거 수정 이력이 미검증인 탐색입니다. 인과 관계나 한국 지역별 적용 가능성, 실시간 서비스 정확도를 입증한 것은 아닙니다. 이번 작업에서 새 미래 시점 예측은 발행하지 않았습니다.</p><p><a href="field_guide.md">분류표 Markdown</a> · <a href="results/field_guide.json">전체 근거 JSON</a> · <a href="results/monthly_domains_predictions.csv">597회 월별 예측</a> · <a href="monthly_domains_protocol.json">월별 고정 설계</a></p></body></html>'''
    (ROOT/'field_guide.html').write_text(body,encoding='utf8');(ROOT/'field_guide.md').write_text('\n'.join(md),encoding='utf8')
    print(json.dumps(counts,ensure_ascii=True))
if __name__=='__main__':main()

