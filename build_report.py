"""Audit published results and produce a Korean evidence report. No model training."""
from pathlib import Path
from html import escape
import csv
import hashlib
import json
from lxml import html
from audit_data import main as run_audit

ROOT = Path(__file__).resolve().parent
PAPER = "https://arxiv.org/html/2607.06973v1"


def extract_results():
    document = html.fromstring((ROOT / "data/timesx_paper.html").read_bytes())
    rows_by_variable = {}
    main_values = None
    main_headers = ["Meta", "Meta+Date", "Meta+Date+Cov", "Meta+Date+Event", "Meta+Date+Event+Cov"]
    required = {"Meta+Date", "Meta+Date+Cov", "Meta+Date+Event", "AllContext"}
    for table in document.xpath("//table"):
        rows = [[" ".join(c.text_content().split()) for c in row.xpath("./th|./td")]
                for row in table.xpath(".//tr")]
        if not rows:
            continue
        if rows[0][1:] == main_headers:
            selected = [r for r in rows if r and r[0] == "MASE"]
            if len(selected) != 1:
                raise ValueError("Ambiguous Table 5 MASE row")
            main_values = dict(zip(main_headers, map(float, selected[0][1:]), strict=True))
        labels = {r[0] for r in rows if r}
        if required.issubset(labels):
            if rows[0][0] != "Method":
                raise ValueError("Unexpected per-variable table header")
            variables = rows[0][1:]
            configs = {r[0]: r[1:] for r in rows[1:]}
            if any(len(configs[key]) != len(variables) for key in required):
                raise ValueError("Misaligned table cells")
            for i, variable in enumerate(variables):
                if variable in rows_by_variable:
                    raise ValueError("Duplicate variable: " + variable)
                rows_by_variable[variable] = {key: (None if configs[key][i] in ("–", "—", "-", "") else float(configs[key][i])) for key in sorted(required)}
    if main_values is None or not rows_by_variable:
        raise ValueError("Expected ablation tables not found")
    # Check the pinned source, not a claim that the underlying study has been reproduced.
    assert main_values == {"Meta": 0.787, "Meta+Date": 0.670, "Meta+Date+Cov": 0.674,
                           "Meta+Date+Event": 0.674, "Meta+Date+Event+Cov": 0.650}
    assert len(rows_by_variable) == 189, "Pinned paper appendix extraction changed"
    comparisons = []
    for base, news in [("Meta+Date", "Meta+Date+Event"), ("Meta+Date+Cov", "AllContext")]:
        differences = [v[base] - v[news] for v in rows_by_variable.values()
                       if v[base] is not None and v[news] is not None]
        comparisons.append({
            "baseline": base, "with_events": news,
            "improved": sum(x > 1e-10 for x in differences),
            "tied_at_published_precision": sum(abs(x) <= 1e-10 for x in differences),
            "worsened": sum(x < -1e-10 for x in differences),
            "variables_with_paired_scores": len(differences),
            "variables_excluded_for_missing_score": len(rows_by_variable) - len(differences)
        })
    return {
        "source": PAPER, "source_sections": ["Table 5", "Appendix Y.3"],
        "source_sha256": hashlib.sha256((ROOT / "data/timesx_paper.html").read_bytes()).hexdigest(),
        "evidence_type": "RECALCULATION_OF_ROUNDED_PUBLISHED_TABLES_NOT_MODEL_REPRODUCTION",
        "model": "Gemini-2.0-Flash as reported by the authors",
        "main_mase": main_values,
        "main_relative_improvement_events_without_covariates_pct":
            100 * (main_values["Meta+Date"] - main_values["Meta+Date+Event"]) / main_values["Meta+Date"],
        "main_relative_improvement_events_with_covariates_pct":
            100 * (main_values["Meta+Date+Cov"] - main_values["Meta+Date+Event+Cov"]) / main_values["Meta+Date+Cov"],
        "per_variable_comparisons": comparisons,
        "limitations": [
            "189 variable columns are extractable in the pinned Appendix Y.3 tables; the paper describes 190 benchmark variables. No result is invented for the difference.",
            "Scores are rounded and aggregate; raw paired forecast errors were not evaluated, and no significance or confidence interval is inferred.",
            "These variable win counts are not independent trials and are not a probability that current forecasts will succeed.",
            "The ablation evaluates constructed event context; it does not establish the causal effect of news or validate Korean SME forecasts."
        ]
    }


def create_report(audit, evidence):
    comparisons = evidence["per_variable_comparisons"]
    def outcome_rows():
        labels = ["관련 지표 없이 사건 정보 추가", "관련 지표가 있는 상태에서 사건 정보 추가"]
        return "".join(f"<tr><td>{label}</td><td>{c['improved']}</td><td>{c['tied_at_published_precision']}</td><td>{c['worsened']}</td><td>{c['variables_excluded_for_missing_score']}</td></tr>"
                       for label, c in zip(labels, comparisons, strict=True))
    audit_rows = "".join(f"<tr><td>{escape(x['file'])}</td><td>{x['rows']:,}</td><td>{escape(', '.join(x['columns']))}</td><td>공개 시점 재검증 필요</td></tr>" for x in audit["files"])
    no_cov = evidence["main_relative_improvement_events_without_covariates_pct"]
    with_cov = evidence["main_relative_improvement_events_with_covariates_pct"]
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>뉴스 반영 예측 — 타당성 검토</title><style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#172b45;font:16px/1.85 system-ui,"Malgun Gothic",sans-serif}}
main{{max-width:1080px;margin:auto;padding:48px 28px 80px}}h1{{font-size:34px;line-height:1.4}}h2{{font-size:24px;margin-top:44px}}p{{max-width:950px}}a{{color:#1d54b9}}table{{border-collapse:collapse;width:100%;font-size:14px;background:white}}th,td{{padding:13px;text-align:left;border-bottom:1px solid #dbe3ef;vertical-align:top}}th{{background:#e9eff8}}.table{{overflow:auto}}.notice{{padding:22px 26px;border-left:5px solid #b7791f;background:#fff8e6;border-radius:8px}}.blue{{border-color:#3267ce;background:#eaf1ff}}.meta{{color:#61718a;font-size:14px}}code{{font-size:13px;overflow-wrap:anywhere}}li{{margin:7px 0}}.flow{{padding:18px;background:white;border:1px solid #dbe3ef;border-radius:8px}}@media(max-width:600px){{main{{padding:24px 16px}}h1{{font-size:27px}}}}
</style></head><body><main>
<p class="meta">2026-10-26 · 문헌 조사 + 공개 데이터 감사 + 사전 검증 설계</p>
<h1>뉴스가 미래 예측에 도움이 되는가?</h1>
<div class="notice"><strong>판정: 조건부 가능성은 확인. 서울 소상공인 현재 예측의 타당성은 아직 미확인.</strong><br>
다른 분야의 개선 사례는 연구를 시작할 근거다. 우리 대상에서의 시간순 검증과 실제 미래 기록이 있어야 적용 근거가 된다. 아래 1~6절은 초기 문헌 감사 기록이며, 후속 탐색 실험 결과는 별도 링크와 하단에 추가했다.</div>
<p><strong><a href="pilot_report.html">후속 실행 결과: 시간순 47개 시점 비교 — 뉴스 추가 시 평균 오차 5.07% 증가</a></strong><br>공개시점 입증이 미완료인 탐색 실험이며, 서울 소상공인 적용의 타당성은 미확인이다.</p>
<h2>1. 무엇을 입증해야 하는가</h2>
<p>검증할 가설은 “같은 시점에 이용 가능한 숫자 정보가 같을 때, 뉴스를 추가한 예측이 이후 실제 결과를 더 잘 예측한다”이다. 뉴스가 변화를 일으켰다는 인과관계와 현재에도 반드시 통한다는 주장은 별개다.</p>
<div class="flow">더 오래된 기간으로 학습 → 이후 과거 구간 예측 → 여러 시작점에서 반복 → 마지막 보류 구간 확인 → 현재 예측을 미리 저장 → 새 결과와 비교</div>
<p>앞 단계가 반복 통과하면 현재 적용을 지지하는 경험적 근거가 생긴다. 그 근거는 데이터 수집 방식·뉴스의 의미·경제 환경·대상 업종이 충분히 유사하다는 조건을 가진다. 과거 성능만으로 “현재 타당할 확률 90%”를 산출할 수는 없다.</p>
<h2>2. 연구 결과는 혼합되어 있다</h2>
<div class="table"><table><thead><tr><th>연구·자료</th><th>확인한 내용</th><th>적용 한계</th></tr></thead><tbody>
<tr><td><a href="https://huggingface.co/papers/2406.08627">Time-MMD · NeurIPS 2024</a></td><td>논문은 숫자에 문서를 결합했을 때 여러 과제에서 예측 오차 감소를 보고한다.</td><td>뉴스와 보고서가 혼합된 영어 데이터다. 한국 폐업·매출과 동일한 문제는 아니다. 발표 성능을 직접 재학습한 결과가 아니다.</td></tr>
<tr><td><a href="{PAPER}">TimesX · ICML 2026</a></td><td>사건 정보와 다른 관련 지표의 조합에 따라 효과가 다르다. 시간 분리와 모델의 학습 지식 누출을 다룬다.</td><td>구성된 사건 문맥을 이용한 벤치마크다. 국내 분기별 소상공인 자료의 검증을 대체하지 못한다.</td></tr>
<tr><td><a href="https://arxiv.org/html/2506.11050v1">NSW-EPNews · 2025 preprint</a></td><td>전력가격 과제에서는 뉴스의 추가 효과가 제한적이며, LLM 출력의 신뢰성 문제도 보고한다.</td><td>일부 LLM 비교는 뉴스와 날씨·프롬프트가 함께 바뀐다. 뉴스 단독 인과효과를 계산하는 실험으로 볼 수 없다.</td></tr>
<tr><td><a href="https://huggingface.co/DecisionIntelligence/Aurora">Aurora · Hugging Face 모델</a></td><td>숫자와 텍스트를 입력받아 확률적 시계열 예측을 만드는 구현 후보다.</td><td>모델 존재 자체는 성능 증거가 아니다. 이번에는 다운로드·실행하지 않았다. 학습기간과 평가자료 중복도 검토해야 한다.</td></tr>
</tbody></table></div>
<h2>3. 논문 표를 직접 읽어 재계산한 결과</h2>
<p>TimesX Table 5의 Gemini-2.0-Flash 비교다. 각 설정은 숫자 시계열을 입력받는다. 아래 MASE는 작을수록 좋은 오차 지표이며, 원문에 반올림해 발표된 수치를 사용했다.</p>
<div class="table"><table><thead><tr><th>추가 문맥</th><th>MASE</th><th>같은 조건에서 사건 추가의 변화</th></tr></thead><tbody>
<tr><td>설명 + 날짜</td><td>0.670</td><td>비교 기준</td></tr><tr><td>설명 + 날짜 + 사건</td><td>0.674</td><td>약 {abs(no_cov):.2f}% 악화</td></tr>
<tr><td>설명 + 날짜 + 관련 지표</td><td>0.674</td><td>비교 기준</td></tr><tr><td>설명 + 날짜 + 관련 지표 + 사건</td><td>0.650</td><td>약 {with_cov:.2f}% 개선</td></tr>
</tbody></table></div>
<p>같은 논문 부록 Y.3에서 추출 가능한 <strong>189개 변수 열</strong>도 비교했다. 벤치마크 전체는 190개로 설명되지만, 해당 고정 버전의 표에서 추출된 열은 189개다. 누락 차이를 추정해 채우지 않았다.</p>
<div class="table"><table><thead><tr><th>비교</th><th>개선</th><th>동률</th><th>악화</th><th>결측 제외</th></tr></thead><tbody>{outcome_rows()}</tbody></table></div>
<p class="meta">원문 Table 5 및 Appendix Y.3 자동 추출. 이는 학습 재현이나 새 예측 실험이 아니다. 변수별 집계는 서로 독립인 시행이 아니며, 원시 예측 오차가 없으므로 유의확률·신뢰구간을 계산하지 않았다. 동률은 발표 정밀도 기준이다. 위 비율을 현재 예측의 성공확률로 읽으면 안 된다.</p>
<h2>4. 공개 원자료를 직접 감사한 결과</h2>
<p>Time-MMD 공식 저장소의 경제 자료를 고정 커밋으로 내려받아 행·열·해시를 검사했다. Hugging Face의 <a href="https://huggingface.co/datasets/lamblamb/time-mmd-economy">경제 데이터 미러</a> 대신 공식 CSV를 감사 대상으로 삼았다.</p>
<div class="table"><table><thead><tr><th>파일</th><th>행 수</th><th>실제 열</th><th>판정</th></tr></thead><tbody>{audit_rows}</tbody></table></div>
<p>텍스트 CSV에는 start_date·end_date·fact·preds가 있지만 별도의 기사 공개시각·원본 URL·과거 버전 증빙 열이 없다. 숫자 CSV에도 실제 발표시각과 수정 전 수치 버전 열이 없다. <strong>기간 표기만으로 당시에 알려졌던 정보임을 인증할 수 없다.</strong> 숫자 행은 시간 오름차순도 아니므로 순서대로 잘라 학습하면 안 된다.</p>
<p>이 감사는 원논문이 틀렸거나 실제로 누출됐다는 판정이 아니다. 다운로드한 파일만으로 우리의 엄격한 검증 요건을 확인할 수 없다는 뜻이다. preds는 실제 미래 관측값으로 사용하지 않는다.</p>
<p><a href="results/data_audit.json">전체 감사 결과</a> · <a href="data/manifest.json">출처·SHA-256 목록</a> · <a href="results/literature_recalculation.json">논문 수치 재계산</a></p>
<h2>5. 우리 대상에 적용할 검증 설계</h2>
<ol>
<li><strong>자료 자격:</strong> 기사 공개시각, 사건시각, 원본 버전과 통계 발표시각·당시 수치를 연결한다. 발표 전 수치와 나중에 수정된 기사 내용을 차단한다.</li>
<li><strong>동일 조건 비교:</strong> 계절 기준선, 숫자만, 숫자+뉴스, 숫자+기사량, 숫자+오래된 뉴스 대조군을 비교한다. 같은 숫자 정보·학습 예산을 준다.</li>
<li><strong>대과거 → 과거:</strong> 학습 구간을 앞으로 이동하며 반복 검증한다. 검증 결과로 정한 모형은 마지막 보류 구간에서 한 번 확인한다.</li>
<li><strong>판정:</strong> 주 지표는 MAE 차이다. 제안한 실용 기준은 5% 개선이며 보편적 통계 법칙이 아니다. 같은 예측시점의 지역들을 묶은 시간 블록 분석으로 불확실성을 평가한다. 우연한 승리와 다중비교를 통제한다.</li>
<li><strong>확률·경고:</strong> 변화량 오차 개선과 “하락 확률 70%”의 타당성은 다른 검증이다. 확률을 내면 Brier 점수·보정 정도와 거짓 경고를 따로 평가한다.</li>
<li><strong>현재 검증:</strong> 예측값과 모델을 결과 발표 전에 고정·저장한다. 실제 결과가 쌓이면 비교한다. 성능이 달라지면 현재 경고를 재검토한다.</li>
</ol>
<p>서울 분기 자료는 독립적인 시간 표본 수가 적을 수 있다. 자치구 수를 곱해 시간 증거가 충분하다고 판단하지 않는다. 최초 제안 대상은 다음 분기의 추정매출 변화이며 개별 가게 폐업확률은 아니다. 정확한 업종·집계식·날짜 경계는 실제 자료 감사 후, 모델 성능을 보기 전에 확정한다.</p>
<p><a href="protocol.json">모델 실행 전 작성한 검증 프로토콜</a></p>
<h2>6. 초기 문헌 감사 시점의 실행 기록</h2>
<div class="notice blue"><strong>실행 완료:</strong> 논문 원문 확인, 고정 버전 데이터 다운로드와 해시 검증, CSV 시간정보 감사, TimesX 표 자동 추출·재계산, 시간정보 차단 테스트 10개 통과.<br>
<strong>초기 감사 당시 미실행:</strong> 예측 모델 학습, 한국 자료 백테스트, 현재 실시간 예측, 3D 경고 화면. 후속 작업에서 원·달러 탐색 모델은 실행했으며, 서울 매출 검증·현재 실시간 예측·3D 경고는 여전히 미실행이다.</div>
<p>다음 실험에 필요한 것은 공개시점과 과거 수치 버전을 입증할 수 있는 대상 자료다. 이를 확보한 뒤 숫자만 쓴 기준선과 뉴스 추가 모델을 동일 조건에서 비교한다. 조건이 충족되지 않으면 “성능이 좋아 보이는 결과”를 입증 자료로 제출하지 않는다.</p>
<p class="meta">검토 방식: evaluate 스킬의 대체 경로로 기계적 확인과 의미 검토를 수행했다. Ouroboros 평가 서버의 승인이나 다중모델 합의는 실행하지 않았다. 테스트 통과는 감사 코드 동작에 관한 결과이며 예측 타당성 승인이 아니다.</p>
<details><summary>재현 명령과 의존성</summary><p>Python 표준 라이브러리로 다운로드·감사·테스트를 실행한다. 논문 표 추출에는 lxml이 필요하다(현재 로컬 환경에서 사용 가능).</p><pre>python fetch_sources.py
python audit_data.py
python -m unittest -v test_audit.py
python build_report.py</pre><p>작업 폴더: <code>D:\\Codex\\CS\\news-evidence-lab</code><br>데이터 커밋: <code>{audit['repository_commit']}</code></p></details>
</main></body></html>'''


def main():
    run_audit()
    audit = json.loads((ROOT / "results/data_audit.json").read_text(encoding="utf-8"))
    evidence = extract_results()
    (ROOT / "results/literature_recalculation.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    report = create_report(audit, evidence)
    if (ROOT / "results/pilot_results.json").exists():
        from build_pilot_report import section
        report = report.replace('</main>', section() + '</main>')
    if (ROOT / "results/keyword_results.json").exists():
        from build_keyword_report import section as keyword_section
        report = report.replace('<h2>1.', '<p><strong><a href="keyword_report.html">추가 비교: 키워드 중심 모델 결과 보기</a></strong></p><h2>1.', 1)
        report = report.replace('</main>', keyword_section() + '</main>')
    if (ROOT / "results/event_results.json").exists():
        from build_event_report import section as event_section
        report = report.replace('</main>', event_section() + '</main>')
        navigation = '''<nav class="notice blue" aria-label="전체 연구 기록"><strong>전체 연구 기록</strong><ol>
<li><a href="#literature">문헌 검토·자료 감사·검증 설계</a></li>
<li><a href="pilot_report.html">숫자 대 단어 해시 시간순 실험</a></li>
<li><a href="keyword_report.html">키워드 중심 비교</a></li>
<li><a href="event_report.html">최신: 방향·주체·예상 대비 차이 비교</a></li>
</ol><p>모든 실험은 탐색 단계다. 현재 예측·서울 소상공인 적용의 타당성은 미입증이며, 전체 맥락 언어모델은 아직 평가하지 않았다.</p></nav>'''
        report = report.replace('<h2>1.', navigation + '<h2 id="literature">1.', 1)
    if (ROOT / "results/market_results.json").exists():
        from build_market_report import section as market_section
        report = report.replace('</main>', market_section() + '</main>')
        report = report.replace('</ol><p>모든 실험', '<li><a href="market_report.html">최신: S&P 500·나스닥 100·코스피·코스닥 결합 비교</a></li></ol><p>모든 실험', 1)
    (ROOT / "report.html").write_text(report, encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=True, indent=2))
    print("Report: " + str(ROOT / "report.html"))


if __name__ == "__main__":
    main()
