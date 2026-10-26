from pathlib import Path
from html import escape
import json
ROOT=Path(__file__).resolve().parent
STYLE='body{font:16px/1.8 system-ui,sans-serif;background:#f4f7fb;color:#172b45;margin:auto;max-width:1300px;padding:30px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}.notice{padding:20px;background:#fff4d6;border-left:5px solid #b7791f}.meta{color:#61718a}.table{overflow:auto}a{color:#1d54b9}small{color:#61718a}'

def fmt(v):return '—' if v is None else f'{v:.3f}'

def overview():
    r=json.loads((ROOT/'results/social_results.json').read_text(encoding='utf8'))
    cat=json.loads((ROOT/'social_catalog.json').read_text(encoding='utf8'))
    topics=''.join(f'<li>{escape(p["name"])} — {escape(p["target"])}</li>' for p in cat['problems'])
    return f'''<section id="social"><h2>사회문제 10선: 한국과 미국 별도 실험</h2>
<div class="notice"><strong>요청한 뉴스·지표 50:50 방법은 두 지역 모두 미실행이다.</strong><br>각 문제에 맞는 과거 뉴스·공개시각·관련 지표가 확보되지 않았다. 아래 숫자 기준선 테스트를 최종방법의 테스트로 표시하지 않는다.</div>
<p>한국 10개 문제를 중심으로 선정하고, 미국의 같은 문제 10개를 별도 비교 묶음으로 구성했다. 국가를 섞어 학습하거나 성능을 합산하지 않았다. 미국 결과는 한국의 타당성을 입증하지 않는다. 해외 전체를 대표하는 표본도 아니다.</p>
<p><strong><a href="social_korea_report.html">한국 10개: 숫자 기준선 6개 실행 · 최종방법 0개</a></strong></p>
<p><strong><a href="social_usa_report.html">미국 10개: 숫자 기준선 7개 실행 · 최종방법 0개</a></strong></p>
<ol>{topics}</ol>
<h3>폐업률을 다른 숫자로 바꾸지 않았다</h3>
<p><a href="https://mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1069562&cbIdx=288">중소벤처기업부 공개 자료</a>에는 전체 사업자 및 소상공인 주요 6대 업종의 폐업 지표가 있지만, 이것을 동일한 소상공인 모집단의 장기 폐업률로 간주하지 않았다. 미국의 사업체 퇴출·폐업 자료도 한국 사업자등록 폐업과 정의가 다를 수 있어 별도 검증 전 숫자를 넣지 않았다.</p>
<h3>실행한 것은 무엇인가</h3>
<p>공개된 세계은행 연간 통계에서 과거 4년의 수준·변화를 이용하는 고정 릿지 회귀와 ‘직전 값 유지’ 기준선을 비교했다. 해당 나라·문제의 과거 값만 사용하고, 결측 연도를 보간하지 않았다. 훈련 표본 10개 이상, 평가 연도 5개 이상을 요구했다. 평가 대상은 자료가 있는 2016~2025년이다. 단위가 다른 지표의 MAE를 평균내거나 순위로 섞지 않았다.</p>
<p>이것은 현재 내려받은 통계를 연도순으로 배치한 진단용 실험이다. 당시 발표일·수정 버전을 확인한 진짜 실시간 재현이 아니며, 평활화되거나 모형으로 추정된 통계는 단순 모델로도 잘 맞을 수 있다. 예를 들어 고령부양비의 큰 개선율을 뉴스 예측이 성공했다는 근거로 해석할 수 없다.</p>
<p>최신 관측이 2025년이고 숫자 테스트 조건을 충족한 항목에만 2026년 조건부 숫자 외삽을 제시했다. 2024년 이전에 끝나는 통계로 2026년 값을 여러 해 외삽하지 않았다. 예측 확률·신뢰구간·위험 경고를 발행하지 않았으며, 개인 위험이나 정책 효과를 예측한 결과도 아니다.</p>
<h3>최종방법으로 넘어가기 위한 조건</h3>
<p>각 문제의 대상과 분모를 고정하고, 당시 확보할 수 있었던 수치 버전과 원문 뉴스, 문제별 방향 추출 규칙, 적합한 관련 지표를 마련해야 한다. 이후 숫자·관련 지표 모델과 뉴스·방향 모델을 따로 검증하고 50:50으로 결합해야 한다. 환율 모델의 계수나 네 주가지수를 모든 사회문제에 그대로 넣는 것은 이번에 하지 않았다.</p>
<p><a href="social_catalog.json">10선과 정확한 지표 정의</a> · <a href="social_protocol.json">실행·미실행 기준</a> · <a href="results/social_results.json">두 지역 결과</a> · <a href="results/social_sources.json">출처·수집시각</a> · <a href="results/social_lock.json">고정 해시</a></p></section>'''

def regional(region):
    r=json.loads((ROOT/f'results/social_{region}.json').read_text(encoding='utf8'));rows='';projections='';details=''
    for p in r['problems']:
        tested=p['baseline_status']=='RETROSPECTIVE_NUMERIC_DIAGNOSTIC_ONLY'
        if tested:
            status=f'숫자만 실행 ({p["n_evaluation"]}개 연도)'
            gain=f'{p["relative_improvement_pct"]:+.2f}%' if p['relative_improvement_pct'] is not None else '계산 불가'
        else:
            status='미실행: 연속 자료·정의 부족' if p['baseline_status']=='NOT_EXECUTED_NO_HARMONIZED_SERIES' else f'미실행: 평가 표본 부족 ({p.get("eligible_evaluation_years",0)}개)'
            gain='—'
        latest=f'{p["latest_year"]}: {fmt(p["latest_value"])}' if 'latest_year' in p else '미확보'
        rows+=f'<tr><td>{escape(p["name"])}</td><td>{latest}<br><small>{escape(p["unit"])}</small></td><td>{status}</td><td>{fmt(p.get("naive_mae"))}</td><td>{fmt(p.get("ridge_mae"))}</td><td>{gain}</td><td>미실행</td></tr>'
        q=p['projection_2026']
        if q:projections+=f'<tr><td>{escape(p["name"])}</td><td>{fmt(q["N0"])}</td><td>{fmt(q["N1"])}</td><td>{escape(p["unit"])}</td></tr>'
        details+=f'<li><strong>{escape(p["name"])}</strong>: {escape(p["target"])}. {escape(p["definition_issue"])}. <a href="{escape(p.get("source_api",p["source"]))}">출처</a></li>'
    return f'''<h1>{escape(r['region_name'])} 사회문제 10선 — 별도 실험</h1>
<div class="notice"><strong>최종 50:50 방법: 0개 실행. 숫자 기준선: {r['numeric_baselines_executed']}개 실행.</strong><br>뉴스·관련 지표 자료 부족으로 최종방법을 실행하지 않았다. 다른 지역의 관측·모델·성능을 섞지 않았다.</div>
<div class="table"><table><tr><th>문제</th><th>최신 수록 값</th><th>숫자 기준선 상태</th><th>직전 값 MAE</th><th>회귀 MAE</th><th>회귀 개선율</th><th>50:50 방법</th></tr>{rows}</table></div>
<p class="meta">양의 개선율은 직전 값 유지보다 회귀 오차가 작다는 뜻이다. MAE는 각 행의 단위이며 행끼리 직접 비교할 수 없다. 숫자 기준선의 성능을 뉴스 모델 성능으로 해석하면 안 된다. 수록 연도는 실제 발표일이 아니다.</p>
<h2>2026년 조건부 숫자 외삽 — 최종방법 예측 아님</h2>
<p>2025년까지 값이 있는 항목만 계산했다. 과거 추세가 이어진다는 가정 아래의 단순 숫자 추정이며 뉴스·시장 충격을 반영하지 않는다. 직전 값 유지와 회귀 값을 둘 다 제시하고, 더 잘 맞은 모델로 바꿔 선택하지 않았다. 보정된 확률이나 운영용 경고가 아니다.</p>
<div class="table"><table><tr><th>문제</th><th>직전 값 유지</th><th>회귀 외삽</th><th>단위</th></tr>{projections}</table></div>
<h2>정의와 자료 한계</h2><ul>{details}</ul>
<p>공통 누락: 문제별 과거 뉴스 원문·발표시각, 통계 최초 발표 버전, 적합한 관련 지표. 주거비·폐업률은 다른 지표로 대체하지 않았다. 교통사망은 수록자료가 2019년에 끝나 평가연도가 4개뿐이라 미실행 처리했다. 최신 연도가 오래된 자살·대기오염 등의 결과를 현재 상태 예측으로 표시하지 않았다.</p>
<p><a href="results/social_{region}.json">이 지역 전체 결과 JSON</a> · <a href="results/social_baseline_predictions.csv">지역 코드가 분리된 개별 평가 CSV</a> · <a href="social_report.html">공통 기준·10선 선정 설명</a></p>'''

def main():
    pages={'social_report.html':overview(),'social_korea_report.html':regional('KOR'),'social_usa_report.html':regional('USA')}
    for name,body in pages.items():
        (ROOT/name).write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>데이터예측분석 | 사회문제 지역별 테스트</title><style>'+STYLE+'</style><body><nav><a href="social_report.html">사회문제 개요</a> · <a href="social_korea_report.html">한국</a> · <a href="social_usa_report.html">미국</a></nav>'+body+'</body></html>',encoding='utf8')
if __name__=='__main__':main()
