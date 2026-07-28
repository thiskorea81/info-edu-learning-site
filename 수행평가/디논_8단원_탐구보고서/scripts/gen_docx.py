# -*- coding: utf-8 -*-
"""Build the unit-8 student report form + teacher-only rubric (stdlib-only docx).

디논 5·7단원 창의융합프로젝트(../디논_5-7단원_창의융합프로젝트/scripts/gen_docx2.py)와
동일한 문서 스타일(글꼴/표 테두리/체크박스 등)을 재사용해, 8단원 탐구보고서 양식과
루브릭을 "학생 배부용"과 "교사 전용"으로 분리한 두 개의 docx로 생성한다.

실행 방법 (이 폴더 기준):
    python3 gen_docx.py

산출물:
    수행평가/디논_8단원_탐구보고서/학생용_보고서_양식_8단원.docx
    수행평가/디논_8단원_탐구보고서/교사용_비공개/교사용_채점기준표_8단원.docx
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
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS_ROOT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

RELS_DOC = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def write_docx(out_path, body):
    document_xml = DOCUMENT_XML_TEMPLATE.format(body=body)
    import xml.dom.minidom as minidom
    minidom.parseString(document_xml.encode("utf-8"))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS_ROOT)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/styles.xml", STYLES_XML)
        z.writestr("word/_rels/document.xml.rels", RELS_DOC)
    print("written:", out_path)


TOPICS = ["메모리 소자", "마이크로프로세서", "임베디드 시스템"]


def info_table():
    w1, w2, w3, w4 = 1400, 3113, 1400, 3113
    full = w1 + w2 + w3 + w4
    topic_boxes = "".join(checkbox(name) for name in TOPICS)
    return table([
        row([cell("학번", w1, bold=True, shade="EEEEEE"), cell("", w2),
             cell("이름", w3, bold=True, shade="EEEEEE"), cell("", w4)]),
        row([cell("탐구주제", w1, bold=True, shade="EEEEEE"), cell(topic_boxes, full - w1)]),
    ], [w1, w2, w3, w4])


def diagram_box():
    return table([row([cell("".join(para("", space_after=280) for _ in range(6)), 9026)])], [9026])


def build_student_body():
    parts = []
    parts.append(heading("디지털논리회로 8단원 탐구보고서 수행평가", 1))
    parts.append(para("메모리 소자 · 마이크로프로세서 · 임베디드 시스템 중 택 1", align="center", space_after=120))
    parts.append(para("※ 안내: 메모리 소자·마이크로프로세서·임베디드 시스템 중 하나의 주제를 선택하여 탐구합니다. "
                       "단순한 개념 나열을 지양하고, 실제 디지털 기기나 산업 현장에서 해당 기술이 어떻게 적용되고 "
                       "동작하는지 심층적으로 분석하여 작성합니다. 필요 시 구조도, 회로도, 표 등 시각 자료를 적극 "
                       "활용하세요.", italic=True, space_after=160))

    parts.append(info_table())

    parts.append(heading("1. 탐구 동기 및 목적 (서론)", 2))
    parts.append(para("가. 주제 선정 동기", bold=True, space_after=80))
    parts.append(para("(평소 사용하는 기기, 기술 트렌드 등과 연계하여 본 주제를 선택한 구체적 이유 서술)",
                       italic=True, space_after=60))
    parts.append(blank_lines(3))
    parts.append(para("나. 탐구 목적", bold=True, space_after=80, space_before=160))
    parts.append(para("(본 보고서를 통해 구체적으로 무엇을 탐구하고 분석하고자 하는지 명확히 제시)",
                       italic=True, space_after=60))
    parts.append(blank_lines(2))

    parts.append(heading("2. 핵심 이론 및 구조 분석 (본론 1)", 2))
    parts.append(para("가. 핵심 개념 정의", bold=True, space_after=80))
    parts.append(para("(선택한 주제의 핵심 소자 및 시스템에 대한 정의와 주요 특성 서술)",
                       italic=True, space_after=60))
    parts.append(blank_lines(2))
    parts.append(para("나. 동작 원리 및 내부 구조", bold=True, space_after=80, space_before=160))
    parts.append(para("(ROM/RAM 셀 구조, 명령어 처리 사이클, 하드웨어-소프트웨어 상호작용 등 체계적 설명)",
                       italic=True, space_after=60))
    parts.append(blank_lines(3))
    parts.append(para("※ 필요 시 직접 그린 블록도, 회로도, 다이어그램 등 시각 자료를 아래 상자에 붙여넣거나 그리세요.",
                       space_after=80, space_before=80))
    parts.append(diagram_box())

    parts.append(heading("3. 실생활 및 산업 응용 사례 심층 탐구 (본론 2)", 2))
    parts.append(para("가. 적용 사례 선정 및 구체적 분석", bold=True, space_after=80))
    parts.append(para("(해당 기술이 적용된 구체적 기기 및 시스템 1~2개 선정)", italic=True, space_after=60))
    parts.append(blank_lines(2))
    parts.append(para("나. 시스템 내에서의 역할 및 제어 흐름", bold=True, space_after=80, space_before=160))
    parts.append(para("(선정된 기기 내에서 입력-처리-출력 과정의 신호/데이터 흐름 분석)",
                       italic=True, space_after=60))
    parts.append(blank_lines(2))
    parts.append(para("다. 기술적 특징 비교 분석", bold=True, space_after=80, space_before=160))
    parts.append(para("(대체 기술 또는 하위/상위 기술과의 비교 — 예: SRAM vs DRAM, CPU vs GPU/NPU 등)",
                       italic=True, space_after=60))
    parts.append(blank_lines(2))

    parts.append(heading("4. 결론 및 통찰 (결론)", 2))
    parts.append(para("가. 탐구 내용 종합 요약", bold=True, space_after=80))
    parts.append(blank_lines(2))
    parts.append(para("나. 기술 발전 방향 및 나의 제언", bold=True, space_after=80, space_before=160))
    parts.append(para("(향후 해당 기술의 발전 전망 및 본인의 공학적 통찰 서술)", italic=True, space_after=60))
    parts.append(blank_lines(2))
    parts.append(para("다. 탐구를 통해 느끼고 알게 된 점", bold=True, space_after=80, space_before=160))
    parts.append(blank_lines(2))

    parts.append(heading("5. 참고 문헌 및 출처", 2))
    parts.append(para("(탐구에 활용한 도서, 학술지, 기술 문서, 웹사이트 등 정확한 출처 기재)",
                       italic=True, space_after=80))
    for _ in range(4):
        parts.append(bullet(""))

    parts.append(heading("6. 평가 기준 (자기 점검용 — 최종 점수는 교사가 확정)", 2))
    parts.append(para("본 보고서는 아래 기준표에 따라 채점됩니다. 제출 전 각 항목을 스스로 점검해보세요.",
                       italic=True, space_after=160))
    parts.append(para("가. 평가 영역별 배점 (지식 및 이해 7점 · 탐구 및 적용 7점 · 논리 및 완성도 6점, 총 20점)",
                       bold=True, space_after=80))
    parts.append(summary_table())
    parts.append(para("나. 세부 평가 기준표 (상/중/하)", bold=True, space_after=80, space_before=160))
    parts.append(detail_table())
    parts.append(para("다. 최종 점수 (교사 작성란)", bold=True, space_after=80, space_before=160))
    parts.append(final_score_table())
    parts.append(para("※ 위 체크리스트는 학생 자기 점검용이며, 최종 점수는 교사가 확정합니다.",
                       space_before=120, space_after=0))

    return "".join(parts)


RUBRIC_SUMMARY = [
    ("지식 및 이해", "7점 (35%)",
     "1. 핵심 개념 정의 (2점)\n2. 동작 원리 및 구조 설명 (3점)\n3. 전문 용어의 적절한 사용 (2점)"),
    ("탐구 및 적용", "7점 (35%)",
     "4. 실생활/산업 응용 사례 분석 (3점)\n5. 기술적 특징 비교 분석 (2점)\n6. 시스템 내에서의 역할 이해 (2점)"),
    ("논리 및 완성도", "6점 (30%)",
     "7. 보고서의 체계적 구조 (2점)\n8. 신뢰성 있는 정보 수집/활용 (2점)\n9. 자체적 통찰 및 발전적 결론 도출 (2점)"),
]

RUBRIC_DETAIL = [
    ("지식 및 이해\n(7점)", "1", "핵심 개념의\n명확한 정의 (2점)",
     "[2.0점] 선택한 주제의 핵심 개념과 특징을 정확하게 이해하고 오류 없이 명확히 서술함.",
     "[1.5점] 핵심 개념을 전반적으로 이해하나, 일부 설명이 부족하거나 아주 미미한 오류가 있음.",
     "[1.0점] 핵심 개념에 대한 이해가 부족하며, 설명이 모호하거나 중요한 오류가 포함됨."),
    ("지식 및 이해\n(7점)", "2", "동작 원리 및\n구조 설명 (3점)",
     "[3.0점] 소자 및 시스템의 내부 구조와 논리적 동작 원리(처리 과정)를 구체적이고 체계적으로 설명함.",
     "[2.0점] 내부 구조와 동작 원리를 설명하였으나, 세부 동작 단계가 일부 누락되는 등 구체성이 다소 떨어짐.",
     "[1.0점] 내부 구조 및 동작 원리에 대한 설명이 매우 피상적이거나 핵심적인 처리 원리를 누락함."),
    ("지식 및 이해\n(7점)", "3", "전문 용어의\n적절한 사용 (2점)",
     "[2.0점] 보고서 전반에 걸쳐 디지털 논리 회로 관련 전문 용어를 문맥에 맞게 정확하게 사용함.",
     "[1.5점] 전문 용어를 사용하였으나, 일부 부자연스럽거나 의미 전달이 다소 모호한 부분이 있음.",
     "[1.0점] 전문 용어 사용이 거의 없거나, 용어를 잘못된 의미로 혼용하여 설명함."),
    ("탐구 및 적용\n(7점)", "4", "실생활/산업\n응용 사례 분석 (3점)",
     "[3.0점] 실제 기기나 산업 현장의 적용 사례를 선정하여 내부 동작 구조와 연결해 매우 구체적으로 탐구함.",
     "[2.0점] 적용 사례를 제시하였으나, 이론적 설명과 실제 기기 작동 방식 간의 연결 분석이 다소 부족함.",
     "[1.0점] 단순 기기명이나 사례를 나열하는 데 그쳤으며, 기술적 적용에 대한 구체적인 분석이 없음."),
    ("탐구 및 적용\n(7점)", "5", "기술적 특징\n비교 분석 (2점)",
     "[2.0점] 관련 기술 간의 분류(ROM/RAM, CPU/GPU 등)를 타당한 기준에 따라 심도 있게 비교 분석함.",
     "[1.5점] 관련 기술의 비교를 시도하였으나, 기준이 다소 모호하거나 일반적인 차이점 서술에 그침.",
     "[1.0점] 기술 간의 특징 비교 분석이 없거나, 사실과 다른 잘못된 비교 기준을 제시함."),
    ("탐구 및 적용\n(7점)", "6", "시스템 내에서의\n역할 이해 (2점)",
     "[2.0점] 선택 요소가 전체 시스템에서 타 장치와 어떻게 상호작용하는지 제어 흐름을 명확히 파악함.",
     "[1.5점] 시스템 내에서의 역할을 서술하였으나, 타 구성 요소와의 상호작용 메커니즘 설명이 다소 부족함.",
     "[1.0점] 해당 요소의 단일 기능만 서술하고, 전체 디지털 시스템 내에서의 유기적 상호작용을 파악하지 못함."),
    ("논리 및 완성도\n(6점)", "7", "보고서의\n체계적 구조 (2점)",
     "[2.0점] 서론-본론-결론의 구성 체계를 완벽히 갖추고, 문장 및 단락 간의 논리적 흐름이 매우 매끄러움.",
     "[1.5점] 기본 구조는 갖추었으나, 단락 간의 연결이 다소 어색하거나 논리의 비약이 일부 발생함.",
     "[1.0점] 보고서의 구성 체계가 미흡하며, 내용이 중구난방으로 서술되어 논리적 흐름을 파악하기 힘듦."),
    ("논리 및 완성도\n(6점)", "8", "신뢰성 있는\n정보 수집/활용 (2점)",
     "[2.0점] 전문 매체(서적, 논문, 기술 문서 등)를 적극 활용하고, 출처를 명확히 밝혀 객관적 근거로 제시함.",
     "[1.5점] 정보를 수집하여 활용하였으나 참고 문헌 출처 표기가 미흡하거나 한정된 자료만 활용함.",
     "[1.0점] 외부 자료 수집의 흔적이 거의 없거나, 출처가 불분명하고 신뢰하기 어려운 정보를 활용함."),
    ("논리 및 완성도\n(6점)", "9", "자체적 통찰 및\n발전적 결론 도출 (2점)",
     "[2.0점] 단순 조사를 넘어 기술의 향후 발전 방향을 조망하고, 본인만의 독창적 통찰이 담긴 결론을 도출함.",
     "[1.5점] 조사한 내용을 본인의 언어로 잘 요약하였으나, 심도 있는 제언이나 독창적 통찰은 다소 부족함.",
     "[1.0점] 본문 내용을 단순히 다시 반복하는 데 그쳤으며, 학생 본인만의 사고나 결론이 드러나지 않음."),
]


def multi_para(text, bold=False):
    return "".join(para(line, bold=bold, space_after=40) for line in text.split("\n"))


def summary_table():
    w = [1800, 1500, 4326, 1400]
    rows = [row([cell("평가 영역", w[0], bold=True, shade="EEEEEE"),
                 cell("배점(비율)", w[1], bold=True, shade="EEEEEE"),
                 cell("평가 요소(항목 구성)", w[2], bold=True, shade="EEEEEE"),
                 cell("평가 척도", w[3], bold=True, shade="EEEEEE")])]
    for area, weight, items in RUBRIC_SUMMARY:
        rows.append(row([cell(area, w[0], bold=True, shade="F5F5F5"),
                          cell(weight, w[1]),
                          cell(multi_para(items), w[2]),
                          cell("상 / 중 / 하", w[3])]))
    return table(rows, w)


def detail_table():
    w = [1400, 600, 1800, 1742, 1742, 1742]
    rows = [row([cell("평가 영역", w[0], bold=True, shade="EEEEEE"),
                 cell("번호", w[1], bold=True, shade="EEEEEE"),
                 cell("평가 요소(항목 및 배점)", w[2], bold=True, shade="EEEEEE"),
                 cell("상 (우수)", w[3], bold=True, shade="EEEEEE"),
                 cell("중 (보통)", w[4], bold=True, shade="EEEEEE"),
                 cell("하 (미흡)", w[5], bold=True, shade="EEEEEE")])]
    for area, no, item, hi, mid, lo in RUBRIC_DETAIL:
        rows.append(row([cell(multi_para(area, bold=True), w[0], shade="F5F5F5"),
                          cell(no, w[1]),
                          cell(multi_para(item), w[2]),
                          cell(hi, w[3]),
                          cell(mid, w[4]),
                          cell(lo, w[5])]))
    return table(rows, w)


def final_score_table():
    w = [2256, 2256, 2256, 2258]
    return table([
        row([cell("지식 및 이해 (7점)", w[0], bold=True, shade="EEEEEE"),
             cell("탐구 및 적용 (7점)", w[1], bold=True, shade="EEEEEE"),
             cell("논리 및 완성도 (6점)", w[2], bold=True, shade="EEEEEE"),
             cell("최종 총점 (20점)", w[3], bold=True, shade="EEEEEE")]),
        row([cell("(        ) / 7 점", w[0]),
             cell("(        ) / 7 점", w[1]),
             cell("(        ) / 6 점", w[2]),
             cell("(        ) / 20 점", w[3])]),
    ], w)


def build_rubric_body():
    parts = []
    parts.append(heading("디지털논리회로 8단원 탐구보고서 채점 기준표 — 교사 전용", 1))
    parts.append(para("메모리 소자 · 마이크로프로세서 · 임베디드 시스템 (20점 만점)", align="center", space_after=120))
    parts.append(para("[교사 전용 — 학생에게 배포하지 마세요] 이 문서는 학생용 보고서 양식(학생용_보고서_양식_8단원.docx)에 "
                       "대한 채점 기준표입니다.", italic=True, bold=True, align="center", space_after=240))

    parts.append(heading("평가 개요", 2))
    parts.append(para("본 루브릭은 8단원 선택형 보고서 수행평가를 위해 지식 및 이해(7점), 탐구 및 적용(7점), "
                       "논리 및 완성도(6점)의 3개 영역, 총 9개 평가 요소(20점 만점)로 구성되었습니다. "
                       "각 평가 항목별 기준에 따라 상·중·하 수준을 평가합니다.", space_after=160))
    parts.append(summary_table())

    parts.append(heading("세부 평가 기준표", 2))
    parts.append(detail_table())

    parts.append(heading("최종 채점 및 환산표", 2))
    parts.append(final_score_table())

    return "".join(parts)


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(here)  # 수행평가/디논_8단원_탐구보고서/
    teacher_dir = f"{base}/교사용_비공개"
    os.makedirs(base, exist_ok=True)
    os.makedirs(teacher_dir, exist_ok=True)

    write_docx(f"{base}/학생용_보고서_양식_8단원.docx", build_student_body())
    write_docx(f"{teacher_dir}/교사용_채점기준표_8단원.docx", build_rubric_body())
