"""Post-hoc descriptive screen, never a significance/production certification."""
from pathlib import Path
import json,csv
import numpy as np
from run_pilot import block_interval
ROOT=Path(__file__).resolve().parent
LABEL={'N0':'현재 값 유지','Trend':'최근 3년 평균 변화 연장','N1':'숫자 회귀','Analog':'유사 사례 5개','Selected':'과거 성적으로 방법 선택','Naive':'단순 기준','B1':'숫자 회귀','History':'과거 전체 오차 보정','Raw5':'유사 사례 결과 중앙값','Analog5':'유사 사례 오차 보정','News5':'뉴스 포함 유사 사례','Analog3':'유사 사례 3개','Original50':'지수·뉴스 50:50','Equal':'뉴스 균등 우선도','Psyche':'심리 뉴스 우선','Reverse':'결과 뉴스 우선','IndexOnly':'지수 쪽 조정','NewsOnly':'뉴스 쪽 조정'}
def csvrows(name):return list(csv.DictReader((ROOT/'results'/name).read_text(encoding='utf8').splitlines()))
def evaluate(rows,models,baseline,n_independent,length):
    base=np.array([abs(float(r['actual'])-float(r[baseline])) for r in rows]);out=[]
    for model in models:
        e=np.array([abs(float(r['actual'])-float(r[model])) for r in rows]);gain=100*(1-e.mean()/base.mean()) if base.mean() else 0.
        interval=block_interval(base-e,length) if gain>=10 and n_independent>=8 else None
        out.append(dict(model=model,mae=float(e.mean()),baseline_mae=float(base.mean()),improvement_pct=float(gain),n=len(rows),nonoverlap_n=n_independent,interval=interval,passes=bool(gain>=10 and n_independent>=8 and interval and interval[0]>0)))
    return out
def main():
    social=json.loads((ROOT/'results/social_transfer_results.json').read_text(encoding='utf8'))['results'];sr=csvrows('social_transfer_predictions.csv');catalog=[]
    for r in social:
        title=r['region_name']+' '+r['name']
        if 'summary' not in r:catalog.append(dict(name=title,status='미실행: 자료 또는 평가 부족',candidates=[]));continue
        rows=[x for x in sr if x['region']==r['region'] and x['problem']==r['problem']]
        catalog.append(dict(name=title,source='social_transfer_report.html',unit=r['unit'],status='실행',candidates=evaluate(rows,['Trend','N1','Analog','Selected'],'N0',len(rows),2)))
    diverse=json.loads((ROOT/'results/diverse_results.json').read_text(encoding='utf8'))['results'];dr=csvrows('diverse_predictions.csv');ar={(r['indicator'],r['date']):r for r in csvrows('analogue_predictions.csv')}
    for r in diverse:
        rows=[dict(x,**{k:v for k,v in ar[(x['indicator'],x['date'])].items() if k not in x}) for x in dr if x['indicator']==r['id']]
        models=['B1','Original50','Equal','Psyche','Reverse','IndexOnly','NewsOnly','History','Raw5','Analog5','News5','Analog3']
        catalog.append(dict(name=r['field']+' '+r['name']+(' 검색' if r['kind']=='search' else ''),source='analogue_report.html',unit=r['unit'],status='실행',candidates=evaluate(rows,models,'Naive',r['nonoverlap']['n'],3)))
    winners=[]
    for r in catalog:
        passing=[m for m in r['candidates'] if m['passes']]
        if passing:winners.append(dict(name=r['name'],unit=r['unit'],source=r['source'],**min(passing,key=lambda m:m['mae'])))
    result=dict(status='POST_HOC_SCREEN_NOT_CONFIRMATORY',criteria=dict(min_improvement_pct=10,min_nonoverlap_n=8,descriptive_interval_lower_gt=0),winners=winners,all=catalog)
    (ROOT/'results/evidence_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# 예측 방법 핵심 결과 기록','', '기록일: 2026-10-26. 기준을 결과 확인 후 정한 사후 선별이며, 실전 타당성·통계적 유의성 인증이 아닙니다.','', '선별: 단순 기준 대비 MAE 10% 이상 감소 + 겹치지 않는 평가 8회 이상 + 기술적 95% 블록 구간 하한 > 0. 여러 후보 중 통과한 최소 오차 방식을 표에 표시합니다. 다중 비교 보정과 독립 미래 검증은 없습니다.','', '| 분야·문제 | 기록할 후보 방식 | 기준 MAE → 후보 MAE | 감소율 | 평가 수 | 차이 구간 |','|---|---|---:|---:|---:|---|']
    for r in winners:
        lo,hi=r['interval'];lines.append(f'| {r["name"]} | {LABEL[r["model"]]} | {r["baseline_mae"]:.4f} → {r["mae"]:.4f} | {r["improvement_pct"]:.2f}% | {r["n"]} | [{lo:.4f}, {hi:.4f}] |')
    lines+=['','단위는 각 원보고서의 목표 단위입니다. 현재 값 유지보다 좋다는 뜻이지, 다른 모든 단순 추세 모델보다 좋다는 뜻은 아닙니다. 고령화·출산율은 수정된 인구 추계와 부드러운 추세의 영향을 받을 수 있습니다.','', '## 제외·보류 기록','', '| 대상 | 판단 |','|---|---|']
    for r in catalog:
        if any(x['name']==r['name'] for x in winners):continue
        reason=r['status'] if not r['candidates'] else ('독립적 기간 부족: 비중복 평가 4회' if r['candidates'][0]['nonoverlap_n']<8 else '10% 개선·구간 하한·평가 수를 함께 만족하지 못함')
        lines.append(f'| {r["name"]} | {reason} |')
    lines+=['','원·달러 고정 50:50의 2.94% 개선도 10% 기준 미달 및 구간 0 포함으로 핵심 표에서 제외합니다. 최초 상품 10개·내부 가중치 실험은 추가 후보 기록이며 이 표의 통합 재계산 대상은 최신 15개 지표와 한국·미국 사회문제입니다.','', '기사 공개시각·통계 최초 발표 버전은 미검증입니다. 검색 표본의 제한과 사회문제 지표 정의 차이를 원보고서에서 확인해야 합니다.','', '[사회문제 방법 비교](https://kfri-cloud.github.io/data-prediction-analysis/social_transfer_report.html) · [유사 사례 결과](https://kfri-cloud.github.io/data-prediction-analysis/analogue_report.html)']
    md='\n'.join(lines);(ROOT/'evidence_summary.md').write_text(md,encoding='utf8')
    import html
    body='<h1>크게 의미 있는 예측 후보 기록</h1><p>사후 선별 기준: 오차 10% 이상 감소 · 비중복 평가 8회 이상 · 기술적 구간 하한 양수. 실전 검증 통과가 아닙니다.</p><table><tr><th>분야·문제</th><th>후보 방법</th><th>기준 MAE</th><th>후보 MAE</th><th>감소율</th><th>평가 수</th><th>차이 구간</th></tr>'
    for r in winners:
        lo,hi=r['interval'];body+=f'<tr><td>{r["name"]}</td><td>{LABEL[r["model"]]}</td><td>{r["baseline_mae"]:.4f}</td><td>{r["mae"]:.4f}</td><td>{r["improvement_pct"]:.2f}%</td><td>{r["n"]}</td><td>[{lo:.4f}, {hi:.4f}]</td></tr>'
    body+='</table><p>같은 자료에서 여러 방법을 시험한 뒤 고른 후보입니다. 미래 성능이나 인과 효과를 입증하지 않습니다. 전체 근거와 제외 기록:</p><pre>'+html.escape(md)+'</pre><p><a href="evidence_summary.md">기록 Markdown</a> · <a href="results/evidence_summary.json">전체 계산 JSON</a></p>'
    (ROOT/'evidence_summary.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>핵심 예측 후보 기록</title><style>body{font:16px/1.8 system-ui;max-width:1400px;margin:auto;padding:28px;color:#17283d}table{border-collapse:collapse;width:100%}td,th{padding:12px;border-bottom:1px solid #ddd}pre{white-space:pre-wrap;background:#f4f7fb;padding:20px;font-size:14px}</style><body><nav><a href="index.html">전체 기록</a> · <a href="social_transfer_report.html">사회문제</a></nav>'+body+'</body></html>',encoding='utf8')
    print(json.dumps(winners,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
