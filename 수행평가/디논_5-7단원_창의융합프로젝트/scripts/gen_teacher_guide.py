# -*- coding: utf-8 -*-
"""교사용 '즉석 변형 질문 가이드' A4 한 장짜리 docx를 생성한다 (gen_docx2.py의 헬퍼 재사용)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_docx2 as g

PROJECTS = [
    ("인코더/디코더 (주차타워 안내판)",
     "4층이 새로 생기면 회로 어디를 바꿔야 해?",
     "1·2층이 동시에 비면 왜 1층이 표시돼?"),
    ("MUX/DEMUX (방송 선택 송출)",
     "신호원이 5개면 선택 스위치가 몇 비트 필요해?",
     "DEMUX 없이 MUX만 있으면 어떻게 돼?"),
    ("비교기 (계주 기록 비교)",
     "세 팀을 비교하려면 회로를 어떻게 늘려야 해?",
     "A=B일 때 왜 두 LED가 동시에 안 켜져?"),
    ("코드 변환기 (그레이코드 다이얼)",
     "5비트로 늘리면 XOR을 몇 개 더 넣어야 해?",
     "반대로 2진수→그레이코드는 회로가 어떻게 달라져?"),
    ("레지스터 (교실 신호 직병렬 전송)",
     "5번째 교실이 추가되면 뭐가 바뀌어야 해?",
     "Load/Shift 선택 MUX가 없으면 어떻게 돼?"),
    ("비동기 카운터 (기구 대여 횟수)",
     "최대 15까지 세려면 플립플롭이 몇 개 필요해?",
     "값이 바뀔 때 왜 LED가 잠깐 깜빡여?"),
    ("동기 카운터 (실험/발표 타이머)",
     "상향만 쓰면 회로가 어떻게 간단해져?",
     "동기식이 비동기식보다 빠른 이유가 뭐야?"),
    ("링 카운터 (학예회 순서 표시등)",
     "팀이 7개면 뭘 바꿔야 해?",
     "초기화 스위치가 없으면 무슨 문제가 생겨?"),
]


def build():
    parts = []
    parts.append(g.heading("즉석 변형 질문 가이드 (교사용)", 1))
    parts.append(g.para("디지털논리회로 창의융합프로젝트 수행평가 — 5·7단원 발표일 참고자료",
                         align="center", italic=True, space_after=200))

    parts.append(g.heading("좋은 질문의 원칙", 2))
    for t in [
        "학생의 실제 회로를 가리키며 질문한다 (교과서 일반론 질문 금지)",
        "\"네/아니오\"로 답할 수 없게 묻는다",
        "조건 하나만 바꿔 예측시킨다 — 정답 여부보다 추론 과정을 본다",
        "침묵을 8~10초 허용한다 — 서둘러 힌트를 주지 않는다",
        "1차 답변 후 \"왜?\"를 한 번 더 물어 깊이를 확인한다",
    ]:
        parts.append(g.bullet(t))

    parts.append(g.heading("범용 질문 (모든 프로젝트 공통)", 2))
    for t in [
        "입력이 하나 더 늘어나면 회로 어디를 바꿔야 해?",
        "이 소자를 빼면 무슨 일이 생겨?",
        "이 두 입력이 동시에 들어오면 어떻게 돼?",
        "지금 이 값을 넣으면 출력이 뭐가 나올지 계산해봐 (답부터 말하지 말고 손으로 짚어가며)",
    ]:
        parts.append(g.bullet(t))

    parts.append(g.heading("프로젝트별 맞춤 질문", 2))
    w1, w2 = 2800, 6226
    rows = [g.row([g.cell("프로젝트", w1, bold=True, shade="EEEEEE"),
                    g.cell("즉석 질문 예시", w2, bold=True, shade="EEEEEE")])]
    for name, q1, q2 in PROJECTS:
        content = g.para(f"① {q1}", space_after=40) + g.para(f"② {q2}", space_after=40)
        rows.append(g.row([g.cell(name, w1), g.cell(content, w2)]))
    parts.append(g.table(rows, [w1, w2]))

    parts.append(g.heading("채점 기준 요약 — 질의응답 대응력(즉석 변형 질문)", 2))
    name, l0, l2, l4, l6 = g.RUBRIC[4]
    sw = [2256, 2256, 2256, 2258]
    parts.append(g.table([
        g.row([g.cell("0점", sw[0], bold=True, shade="EEEEEE"),
               g.cell("2점", sw[1], bold=True, shade="EEEEEE"),
               g.cell("4점", sw[2], bold=True, shade="EEEEEE"),
               g.cell("6점", sw[3], bold=True, shade="EEEEEE")]),
        g.row([g.cell(l0, sw[0]), g.cell(l2, sw[1]), g.cell(l4, sw[2]), g.cell(l6, sw[3])]),
    ], sw))

    return "".join(parts)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "교사용_비공개")
    os.makedirs(out_dir, exist_ok=True)
    g.write_docx(f"{out_dir}/교사용_즉석질문가이드.docx", build())
