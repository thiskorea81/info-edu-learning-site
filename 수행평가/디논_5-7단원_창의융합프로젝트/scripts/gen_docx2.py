# -*- coding: utf-8 -*-
"""Build per-unit student report templates + worked examples (stdlib-only docx).

실행 방법 (이 폴더 기준):
    python3 gen_diagrams.py   # 회로 구조도 PNG 생성 (diagrams/ 폴더)
    python3 gen_docx2.py      # 학생용 양식 2개 + 교사용 예시 보고서 8개(구조도 포함) 생성
    python3 gen_teacher_guide.py  # 교사용 즉석질문가이드 생성

산출물은 이 스크립트 폴더의 상위 폴더(수행평가/디논_5-7단원_창의융합프로젝트/)와
그 안의 교사용_비공개/ 폴더에 저장된다.
"""
import zipfile
from xml.sax.saxutils import escape

def esc(s):
    return escape(str(s))

def para(text="", bold=False, size=None, align=None, space_after=120, space_before=0, border_bottom=False, italic=False):
    rpr = ""
    if bold:
        rpr += "<w:b/>"
    if italic:
        rpr += "<w:i/>"
    if size:
        rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    rpr_xml = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    ppr = f'<w:spacing w:before="{space_before}" w:after="{space_after}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    if border_bottom:
        ppr += '<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="999999"/></w:pBdr>'
    run = f'<w:r>{rpr_xml}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>' if text else ""
    return f'<w:p><w:pPr>{ppr}</w:pPr>{run}</w:p>'

def heading(text, level=1):
    size = "32" if level == 1 else "26"
    align = "center" if level == 1 else None
    return para(text, bold=True, size=size, align=align, space_after=200, space_before=200 if level > 1 else 0)

def blank_lines(n=3, filled=None):
    if filled:
        lines = filled if isinstance(filled, list) else [filled]
        out = "".join(para(t, space_after=280, border_bottom=True) for t in lines)
        for _ in range(max(0, n - len(lines))):
            out += para("", space_after=280, border_bottom=True)
        return out
    return "".join(para("", space_after=280, border_bottom=True) for _ in range(n))

def checkbox(text, checked=False):
    box = "☑" if checked else "☐"
    return para(f"{box}  {text}", space_after=60)

def bullet(text):
    return para(f"•  {text}", space_after=60)

def cell(text_or_xml, width, bold=False, shade=None, valign="center"):
    if isinstance(text_or_xml, str) and not text_or_xml.startswith("<w:p"):
        content = para(text_or_xml, bold=bold, space_after=40)
    else:
        content = text_or_xml
    shade_xml = f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>' if shade else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>'
            f'<w:vAlign w:val="{valign}"/>{shade_xml}</w:tcPr>{content}</w:tc>')

def row(cells_xml):
    return f'<w:tr>{"".join(cells_xml)}</w:tr>'

def picture_paragraph(rel_id, cx_emu, cy_emu, name="circuit.png"):
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        f'<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        f'distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx_emu}" cy="{cy_emu}"/>'
        f'<wp:docPr id="1" name="{esc(name)}"/>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="0" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill>'
        f'<a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rel_id}"/>'
        '<a:stretch><a:fillRect/></a:stretch>'
        '</pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx_emu}" cy="{cy_emu}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )


def table(rows_xml, col_widths):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="4" w:color="666666"/>'
               '<w:left w:val="single" w:sz="4" w:color="666666"/>'
               '<w:bottom w:val="single" w:sz="4" w:color="666666"/>'
               '<w:right w:val="single" w:sz="4" w:color="666666"/>'
               '<w:insideH w:val="single" w:sz="4" w:color="666666"/>'
               '<w:insideV w:val="single" w:sz="4" w:color="666666"/>'
               '</w:tblBorders>')
    tblpr = f'<w:tblPr><w:tblW w:w="0" w:type="auto"/>{borders}<w:tblLayout w:type="fixed"/></w:tblPr>'
    return f'<w:tbl>{tblpr}<w:tblGrid>{grid}</w:tblGrid>{"".join(rows_xml)}</w:tbl>' + para("", space_after=120)


RUBRIC = [
    ("문제 정의의 구체성",
     "문제 상황이 없거나 매우 막연함 (예: \"논리 회로를 활용해 본다\" 수준)",
     "문제 상황은 있으나 대상이나 조건이 불명확함",
     "문제 상황에 대상과 조건 중 일부가 구체적으로 제시됨",
     "문제 상황에 대상·조건·목적이 모두 구체적으로 제시됨"),
    ("회로 확장·복합화",
     "교과서 회로를 그대로 재현",
     "입출력 개수 등 일부 수치만 변경",
     "교과서 소자 2개 이상을 조합해 새로운 기능 구성",
     "교과서 소자를 응용하여 교과서에 없는 새로운 회로 구조로 완성함"),
    ("동작 구현·검증 완성도",
     "시뮬레이션 미완성 또는 미동작",
     "일부 입력에서만 정상 동작",
     "전체 입력에서 정상 동작하나 검증 기록 미흡",
     "전체 동작을 진리표/타이밍도로 검증하고 기록함"),
    ("설계 근거의 논리성",
     "소자 선택 이유를 설명하지 못함(AI 제안을 그대로 옮겨 말하는 수준 포함)",
     "\"AI가 그렇게 하라고 해서\" 수준의 설명, 원리 설명 없음",
     "소자 특성과 연결지어 설명하나, AI 제안을 검증 없이 수용한 부분이 남아있음",
     "동작 원리에 근거해 논리적으로 설명하며, AI 제안 중 스스로 확인·수정한 부분을 구체적으로 제시함"),
    ("질의응답 대응력(즉석 변형 질문)",
     "교사의 즉석 변형 질문(예: 입력이 하나 늘어나면?)에 답하지 못함",
     "즉석 질문의 의도와 다른 답변을 하거나 암기한 내용만 반복함",
     "즉석 질문에 원리로 접근하나 정확성이 다소 부족함",
     "즉석 질문에 원리에 근거해 정확히 답하고, 회로를 어떻게 바꿔야 하는지까지 설명함"),
]

UNIT_INFO = {
    5: {
        "label": "5단원 (조합 논리 회로 응용)",
        "circuits": [
            "인코더 / 디코더",
            "멀티플렉서(MUX) / 디멀티플렉서(DEMUX)",
            "비교기",
            "코드 변환기 (BCD-3초과, 2진수-그레이 코드)",
        ],
        "topics": [
            "[인코더/디코더] 우선순위 인코더 기반 주차타워 최저 여유층 안내판",
            "[MUX/DEMUX] 방송실 신호원-교실 선택 송출 시스템",
            "[비교기] 계주 기록 비교 승리팀 표시기",
            "[코드 변환기] 그레이 코드-2진수 변환 회전 다이얼 표시기",
        ],
    },
    7: {
        "label": "7단원 (순서 논리 회로 응용)",
        "circuits": [
            "레지스터 (시프트·순환·직병렬)",
            "비동기식 카운터",
            "동기식 카운터",
            "링 카운터",
        ],
        "topics": [
            "[레지스터] 교실 출입센서 신호 직렬 전송 시스템",
            "[비동기식 카운터] 과학실 기구 대여 누적 횟수 표시기",
            "[동기식 카운터] 실험/발표 겸용 카운트업·다운 타이머",
            "[링 카운터] 학예회 팀 순서 표시등",
        ],
    },
}


def info_table(unit, example=False, name="", sid=""):
    info = UNIT_INFO[unit]
    w1, w2, w3, w4 = 1400, 3113, 1400, 3113
    return table([
        row([cell("학번", w1, bold=True, shade="EEEEEE"), cell(sid, w2),
             cell("이름", w3, bold=True, shade="EEEEEE"), cell(name, w4)]),
        row([cell("반", w1, bold=True, shade="EEEEEE"), cell("", w2),
             cell("제출일", w3, bold=True, shade="EEEEEE"), cell("", w4)]),
        row([cell("대상 단원", w1, bold=True, shade="EEEEEE"),
             cell(info["label"], w2 + w3 + w4)]),
    ], [w1, w2, w3, w4])


def rubric_table(marks=None):
    """marks: optional list of 5 ints (0/2/4/6) to mark as achieved, for example docs."""
    w0 = 1400
    wr = (9026 - w0) // 4
    rows = [row([cell("평가 항목", w0, bold=True, shade="EEEEEE"),
                 cell("0점", wr, bold=True, shade="EEEEEE"),
                 cell("2점", wr, bold=True, shade="EEEEEE"),
                 cell("4점", wr, bold=True, shade="EEEEEE"),
                 cell("6점", wr, bold=True, shade="EEEEEE")])]
    for i, (name, l0, l2, l4, l6) in enumerate(RUBRIC):
        levels = [0, 2, 4, 6]
        labels = [l0, l2, l4, l6]
        mark = marks[i] if marks else None
        cells = [cell(name, w0, bold=True, shade="F5F5F5")]
        for lvl, lab in zip(levels, labels):
            cells.append(cell(checkbox(f"{lvl}점: {lab}", checked=(mark == lvl)), wr))
        rows.append(row(cells))
    return table(rows, [w0, wr, wr, wr, wr])


def scoring_section(marks=None):
    parts = []
    parts.append(heading("6. 평가 기준 (자기 점검용 — 발표 후 교사가 최종 확정)", 2))
    parts.append(para("가. 응용점수 루브릭 (항목당 0/2/4/6점, 5개 항목 합산 최대 30점)", bold=True, space_after=80))
    parts.append(rubric_table(marks))
    parts.append(para("나. 최저 점수 보장 (9점)", bold=True, space_after=80, space_before=160))
    parts.append(para("위 응용점수 합계가 9점 미만이더라도, 보고서를 제출하고 발표에 참여했다면 "
                       "최저 9점을 보장합니다. (예: 응용점수 합계가 0~8점이면 9점으로 보정)",
                       space_after=160))
    parts.append(para("다. 점수 집계 (교사 작성란)", bold=True, space_after=80))
    sw = [3009, 3009, 3008]
    app_score = sum(marks) if marks else None
    total = max(app_score, 9) if marks else None
    parts.append(table([
        row([cell("응용점수 합계 ( / 30)", sw[0], bold=True, shade="EEEEEE"),
             cell("총점 (9~30점, 9점 미만 시 9점 보정)", sw[1], bold=True, shade="EEEEEE"),
             cell("교사 확인", sw[2], bold=True, shade="EEEEEE")]),
        row([cell(str(app_score) if app_score is not None else "", sw[0]),
             cell(str(total) if total is not None else "", sw[1]),
             cell("", sw[2])]),
    ], sw))
    parts.append(para("※ 체크리스트는 학생 자기 점검용이며, 최종 점수는 발표 후 교사가 확정합니다.",
                       space_before=120, space_after=0))
    return "".join(parts)


def build_body(unit, is_example=False, ex=None):
    info = UNIT_INFO[unit]
    parts = []
    tag = " — 예시 보고서(교사 전용)" if is_example else ""
    parts.append(heading(f"디지털논리회로 창의융합프로젝트 수행평가 보고서{tag}", 1))
    parts.append(para(f"{info['label']} · Tinkercad 시뮬레이터 활용", align="center", space_after=120))
    if is_example:
        parts.append(para("[교사 전용 — 학생에게 배포하지 마세요] 이 문서는 응용점수 루브릭의 상위 수준(6점)을 "
                           "보여주기 위한 채점 참고용 모범 예시입니다.",
                           italic=True, bold=True, align="center", space_after=240))

    parts.append(info_table(unit, example=is_example,
                             name=(ex["name"] if ex else ""), sid=(ex["sid"] if ex else "")))

    parts.append(heading("1. 프로젝트 개요", 2))
    parts.append(para("① 기반이 된 교과서 회로 (해당하는 것에 표시)", bold=True, space_after=80))
    for c in info["circuits"]:
        checked = is_example and ex and c == ex["base_circuit"]
        parts.append(checkbox(c, checked=checked))

    parts.append(para("② 프로젝트 제목", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(1, filled=[ex["title"]] if is_example else None))

    parts.append(para("③ 해결하고자 하는 실생활 문제 상황", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(3, filled=ex["problem"] if is_example else None))

    parts.append(para("④ 교과서 예제와 달라진 점(응용 포인트) 요약", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(3, filled=ex["application"] if is_example else None))

    parts.append(heading("참고 자료", 2))
    parts.append(para("① 교과서 그대로 설계해도 기본 요건은 충족됩니다. 기준이 되는 회로는 정보ON 학습자료 "
                       "(디논 05-01~05-04 / 07-01~07-03)를 참고하세요.", bold=True, space_after=120))
    parts.append(para("② 프로젝트 주제 아이디어 — 그대로 사용해도 되고, 자유롭게 다른 주제를 설계해도 됩니다.",
                       bold=True, space_after=80, space_before=120))
    for t in info["topics"]:
        parts.append(bullet(t))
    parts.append(para("③ 문제 정의 예시 (해결책·회로 설계는 제시하지 않습니다 — 스스로 완성하세요)",
                       bold=True, space_after=80, space_before=160))
    for label, ptext in PROBLEM_EXCERPTS[unit]:
        parts.append(para(label, bold=True, italic=True, space_after=40))
        parts.append(para(ptext, space_after=120))

    parts.append(heading("2. AI 활용 및 검증 과정", 2))
    parts.append(para("이 프로젝트는 AI의 도움을 받아도 됩니다. 다만 발표 중 교사가 회로를 즉석에서 바꿔보라고 "
                       "요청할 수 있으므로, AI가 준 내용을 얼마나 이해하고 검증했는지를 이 section과 질의응답으로 평가합니다.",
                       italic=True, space_after=160))
    parts.append(para("① 어떤 AI에게 무엇을 질문했는가", bold=True, space_after=80))
    parts.append(blank_lines(2, filled=[ex["ai"]["question"]] if is_example else None))
    parts.append(para("② AI 답변 중 틀렸거나 스스로 검증해서 수정한 부분", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(3, filled=ex["ai"]["correction"] if is_example else None))
    parts.append(para("③ AI 답변을 그대로 쓰지 않고 스스로 판단·추가한 부분", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(2, filled=[ex["ai"]["judgement"]] if is_example else None))

    parts.append(heading("3. 설계 내용", 2))
    parts.append(para("① 사용한 논리 소자 목록", bold=True, space_after=80))
    hw = [2400, 1200, 5426]
    device_rows = [row([cell("소자명", hw[0], bold=True, shade="EEEEEE"),
                         cell("개수", hw[1], bold=True, shade="EEEEEE"),
                         cell("역할", hw[2], bold=True, shade="EEEEEE")])]
    devices = ex["devices"] if is_example else [("", "", "")] * 4
    for d in devices:
        device_rows.append(row([cell(d[0], hw[0]), cell(d[1], hw[1]), cell(d[2], hw[2])]))
    parts.append(table(device_rows, hw))

    parts.append(para("② 회로도 (Tinkercad 회로 캡처를 붙여넣으세요)", bold=True, space_after=80))
    if is_example:
        diagram = ex.get("diagram_emu")
        if diagram:
            box_content = (picture_paragraph("rIdImg1", diagram[0], diagram[1])
                            + para(f"[구조도] {ex['circuit_note']}", space_after=120, space_before=120))
        else:
            box_content = para(f"[예시 설명] {ex['circuit_note']}", space_after=280) + "".join(
                para("", space_after=280) for _ in range(5))
    else:
        box_content = "".join(para("", space_after=280) for _ in range(8))
    parts.append(table([row([cell(box_content, 9026)])], [9026]))

    parts.append(para("③ 동작 설명 (입력에 따른 출력 동작을 순서대로 서술)", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(4, filled=ex["operation"] if is_example else None))

    parts.append(heading("4. Tinkercad 시뮬레이션 검증", 2))
    parts.append(para("① Tinkercad 공유(Share) 링크", bold=True, space_after=80))
    parts.append(blank_lines(1, filled=["https://www.tinkercad.com/things/xxxxxxxxxxx"] if is_example else None))
    parts.append(para("② 진리표 / 동작표 (직접 표를 그리거나 아래 표를 활용)", bold=True, space_after=80, space_before=160))
    if is_example:
        tbl_header = ex["table_header"]
        tbl_rows = ex["table_rows"]
        n = len(tbl_header)
        tw = [9026 // n] * (n - 1) + [9026 - (9026 // n) * (n - 1)]
        rows_xml = [row([cell(h, w, bold=True, shade="EEEEEE") for h, w in zip(tbl_header, tw)])]
        for r in tbl_rows:
            rows_xml.append(row([cell(v, w) for v, w in zip(r, tw)]))
        parts.append(table(rows_xml, tw))
    else:
        tw = [1128, 1128, 1128, 1128, 1128, 1128, 1128, 1130]
        parts.append(table([row([cell("", w) for w in tw]) for _ in range(6)], tw))
    parts.append(para("③ 테스트 결과 요약 (정상 동작 여부, 발견한 문제와 해결 과정)", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(3, filled=ex["test_result"] if is_example else None))

    parts.append(heading("5. 발표 준비 (1인당 발표 7분 + 질의응답 3분)", 2))
    for c in ["문제 상황 소개", "회로 설계 설명 (선택한 소자와 이유)",
              "Tinkercad 시뮬레이션 시연 / 결과 제시", "교과서 예제 대비 응용 포인트 강조",
              "AI 활용 및 검증 과정 설명", "마무리 및 소감"]:
        parts.append(checkbox(c, checked=is_example))
    parts.append(para("※ 질의응답 3분 중에는 교사가 회로를 즉석에서 바꿔보라고 요청할 수 있습니다.",
                       italic=True, space_before=100, space_after=0))

    parts.append(scoring_section(marks=[6, 6, 6, 6, 6] if is_example else None))

    return "".join(parts)


DOCUMENT_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
{body}
<w:sectPr>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/>
</w:sectPr>
</w:body>
</w:document>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults>
<w:rPrDefault><w:rPr>
<w:rFonts w:ascii="맑은 고딕" w:eastAsia="맑은 고딕" w:hAnsi="맑은 고딕" w:cs="맑은 고딕"/>
<w:sz w:val="21"/><w:szCs w:val="21"/>
</w:rPr></w:rPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
<w:name w:val="Normal"/>
</w:style>
</w:styles>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS_ROOT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

RELS_DOC_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
{image_rel}
</Relationships>"""


def write_docx(out_path, body, image_bytes=None, image_rel_id="rIdImg1"):
    document_xml = DOCUMENT_XML_TEMPLATE.format(body=body)
    import xml.dom.minidom as minidom
    minidom.parseString(document_xml.encode("utf-8"))
    image_rel = ""
    if image_bytes:
        image_rel = (f'<Relationship Id="{image_rel_id}" '
                     'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                     'Target="media/image1.png"/>')
    rels_doc = RELS_DOC_TEMPLATE.format(image_rel=image_rel)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS_ROOT)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/styles.xml", STYLES_XML)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
        if image_bytes:
            z.writestr("word/media/image1.png", image_bytes)
    print("written:", out_path)


EXAMPLE_5 = {
    "name": "홍길동", "sid": "10203",
    "base_circuit": "인코더 / 디코더",
    "title": "우선순위 인코더 기반 주차타워 최저 여유층 안내판",
    "problem": [
        "우리 학교 인근 3층 규모 공영 주차타워는 각 층 입구에서만 만차 여부를 확인할 수 있어,",
        "진입로 초입에 있는 운전자는 어느 층에 자리가 있는지 알 수 없다.",
        "여러 층에 동시에 자리가 있을 때는 가장 낮은 층부터 안내하여 운전자의 이동 거리를 줄인다.",
    ],
    "application": [
        "교과서는 8-to-3 우선순위 인코더의 진리표를 확인하는 수준에 그치지만,",
        "본 프로젝트는 인코더 출력에 BCD-7세그먼트 디코더(7447)를 추가로 연결해",
        "사람이 바로 읽을 수 있는 숫자로 표시되도록 인코더+디코더를 복합 설계했다.",
    ],
    "devices": [
        ("74148 우선순위 인코더", "1", "3개 층의 '자리 있음' 신호 중 최저 층 번호를 2진 코드로 변환"),
        ("7447 BCD-7세그먼트 디코더", "1", "인코더 출력을 7세그먼트 구동 신호로 변환"),
        ("7세그먼트 표시장치", "1", "최종 층 번호를 숫자로 출력"),
        ("입력 스위치", "3", "1·2·3층의 '자리 있음(HIGH)' 신호를 시뮬레이션"),
    ],
    "circuit_note": "입력 스위치 3개(1~3층) → 74148 우선순위 인코더 → 7447 디코더 → 7세그먼트. "
                    "동시에 여러 층이 HIGH여도 가장 낮은 층 번호가 출력되도록 인코더의 우선순위 특성을 활용함.",
    "operation": [
        "1) 각 층 스위치를 눌러 '자리 있음(HIGH)' 상태를 입력한다.",
        "2) 74148 인코더가 눌린 입력 중 최저 순위(가장 낮은 층)를 2진 코드로 출력한다.",
        "3) 7447 디코더가 이 코드를 7세그먼트 신호로 바꾸어 층 번호를 표시한다.",
        "4) 모든 층이 만차(입력 없음)이면 표시장치가 꺼지도록 Enable 입력을 연결했다.",
    ],
    "table_header": ["3층", "2층", "1층", "인코더 출력(2진)", "표시 숫자"],
    "table_rows": [
        ["0", "0", "0", "-", "표시 없음(만차)"],
        ["0", "0", "1", "00", "1"],
        ["0", "1", "0", "01", "2"],
        ["0", "1", "1", "00", "1"],
        ["1", "0", "0", "10", "3"],
        ["1", "1", "1", "00", "1"],
    ],
    "test_result": [
        "모든 입력 조합에서 표에 정리한 대로 최저 층 번호가 정상 출력됨을 확인했다.",
        "초기에는 모든 층이 0일 때도 '0층'이 표시되는 문제가 있었는데, 인코더의 Enable Output(EO) 신호로",
        "표시장치를 끄도록 회로를 수정해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '동시에 여러 층에 자리가 있을 때 가장 낮은 층을 표시하려면 어떤 소자를 쓰면 좋을지' 물어봤다.",
        "correction": "AI는 처음에 단순 디코더만 쓰라고 제안했는데, 디코더는 입력이 한 번에 하나만 있을 때만 정확히 "
                      "동작해 동시 입력 상황을 처리하지 못한다는 걸 시뮬레이션으로 확인하고 우선순위 인코더로 바꿨다.",
        "judgement": "AI가 제안한 7447 연결 방식은 그대로 썼지만, 모든 층이 만차일 때 표시를 끄는 부분은 AI 제안에 없어 "
                     "인코더의 Enable Output 신호를 직접 찾아 추가했다.",
    },
}

EXAMPLE_5_MUX = {
    "name": "박서준", "sid": "10215",
    "base_circuit": "멀티플렉서(MUX) / 디멀티플렉서(DEMUX)",
    "title": "MUX·DEMUX 기반 방송실 신호원-교실 선택 송출 시스템",
    "problem": [
        "학교 방송실에는 교장실 마이크, 방송부 마이크, 외부 입력 등 여러 신호원이 있지만,",
        "한 번에 하나의 신호만 원하는 교실에만 선택적으로 내보내고 싶다.",
        "신호원 선택과 수신 교실 선택을 각각 독립적으로 제어할 수 있는 장치를 설계한다.",
    ],
    "application": [
        "교과서는 MUX·DEMUX 각각의 개별 동작(진리표) 확인에 그치지만,",
        "본 프로젝트는 MUX로 여러 입력 중 하나를 고르고 DEMUX로 여러 출력 중 하나에만 전달하도록",
        "두 회로를 직렬로 연결해 '선택 송신-선택 수신'이 모두 가능한 시스템으로 응용했다.",
    ],
    "devices": [
        ("74151 8:1 멀티플렉서", "1", "3개 신호원(스위치) 중 선택된 신호 하나를 출력으로 전달"),
        ("74155 2:4 디멀티플렉서", "1", "MUX 출력 신호를 선택된 교실 LED 하나에만 전달"),
        ("입력 신호 스위치", "3", "교장실·방송부·외부 입력 신호를 시뮬레이션"),
        ("선택 스위치", "4", "입력 선택 2비트 + 출력(교실) 선택 2비트"),
        ("교실 표시 LED", "4", "선택된 교실에만 점등되어 신호 수신을 표시"),
    ],
    "circuit_note": "입력 스위치 3개 → 74151 MUX(선택 S1S0) → 74155 DEMUX(선택 D1D0) → 교실 LED 4개 중 1개. "
                    "MUX 선택과 DEMUX 선택을 별도 스위치로 분리해 '누가 방송하고 누가 듣는지'를 독립적으로 제어함.",
    "operation": [
        "1) 방송실 담당자가 입력 선택 스위치로 내보낼 신호원을 고른다.",
        "2) 74151 MUX가 선택된 신호원의 신호만 다음 단으로 전달한다.",
        "3) 출력 선택 스위치로 신호를 받을 교실을 지정한다.",
        "4) 74155 DEMUX가 지정된 교실 LED에만 신호를 전달해 점등시킨다.",
    ],
    "table_header": ["입력선택(S1S0)", "선택된 신호원", "출력선택(D1D0)", "점등 교실"],
    "table_rows": [
        ["00", "교장실 마이크", "00", "1반"],
        ["00", "교장실 마이크", "01", "2반"],
        ["01", "방송부 마이크", "10", "3반"],
        ["10", "외부 입력", "11", "4반"],
    ],
    "test_result": [
        "모든 입력·출력 선택 조합에서 지정한 교실 LED만 정상 점등됨을 확인했다.",
        "처음에는 선택하지 않은 교실에도 신호가 약하게 새는 문제가 있었는데,",
        "DEMUX의 미선택 출력이 실제로 LOW로 고정되도록 결선을 다시 확인해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '여러 신호원 중 하나를 골라 여러 목적지 중 하나로 보내려면 어떻게 설계해야 하는지' 물어봤다.",
        "correction": "AI는 MUX 출력을 바로 LED에 연결하라고 했는데, 그러면 모든 교실에 신호가 동시에 전달돼 원하는 "
                      "동작이 아니라는 걸 시뮬레이션으로 확인하고 DEMUX를 추가로 연결했다.",
        "judgement": "MUX 선택 스위치와 DEMUX 선택 스위치를 분리한 것은 AI 제안이 아니라, '누가 방송하고 누가 듣는지'를 "
                     "따로 정하고 싶어서 스스로 추가한 설계다.",
    },
}

EXAMPLE_5_COMP = {
    "name": "이수민", "sid": "10422",
    "base_circuit": "비교기",
    "title": "비교기를 활용한 계주 기록 비교 승리팀 표시기",
    "problem": [
        "체육대회 이어달리기에서 두 팀의 기록을 초 단위로 측정한 뒤 수기로 비교해 승리팀을 발표하다 보니 시간이 걸린다.",
        "두 팀의 기록(2자리 숫자)을 스위치로 입력하면 자동으로 더 빠른(작은 값) 팀의 LED가 켜지도록 한다.",
    ],
    "application": [
        "교과서는 두 4비트 값의 대소 비교 진리표 확인에 그치지만,",
        "본 프로젝트는 비교 결과(A>B, A<B, A=B) 각각에 서로 다른 LED와 문구를 연결해",
        "실제 대회에서 바로 승패를 알려주는 표시 장치로 응용했다.",
    ],
    "devices": [
        ("7485 4비트 크기 비교기", "1", "A팀·B팀 기록(4비트씩)의 대소를 비교"),
        ("BCD 입력 스위치", "8", "A팀 기록 4비트 + B팀 기록 4비트 입력"),
        ("승리 LED", "2", "A팀 승리(A<B, 기록이 작음) / B팀 승리(A>B) 표시"),
        ("동점 LED", "1", "두 팀 기록이 같을 때(A=B) 점등"),
    ],
    "circuit_note": "A팀 기록 스위치 4비트, B팀 기록 스위치 4비트 → 7485 비교기 → A<B, A>B, A=B 세 출력을 각각 LED에 연결. "
                    "기록(초)이 작을수록 빠른 팀이므로 A<B 출력에 'A팀 승리' LED를 연결함.",
    "operation": [
        "1) 심판이 A팀과 B팀의 기록을 각각 스위치로 입력한다.",
        "2) 7485 비교기가 두 값을 비교해 A<B, A>B, A=B 중 하나만 HIGH로 출력한다.",
        "3) A<B가 HIGH면 'A팀 승리' LED가, A>B가 HIGH면 'B팀 승리' LED가 켜진다.",
        "4) 두 기록이 같으면 '동점' LED가 켜진다.",
    ],
    "table_header": ["A팀 기록", "B팀 기록", "결과", "점등 LED"],
    "table_rows": [
        ["12", "15", "A<B", "A팀 승리"],
        ["15", "12", "A>B", "B팀 승리"],
        ["10", "10", "A=B", "동점"],
        ["9", "14", "A<B", "A팀 승리"],
    ],
    "test_result": [
        "여러 기록 조합에서 항상 더 작은 값(빠른 기록)을 낸 팀의 LED가 정확히 켜짐을 확인했다.",
        "두 자리 수 비교 시 자리올림 처리가 꼬여 오작동한 적이 있었는데,",
        "7485의 하위 자리 비교기 캐스케이드 입력을 정확히 연결해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '두 값 중 어느 게 더 작은지 비교해서 LED를 켜는 회로'를 물어봤다.",
        "correction": "AI가 예시로 준 회로는 4비트 단일 비교였는데, 우리 팀 기록은 두 자리 수라 7485를 두 개 이어(캐스케이드) "
                      "연결해야 한다는 걸 직접 확인해 회로를 고쳤다.",
        "judgement": "동점(A=B) LED를 추가한 것은 AI 제안에 없던 부분으로, 실제 계주에서 동시 도착도 있을 수 있다고 "
                     "생각해 스스로 추가했다.",
    },
}

EXAMPLE_5_CODE = {
    "name": "정하늘", "sid": "10508",
    "base_circuit": "코드 변환기 (BCD-3초과, 2진수-그레이 코드)",
    "title": "그레이 코드-2진수 변환기를 이용한 회전 다이얼 표시기",
    "problem": [
        "동아리에서 사용하는 회전 센서(로터리 인코더)는 회전 위치를 그레이 코드로 출력하는데,",
        "그레이 코드는 사람이 바로 읽기 어려워 전시 부스에서 관람객이 값을 이해하기 힘들다.",
        "그레이 코드 신호를 2진수로 변환해 숫자로 바로 표시되는 장치를 설계한다.",
    ],
    "application": [
        "교과서는 그레이-2진 변환의 진리표 확인 수준에 그치지만,",
        "본 프로젝트는 변환된 2진수를 7447 디코더와 7세그먼트에 연결해",
        "회전 다이얼의 위치를 사람이 읽을 수 있는 숫자로 실시간 표시되도록 응용했다.",
    ],
    "devices": [
        ("그레이 코드 입력 스위치", "4", "회전 센서의 그레이 코드 출력을 시뮬레이션"),
        ("XOR 게이트", "3", "그레이 코드를 2진수로 변환하는 조합 회로 구성"),
        ("7447 BCD-7세그먼트 디코더", "1", "변환된 2진수를 세그먼트 신호로 변환"),
        ("7세그먼트 표시장치", "1", "다이얼 위치를 숫자로 표시"),
    ],
    "circuit_note": "그레이코드 스위치 4비트(G3G2G1G0) → XOR 체인(B3=G3, B2=B3⊕G2, B1=B2⊕G1, B0=B1⊕G0)으로 "
                    "2진수 변환 → 7447 디코더 → 7세그먼트.",
    "operation": [
        "1) 회전 다이얼(스위치)로 그레이 코드 값을 입력한다.",
        "2) XOR 게이트 체인이 최상위 비트부터 순서대로 그레이 코드를 2진수로 변환한다.",
        "3) 변환된 2진수를 7447 디코더가 세그먼트 신호로 바꾼다.",
        "4) 7세그먼트 표시장치에 다이얼 위치가 숫자로 나타난다.",
    ],
    "table_header": ["그레이코드 입력", "변환된 2진수", "표시 숫자"],
    "table_rows": [
        ["0000", "0000", "0"],
        ["0001", "0001", "1"],
        ["0011", "0010", "2"],
        ["0010", "0011", "3"],
        ["0110", "0100", "4"],
    ],
    "test_result": [
        "표에 정리한 모든 입력에서 올바른 숫자가 표시됨을 확인했다.",
        "처음에는 XOR 체인의 연결 순서를 반대로 해 엉뚱한 숫자가 나왔는데,",
        "최상위 비트부터 순서대로 누적 XOR하도록 배선을 수정해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '그레이 코드를 2진수로 바꾸는 회로를 어떻게 만드는지' 물어봤다.",
        "correction": "AI가 알려준 XOR 연결 순서를 그대로 따라 했더니 엉뚱한 숫자가 나와서, 최상위 비트부터 누적으로 "
                      "XOR해야 한다는 원리를 교과서에서 다시 확인하고 배선을 고쳤다.",
        "judgement": "AI 답변은 회로도만 주고 원리 설명은 없어서, 왜 이렇게 연결해야 하는지는 교과서 내용을 직접 찾아 "
                     "이해한 뒤 발표에 포함했다.",
    },
}

EXAMPLE_7_REG = {
    "name": "김철수", "sid": "10315",
    "base_circuit": "레지스터 (시프트·순환·직병렬)",
    "title": "직병렬 레지스터를 이용한 교실 출입센서 신호 직렬 전송 시스템",
    "problem": [
        "교실 4개의 출입 센서 신호를 각각 관리실까지 배선하면 전선이 4개나 필요해 설치가 번거롭다.",
        "병렬 신호를 직렬로 압축해 한 가닥으로 전송하고, 관리실에서 다시 병렬로 복원해",
        "교실별 상태를 표시하는 시스템을 설계한다.",
    ],
    "application": [
        "교과서는 시프트 레지스터의 단순 이동 동작(오른쪽/왼쪽 시프트) 확인에 그치지만,",
        "본 프로젝트는 병렬 입력-직렬 출력(PISO) 레지스터로 송신하고 직렬 입력-병렬 출력(SIPO)",
        "레지스터로 수신하는 구조를 결합해 실제 직렬 통신처럼 응용했다.",
    ],
    "devices": [
        ("7474 D 플립플롭 (송신용)", "4", "교실 4개 신호를 병렬로 저장 후 1비트씩 직렬 출력(PISO)"),
        ("74157 멀티플렉서", "4", "Load(병렬 입력)와 Shift(이전 단 출력) 중 하나를 D 플립플롭 입력으로 선택"),
        ("7474 D 플립플롭 (수신용)", "4", "직렬로 들어오는 비트를 순서대로 저장해 병렬 출력(SIPO)"),
        ("입력 스위치", "4", "교실 1~4의 출입 센서 상태(1=사용 중)를 시뮬레이션"),
        ("표시 LED", "4", "관리실에서 복원된 교실별 상태를 표시"),
    ],
    "circuit_note": "D 플립플롭 4개 + 74157 MUX 4개로 병렬 입력-직렬 출력(PISO) 레지스터를 구성해 송신측으로, "
                    "D 플립플롭 4개만으로 직렬 입력-병렬 출력(SIPO) 레지스터를 구성해 수신측으로 사용. "
                    "송수신 D 플립플롭에 같은 클럭을 공유해 비트가 밀리지 않도록 동기화함.",
    "operation": [
        "1) Load 신호로 교실 4개의 센서 상태(예: 1101)를 송신측 레지스터에 병렬로 저장한다.",
        "2) Shift 모드로 전환하고 클럭을 가할 때마다 최상위 비트부터 1비트씩 직렬로 출력한다.",
        "3) 수신측 레지스터가 같은 클럭에 맞춰 비트를 순서대로 밀어 넣는다.",
        "4) 4클럭 후 수신측에 4비트가 모두 채워지면 관리실 LED 4개에 교실별 상태가 표시된다.",
    ],
    "table_header": ["클럭", "송신측 동작", "수신측 값", "비고"],
    "table_rows": [
        ["Load", "병렬 로드 1101 (1반=1,2반=1,3반=0,4반=1)", "0000", "전송 준비"],
        ["1클럭", "1 직렬 출력", "0001", "1비트 수신"],
        ["2클럭", "1 직렬 출력", "0011", "2비트 수신"],
        ["3클럭", "0 직렬 출력", "0110", "3비트 수신"],
        ["4클럭", "1 직렬 출력", "1101", "4비트 수신 완료 → LED 표시"],
    ],
    "test_result": [
        "4클럭 후 송신측 원래 값(1101)과 수신측 값이 정확히 일치함을 확인했다.",
        "처음에는 송수신 클럭이 어긋나 비트가 한 칸씩 밀리는 문제가 있었는데,",
        "두 레지스터가 같은 클럭 신호를 공유하도록 배선을 수정해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '여러 센서 신호를 전선 하나로 보내는 방법'을 물어봤다.",
        "correction": "AI는 74165/74164 같은 기성 IC를 쓰라고 했는데, 교과서에서 배운 대로 D 플립플롭과 MUX로 "
                      "직접 구성해야 한다는 걸 알고 있어서 IC 대신 플립플롭 조합으로 다시 설계했다.",
        "judgement": "송수신 클럭을 공유하지 않으면 비트가 밀린다는 것은 AI가 알려주지 않아서, 직접 시뮬레이션하다 "
                     "발견하고 스스로 고쳤다.",
    },
}

EXAMPLE_7_ASYNC = {
    "name": "박도윤", "sid": "10327",
    "base_circuit": "비동기식 카운터",
    "title": "비동기식 3비트 상향 카운터를 이용한 실험 기구 대여 누적 횟수 표시기",
    "problem": [
        "과학실 현미경 대여 시 누적 대여 횟수를 수기로 기록하다 보니 빠뜨리는 경우가 많다.",
        "대여 버튼을 누를 때마다 자동으로 1씩 증가해 누적 횟수를 표시하는 장치를 설계한다",
        "(최대 7회까지 세고 다시 0부터 반복).",
    ],
    "application": [
        "교과서는 3비트 상향 카운터의 동작(0→1→…→7→0) 확인에 그치지만,",
        "본 프로젝트는 이를 실험 기구 대여 횟수 누적 표시기로 연결하고,",
        "리플(비동기) 전파로 인한 지연이 실제로 어떻게 나타나는지 관찰 결과까지 보고서에 포함했다.",
    ],
    "devices": [
        ("7476 JK 플립플롭", "3", "J=K=1(토글 모드) 고정, 리플 연결로 3비트 비동기 상향 카운터 구성"),
        ("대여 버튼", "1", "최하위 플립플롭 Fa의 클럭 신호로 직접 연결"),
        ("표시 LED", "3", "카운트 값(2진, Q_C Q_B Q_A)을 표시"),
        ("리셋 스위치", "1", "000으로 초기화"),
    ],
    "circuit_note": "대여 버튼(클럭)을 누를 때마다 Fa가 반전되고, Fa의 출력 Q_A가 다음 플립플롭 Fb의 클럭으로, "
                    "Fb의 출력 Q_B가 Fc의 클럭으로 순차 연결되는 리플(비동기) 구조로 3비트 카운터를 구성함.",
    "operation": [
        "1) 기구를 대여할 때마다 대여 버튼(클럭)을 누른다.",
        "2) 버튼이 눌릴 때마다 Fa가 먼저 반전되고, 그 출력이 순차적으로 다음 플립플롭에 전파되어 값이 1 증가한다.",
        "3) 7(111)까지 센 뒤 다시 누르면 0(000)으로 돌아가 반복된다.",
        "4) LED 3개로 현재 누적 대여 횟수(2진수)를 표시한다.",
    ],
    "table_header": ["버튼 횟수", "Q_C Q_B Q_A", "10진값"],
    "table_rows": [
        ["0", "000", "0"],
        ["1", "001", "1"],
        ["2", "010", "2"],
        ["7", "111", "7"],
        ["8", "000", "0 (순환)"],
    ],
    "test_result": [
        "8번째 버튼 입력에서 정확히 000으로 순환됨을 확인했다.",
        "값이 바뀌는 순간 LED가 잠깐 깜빡이는 현상이 있었는데,",
        "이는 리플 전파로 지연이 단마다 누적되는 비동기식 카운터의 특성임을 확인하고 발표에서 동기식과 비교 설명했다.",
    ],
    "ai": {
        "question": "AI에게 '누르는 횟수를 세는 가장 간단한 카운터'를 물어봤다.",
        "correction": "AI는 74192 같은 IC를 추천했는데, 교과서 범위(JK 플립플롭 리플 연결)에 맞지 않는다는 걸 알고 있어 "
                      "직접 JK 플립플롭 3개로 다시 구성했다.",
        "judgement": "리플 전파 때문에 LED가 잠깐 깜빡이는 현상은 AI 설명에 없어서, 직접 관찰하고 그 이유(지연 누적)를 "
                     "교과서 내용과 연결해 스스로 설명을 완성했다.",
    },
}

EXAMPLE_7_SYNC = {
    "name": "최유진", "sid": "10336",
    "base_circuit": "동기식 카운터",
    "title": "동기식 3비트 카운터를 이용한 실험/발표 겸용 카운트업·다운 타이머",
    "problem": [
        "과학실에서 실험 경과 시간을 잴 때는 카운트업이, 발표 준비 남은 시간을 볼 때는 카운트다운이 필요하다.",
        "모드 선택 스위치 하나로 카운트업과 카운트다운을 전환할 수 있는 동기식 타이머를 설계한다.",
    ],
    "application": [
        "교과서는 동기식 카운터의 상향/하향 진리표 확인에 그치지만,",
        "본 프로젝트는 실험 중(카운트업)과 발표 준비 중(카운트다운) 두 상황에 맞춰",
        "모드를 전환해 쓰는 실제 타이머 장치로 응용했다.",
    ],
    "devices": [
        ("7476 JK 플립플롭", "3", "J=K=1(토글) 고정, 같은 클럭을 동시에 인가해 동기식 3비트 카운터 구성"),
        ("모드 선택 스위치(X)", "1", "X=0이면 카운트업, X=1이면 카운트다운으로 동작"),
        ("클럭 발생기", "1", "모든 플립플롭에 공통으로 인가되는 클럭 신호"),
        ("표시 LED", "3", "카운트 값(2진, Q_C Q_B Q_A) 표시"),
    ],
    "circuit_note": "3개의 JK 플립플롭에 동일한 클럭을 동시에 인가하고, 모드 선택 스위치 X 값에 따라 상위 플립플롭의 "
                    "클럭 입력을 이전 단의 Q(X=0, 상향) 또는 Q̅(X=1, 하향) 중 하나로 조합 논리를 거쳐 연결해 "
                    "동기식으로 동작하도록 구성함.",
    "operation": [
        "1) 모드 선택 스위치 X를 0(카운트업) 또는 1(카운트다운)으로 설정한다.",
        "2) 클럭이 들어올 때마다 3개의 JK 플립플롭이 동시에 반응해 지연 없이 값이 바뀐다.",
        "3) X=0이면 000→001→010→…→111→000 순서로 증가한다.",
        "4) X=1이면 111→110→…→000→111 순서로 감소한다.",
    ],
    "table_header": ["모드(X)", "클럭 순서", "Q_C Q_B Q_A"],
    "table_rows": [
        ["0(상향)", "시작", "000"],
        ["0(상향)", "1클럭", "001"],
        ["0(상향)", "2클럭", "010"],
        ["1(하향)", "시작", "111"],
        ["1(하향)", "1클럭", "110"],
    ],
    "test_result": [
        "X=0/1을 전환할 때마다 예상한 상향·하향 순서대로 정확히 카운트됨을 확인했다.",
        "X를 바꿔도 다음 클럭 전까지는 값이 그대로였는데,",
        "동기식 카운터는 클럭 에지에서만 값이 바뀌는 정상 동작임을 확인하고 발표 내용에 포함했다.",
    ],
    "ai": {
        "question": "AI에게 '상향과 하향을 스위치 하나로 바꿀 수 있는 카운터'를 물어봤다.",
        "correction": "AI가 준 회로는 플립플롭마다 다른 클럭을 쓰는 비동기식 구조였는데, 교과서의 동기식 정의(모든 "
                      "플립플롭이 같은 클럭)와 다르다는 걸 확인하고 공통 클럭 구조로 고쳤다.",
        "judgement": "X 스위치를 바꿔도 다음 클럭까지 값이 그대로인 것은 오작동이 아니라 동기식의 정상 동작이라는 걸 "
                     "직접 검증해 발표에 포함했다.",
    },
}

EXAMPLE_7_RING = {
    "name": "한서연", "sid": "10344",
    "base_circuit": "링 카운터",
    "title": "동기식 5진 링 카운터를 이용한 학예회 팀 순서 표시등",
    "problem": [
        "학예회에서 5개 팀이 순서대로 공연하는데 현재 몇 번째 팀 차례인지 안내가 없어 혼선이 생긴다.",
        "버튼을 누를 때마다 다음 팀의 표시등만 켜지고, 5번째 다음엔 다시 1번 팀으로 돌아오는",
        "순서 표시기를 설계한다.",
    ],
    "application": [
        "교과서는 5진 링 카운터가 1비트를 순서대로 돌리는 동작 확인에 그치지만,",
        "본 프로젝트는 이 순환 동작을 학예회 팀 순서 표시로 연결해 실제 행사 진행 도구로 응용했다.",
    ],
    "devices": [
        ("7474 D 플립플롭", "5", "Q_A→D_B→…→Q_E→D_A 순으로 고리 모양 연결, 공통 클럭으로 동시 동작"),
        ("'다음 순서' 버튼", "1", "5개 D 플립플롭에 공통으로 인가되는 클럭 신호"),
        ("초기화 스위치", "1", "Q_A만 1, 나머지는 0으로 강제 설정"),
        ("표시 LED", "5", "현재 차례인 팀(1~5팀) 하나만 점등"),
    ],
    "circuit_note": "D 플립플롭 5개를 Q_A→D_B, Q_B→D_C, Q_C→D_D, Q_D→D_E, Q_E→D_A 순서로 고리 모양으로 연결하고, "
                    "초기화 시 Q_A만 1, 나머지는 0으로 설정. '다음 순서' 버튼(클럭)을 누를 때마다 1이 옆자리로 이동함.",
    "operation": [
        "1) 초기화 스위치로 Q_A=1, 나머지는 0으로 만들어 1팀 LED를 켠다.",
        "2) '다음 순서' 버튼(클럭)을 누르면 1이 Q_B로 이동해 2팀 LED가 켜진다.",
        "3) 버튼을 누를 때마다 순서대로 3팀→4팀→5팀 LED로 이동한다.",
        "4) 5팀 다음에 버튼을 누르면 다시 1팀(Q_A)으로 돌아온다.",
    ],
    "table_header": ["클럭 순서", "점등 LED(팀)", "Q_A Q_B Q_C Q_D Q_E"],
    "table_rows": [
        ["초기화", "1팀", "10000"],
        ["1클럭", "2팀", "01000"],
        ["2클럭", "3팀", "00100"],
        ["3클럭", "4팀", "00010"],
        ["4클럭", "5팀", "00001"],
        ["5클럭", "1팀(복귀)", "10000"],
    ],
    "test_result": [
        "5클럭마다 정확히 처음 위치(1팀)로 돌아오는 것을 확인했다.",
        "전원을 켰을 때 여러 플립플롭이 동시에 1로 시작해 불빛이 2개 켜지는 문제가 있었는데,",
        "초기화 스위치로 Q_A만 1로 강제 설정하는 회로를 추가해 해결했다.",
    ],
    "ai": {
        "question": "AI에게 '불빛이 하나씩 순서대로 도는 회로'를 물어봤다.",
        "correction": "AI 예시는 초기화 회로 없이 바로 정상 동작을 가정했는데, 실제로 전원을 켜면 여러 플립플롭이 "
                      "동시에 1로 시작해 불빛이 2개 켜지는 문제가 생겼다. AI가 알려주지 않은 부분이라 직접 원인을 "
                      "찾아 초기화 스위치를 추가했다.",
        "judgement": "왜 5클럭마다 정확히 처음으로 돌아오는지는 교과서의 D 플립플롭 순환 원리로 직접 설명을 완성했다.",
    },
}


PROBLEM_EXCERPTS = {
    5: [
        ("인코더/디코더", " ".join(EXAMPLE_5["problem"])),
        ("MUX/DEMUX", " ".join(EXAMPLE_5_MUX["problem"])),
        ("비교기", " ".join(EXAMPLE_5_COMP["problem"])),
        ("코드 변환기", " ".join(EXAMPLE_5_CODE["problem"])),
    ],
    7: [
        ("레지스터", " ".join(EXAMPLE_7_REG["problem"])),
        ("비동기식 카운터", " ".join(EXAMPLE_7_ASYNC["problem"])),
        ("동기식 카운터", " ".join(EXAMPLE_7_SYNC["problem"])),
        ("링 카운터", " ".join(EXAMPLE_7_RING["problem"])),
    ],
}


def _load_diagram(ex, png_path):
    from PIL import Image
    with open(png_path, "rb") as f:
        img_bytes = f.read()
    w_px, h_px = Image.open(png_path).size
    cx = 5730000  # ~6.26in, matches the 9026-twip content box width
    cy = int(cx * h_px / w_px)
    ex["diagram_emu"] = (cx, cy)
    return img_bytes


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(here)  # 수행평가/디논_5-7단원_창의융합프로젝트/
    teacher_dir = f"{base}/교사용_비공개"
    diag_dir = f"{here}/diagrams"
    os.makedirs(base, exist_ok=True)
    os.makedirs(teacher_dir, exist_ok=True)
    write_docx(f"{base}/학생용_보고서_양식_5단원.docx", build_body(5, is_example=False))
    write_docx(f"{base}/학생용_보고서_양식_7단원.docx", build_body(7, is_example=False))

    jobs = [
        ("예시_보고서_5단원_인코더디코더.docx", 5, EXAMPLE_5, "5_encoder.png"),
        ("예시_보고서_5단원_멀티플렉서디멀티플렉서.docx", 5, EXAMPLE_5_MUX, "5_mux.png"),
        ("예시_보고서_5단원_비교기.docx", 5, EXAMPLE_5_COMP, "5_comparator.png"),
        ("예시_보고서_5단원_코드변환기.docx", 5, EXAMPLE_5_CODE, "5_code_converter.png"),
        ("예시_보고서_7단원_레지스터.docx", 7, EXAMPLE_7_REG, "7_register.png"),
        ("예시_보고서_7단원_비동기카운터.docx", 7, EXAMPLE_7_ASYNC, "7_async_counter.png"),
        ("예시_보고서_7단원_동기카운터.docx", 7, EXAMPLE_7_SYNC, "7_sync_counter.png"),
        ("예시_보고서_7단원_링카운터.docx", 7, EXAMPLE_7_RING, "7_ring_counter.png"),
    ]
    for fname, unit, ex, png in jobs:
        img_bytes = _load_diagram(ex, f"{diag_dir}/{png}")
        write_docx(f"{teacher_dir}/{fname}", build_body(unit, is_example=True, ex=ex), image_bytes=img_bytes)
