from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parent
def main():
    data=json.loads((ROOT/'results/diverse_results.json').read_text(encoding='utf8'))['results'];sources={r['id']:r for r in json.loads((ROOT/'results/diverse_sources.json').read_text(encoding='utf8'))}
    sections=[]
    for field in dict.fromkeys(r['field'] for r in data):
        table=[];details=[]
        for r in [x for x in data if x['field']==field]:
            s=r['summary'];m=s['mae'];lo,hi=s['interval'];p=r['latest'];n=r['nonoverlap'];kind='가격' if r['kind']=='price' else '검색 관심도'
            table.append(f'<tr><th>{r["name"]} {kind}</th><td>{s["n"]}/{n["n"]}</td><td>{m["Naive"]:.3f}</td><td>{m["B1"]:.3f}</td><td>{m["Equal"]:.3f}</td><td>{m["Psyche"]:.3f}</td><td>{s["improvement"]["Equal"]:+.2f}%</td><td>{s["improvement"]["B1"]:+.2f}%</td><td>[{lo:+.3f},{hi:+.3f}]</td></tr>')
            years=' / '.join(f'{y}: {v["improvement"]["Equal"]:+.2f}%' for y,v in r['years'].items())
            c=r['category_counts'];total=sum(c.values());coverage=100*(total-c['unknown'])/max(total,1)
            details.append(f'<details><summary>{r["name"]}: 예측값·분류·검증 한계</summary><p>전체 뉴스 결합 표본 {r["samples"]}개, 평가 {r["first"]}~{r["last"]}. 단위: {r["unit"]}. 비중복 {n["n"]}회만 남겼을 때 균등 대비 감소율 {n["improvement"]["Equal"]:+.2f}%. 연도별 감소율: {years}.</p><p>심리 후보 {c["psyche"]}, 결과 후보 {c["outcome"]}, 예상 차이 후보 {c["surprise"]}, 미분류 {c["unknown"]} 문장. 규칙이 분류한 비율 {coverage:.1f}%는 추출 정확도가 아닙니다. 수동 정확도·인과 영향은 미측정입니다.</p><p>MAE: 기존 구조 50:50 {m["Original50"]:.3f}, 결과 우선 반대군 {m["Reverse"]:.3f}, 지수만 변경 {m["IndexOnly"]:.3f}, 뉴스만 변경 {m["NewsOnly"]:.3f}. 이번 수치 특징·확장 사전이 달라 이전 상품 보고서와 같은 실험으로 간주하면 안 됩니다.</p><p>마지막 과거 예측 {p["date"]}~{p["target_end"]}: 지수 {p["index_prediction"]:+.3f} × 0.5 + 뉴스 {p["news_prediction"]:+.3f} × 0.5 = <b>{p["Psyche"]:+.3f} {r["unit"]}</b>, 실제 {p["actual"]:+.3f}. 뉴스 내부 비중: 심리 {p["psyche_weight"]:.1%}, 결과 {p["outcome_weight"]:.1%}, 예상 차이 {p["surprise_weight"]:.1%}, 미분류 {p["unknown_weight"]:.1%}. 해당 시점 가중치 학습용 과거 예측 {p["weight_validation_n"]}회.</p><a href="{html.escape(sources[r["id"]]["url"])}">고정 원자료</a></details>')
        sections.append(f'<section><h2>{field} — 대표 3개</h2><div class="scroll"><table><tr><th>목표</th><th>평가/비중복</th><th>단순 기준</th><th>B1</th><th>균등 우선도</th><th>심리 우선</th><th>균등 대비 감소</th><th>B1 대비 감소</th><th>차이 95% 구간</th></tr>{"".join(table)}</table></div>{"".join(details)}</section>')
    total=sum(r['summary']['n'] for r in data);better=sum(r['summary']['improvement']['Equal']>0 for r in data)
    body=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>5개 분야 × 3개 지표 — 뉴스 가중치 검증</title><style>body{{font:16px/1.8 system-ui;max-width:1450px;margin:auto;padding:28px;background:#f5f7fb;color:#16263c}}section,.note{{background:white;padding:22px;border:1px solid #d8e1ed;border-radius:12px;margin:20px 0}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{text-align:right;padding:10px;border-bottom:1px solid #ddd}}.scroll{{overflow:auto}}details{{margin:12px 0;padding:12px;background:#f4f7fa}}a{{color:#155bb5}}</style><body><nav><a href="index.html">전체 기록</a> · <a href="weighted_report.html">이전 가중치 실험</a></nav><h1>분야별로 성격이 다른 대표 지표 3개씩</h1>
<p>에너지·농산물·기술·여가/여행·소비에서 총 15개. 구조적 차이로 선정했으며 실제로 반대로 움직이는 조합이라는 뜻은 아닙니다. 뉴스 후 기대·불안이 생겼는지에 대한 인과 검증 대신, 해당 표현을 포함한 뉴스에 더 높은 비중을 주는 가설을 시험했습니다.</p>
<div class="note"><b>{total}회 과거 예측. 균등 우선도보다 평균 오차 감소 {better}/15개. 실전 타당성 입증 0개.</b><p>뉴스가 붙은 가격 표본은 수십 개, 주간 검색 표본은 각 29개뿐입니다. 분야는 넓혔지만 뉴스 결합 자료가 충분히 풍부하다고 판정한 것은 아닙니다. 기사 원문·공개시각·과거 버전이 없고 반복 탐색이므로 확증 결과가 아닙니다.</p></div>
<h2>서로 다른 목표를 구분</h2><p>가격 6개는 직전 값 대비 다음 12개 일별 관측치 평균 변화율(%), 검색 9개는 다음 12주 평균−직전 검색지수(점)를 예측합니다. 검색 관심도는 실제 매출·관광객·기술 보급량이 아닙니다. 지역도 확인되지 않아 한국 수요로 해석할 수 없습니다. 서로 다른 단위의 MAE를 합산하거나 분야 순위로 비교하지 않습니다.</p>
<p>검색지수는 Google Trends 정규화 자료이며 2025-07-06 이후는 겹치는 기간으로 보정한 확장 자료입니다. 100을 넘을 수 있고 최초 공개 버전이 아닙니다. 검색 예측 구간이 서로 겹치므로 비중복 표본 결과도 제공합니다. <a href="https://github.com/haoxin1998/TimesX-project/blob/26bc70cfa669407c71ae1ad6ce2194be9cfe9a0b/Datasets/SearchTrend/readme.md">원자료 척도 설명</a></p>
<h2>가중치와 공정한 비교</h2><p>각 뉴스 유형별로 같은 숫자 기반 모델에 해당 문장의 특징을 더한 모델을 학습했습니다. 기사 문장을 심리 표현·결과 발표·예상과 실제 차이·미분류로 나누고, 심리/예상 차이에 우선도 2 또는 3, 결과/미분류에 1을 줍니다. 각 유형의 문장 수는 10개까지 제한한 뒤 제곱근을 취해 우선도를 곱하고 정규화합니다. 따라서 뉴스 내용에 따라 내부 비중이 달라집니다. 없는 유형은 비중 0이고 모두 없으면 숫자 모델로 돌아갑니다.</p>
<p>우선도 2·3의 선택과 나스닥/다른 지수 비중은 해당 시점 이전에 결과가 끝난 과거 예측만 사용합니다. 과거 예측도 그 이전 자료로 학습합니다. 최종은 지수 50%+뉴스 50%. 주비교는 같은 지수·뉴스 모델에서 우선도를 모두 1로 둔 대조군이며, 결과 뉴스에 높은 우선도를 주는 반대군도 비교합니다. 신규·중복 정보 여부나 실제 시장 예상치는 직접 확인하지 못했습니다.</p>
<p>표의 수치는 MAE, 감소율 양수는 개선입니다. 단순 기준은 가격의 변화 없음, 검색의 전년 같은 12주 평균입니다. 95% 구간은 균등 모델 오차−심리 우선 모델 오차의 기술적 블록 부트스트랩 구간이며 0을 포함하면 개선 방향이 불확실합니다. 다중 비교 보정은 없으며, 특히 적은 주간 표본에서는 구간도 불안정합니다.</p>
{''.join(sections)}<p><b>현재 예측 미발행:</b> 마지막 예측 예시는 2026년 10월 현재의 미래 예측이 아닌 과거 재현입니다. 최신 가격·검색·공개시각이 확인된 뉴스가 필요합니다.</p><p><a href="results/diverse_predictions.csv">시점별 예측·가중치 CSV</a> · <a href="results/diverse_results.json">결과 JSON</a> · <a href="results/diverse_classification.csv">문장 분류 해시 감사표</a> · <a href="diverse_protocol.json">고정 설계</a></p></body></html>'''
    (ROOT/'diverse_report.html').write_text(body,encoding='utf8')
if __name__=='__main__':main()
