from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
LABEL={'N0':'현재 값 유지','Trend':'최근 3년 평균 변화','N1':'숫자 회귀','Analog':'유사 사례 5개'}
def main():
    data=json.loads((ROOT/'results/social_transfer_results.json').read_text(encoding='utf8'))['results'];sections=[]
    for region,title in [('KOR','한국'),('USA','미국')]:
        rows=[];projections=[];details=[]
        for r in [x for x in data if x['region']==region]:
            if 'summary' not in r:
                reason='동질적 시계열 미확보' if r['status']=='NOT_EXECUTED_NO_HARMONIZED_SERIES' else f'평가 가능 {r["eligible_years"]}년: 최소 5년 미달'
                rows.append(f'<tr><th>{r["name"]}</th><td colspan="8">미실행 — {reason}</td></tr>');continue
            s=r['summary'];m=s['mae'];lo,hi=s['descriptive_interval'];best=min(m,key=m.get);bestlabel=LABEL.get(best,'과거 성적으로 선택')
            rows.append(f'<tr><th>{r["name"]}</th><td>{s["n"]}</td><td>{m["N0"]:.3f}</td><td>{m["Trend"]:.3f}</td><td>{m["N1"]:.3f}</td><td>{m["Analog"]:.3f}</td><td>{m["Selected"]:.3f}</td><td>{s["selected_improvement_pct"]:+.2f}%</td><td>[{lo:+.3f},{hi:+.3f}]</td></tr>')
            selection=' / '.join(f'{LABEL[k]} {v}회' for k,v in s['selection_counts'].items())
            details.append(f'<details><summary>{r["name"]} — 정의와 해석</summary><p>목표: {r["target"]}. 단위: {r["unit"]}. {r["issue"]}</p><p>원자료 {r["observations"]}개 연도, 최신 {r["latest_year"]}년 값 {r["latest_value"]:.3f}. 평가 {r["first_target"]}~{r["last_target"]}년. 시점별 선택: {selection}. 전체 평가를 사후에 본 최저 오차 방식은 {bestlabel}이며 미래 승자가 아닙니다.</p><a href="{r["source"]}">지표 원출처</a></details>')
            p=r['projection_2026']
            if p:
                projections.append(f'<tr><th>{r["name"]}</th><td>{r["latest_value"]:.3f}</td><td>{LABEL[p["chosen"]]}</td><td>{p["value"]:.3f}</td><td>{r["unit"]}</td><td>{p["selection_n"]}년</td></tr>')
        sections.append(f'<section><h2>{title}: 별도 학습·검증</h2><div class="scroll"><table><tr><th>문제</th><th>평가 연도 수</th><th>현재 유지</th><th>3년 변화</th><th>숫자 회귀</th><th>유사 사례</th><th>시점별 선택</th><th>유지 대비 감소</th><th>차이 95% 구간</th></tr>{"".join(rows)}</table></div><h3>2025년 값이 있는 항목의 2026년 조건부 연간 추정</h3><p>2025년까지의 수치만 주어졌다고 가정한 2026년 연간 값입니다. 현재인 2026년 10월의 최신 정보 기반 예측이나 2027년 전망이 아닙니다. 개선이 없었던 항목도 표에 남겼으며 실전 사용 승인을 뜻하지 않습니다.</p><div class="scroll"><table><tr><th>문제</th><th>2025 관측값</th><th>과거 성적으로 고른 방식</th><th>2026 조건부 추정</th><th>단위</th><th>선택 검증 자료</th></tr>{"".join(projections)}</table></div>{"".join(details)}</section>')
    body=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>사회문제 예측 — 문제별 방법 비교</title><style>body{{font:16px/1.8 system-ui;max-width:1450px;margin:auto;padding:28px;background:#f5f7fb;color:#17283d}}section,.note{{background:white;padding:22px;border:1px solid #d7e0eb;border-radius:12px;margin:20px 0}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:10px;text-align:right;border-bottom:1px solid #ddd}}.scroll{{overflow:auto}}details{{margin:12px 0;padding:12px;background:#f4f7fa}}a{{color:#155bb5}}</style><body><nav><a href="index.html">전체 기록</a> · <a href="social_report.html">이전 사회문제 실험</a> · <a href="analogue_report.html">유사 사례 검증</a></nav><h1>사회문제별로 어떤 예측 방식이 맞는가?</h1><div class="note"><b>한국 6개·미국 7개 실행. 2026년 조건부 연간 추정 각 3개. 실제 공개시점 기반 타당성은 미입증.</b><p>다른 분야의 승자를 사회문제에 그대로 적용하지 않고 후보 방법만 가져왔습니다. 매 예측 시점 이전 성적으로 방법을 선택하고 그 다음 연도의 실제 값과 비교했습니다. 뉴스·지수 50:50은 필요한 자료가 없어 미실행입니다.</p></div>
<h2>문제별 선택 규칙</h2><p>후보는 현재 값 유지, 최근 3년의 평균 연간 변화 연장, 기존 숫자 회귀, 유사 사례 5개입니다. 연간 자료라 월별 계절성을 시험할 수 없습니다. 국가는 섞지 않습니다. 유사 사례는 같은 지표의 수준·1년 변화·3년 변화가 가까운 과거 5개를 결과를 가리고 고른 뒤, 다음 해 변화 중앙값을 현재 값에 더합니다.</p>
<p>각 시점의 방법 선택에는 그 시점까지 결과가 끝난 최근 최대 8개 과거 예측만 사용합니다. 최소 5개가 없으면 현재 값 유지로 돌아갑니다. 과거 예측도 당시의 이전 자료만 학습했습니다. 모든 후보는 최소 10개 완료 학습 사례가 필요하고, 비교할 평가 연도가 5개 미만이면 미실행입니다. 물가 상승률은 음수를 허용하고 그 외는 비음수, 청년 비율은 최대 100%로 제한합니다.</p>
<h2>해석할 때 구분할 것</h2><p>수치는 MAE이며 낮을수록 좋습니다. 단위는 문제별로 달라 합산하거나 문제 간 성능 순위로 읽을 수 없습니다. 감소율은 현재 값 유지 대비이며 양수가 개선입니다. 95% 구간은 유지 오차−선택 모델 오차의 기술적 블록 부트스트랩 구간으로, 적은 표본·반복 탐색·다중 비교 미보정을 고려해야 합니다.</p>
<p>World Bank 현재 버전의 통계연도 순서만 지킨 재현입니다. 통계연도와 실제 공개일은 다르며 수정 전 자료·발표 지연을 검증하지 못했습니다. 유사성도 원인이나 정책 효과가 아닙니다. 고령화의 부드러운 추세가 잘 맞는다고 뉴스 효과가 입증되지는 않습니다. 사망률은 인구 집계 통계이며 개인 위험 판단에 사용할 수 없습니다.</p>{''.join(sections)}
<p><a href="results/social_transfer_results.json">계산 결과 JSON</a> · <a href="results/social_transfer_predictions.csv">연도별 예측·선택 기록</a> · <a href="results/social_transfer_neighbors.csv">선택된 유사 사례</a> · <a href="social_transfer_protocol.json">고정 설계</a></p></body></html>'''
    (ROOT/'social_transfer_report.html').write_text(body,encoding='utf8')
if __name__=='__main__':main()
