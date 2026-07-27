# -*- coding: utf-8 -*-
"""교사용 예시 보고서에 들어가는 회로 구조도(블록 다이어그램) PNG를 생성한다.
diagrams/ 폴더(이 스크립트 옆)에 저장되며, gen_docx2.py가 이 폴더를 읽어 docx에 삽입한다.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# 한글이 표시되는 CJK 폰트를 찾아 등록 (Noto Sans CJK 우선, 없으면 나눔고딕)
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
for _fp in FONT_CANDIDATES:
    if os.path.exists(_fp):
        fm.fontManager.addfont(_fp)
        plt.rcParams["font.family"] = fm.FontProperties(fname=_fp).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

BOX_W, BOX_H = 1.7, 0.85
GAP = 0.55


def box(ax, cx, cy, label, fc="#eef3fb", ec="#3a5a8a", w=BOX_W, h=BOX_H, fontsize=11, fontweight="normal"):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                        boxstyle="round,pad=0.03,rounding_size=0.06",
                        linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize, fontweight=fontweight,
            zorder=4, linespacing=1.3)


def arrow(ax, x1, y1, x2, y2, style="-|>", color="#333333", lw=1.6, connectionstyle="arc3,rad=0.0", ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                         linewidth=lw, color=color, connectionstyle=connectionstyle, zorder=2, linestyle=ls)
    ax.add_patch(a)


def draw_chain(out_path, main_chain, extra_inputs=None, below_labels=None, wrap_around=False,
               note=None, figsize=(9, 3.2), title=None):
    extra_inputs = extra_inputs or []
    n = len(main_chain)
    xs = [GAP + BOX_W / 2 + i * (BOX_W + GAP) for i in range(n)]
    cy = 1.9 if extra_inputs else 1.5

    y_bottom_lim = -0.75 if (wrap_around and below_labels) else 0
    fig, ax = plt.subplots(figsize=figsize, dpi=170)
    ax.set_xlim(-0.7, xs[-1] + BOX_W / 2 + GAP + 0.3)
    ax.set_ylim(y_bottom_lim, cy + 2.0)
    ax.axis("off")

    if title:
        ax.text(ax.get_xlim()[1] / 2, cy + 1.75, title, ha="center", va="center",
                fontsize=13, fontweight="bold")

    for i, label in enumerate(main_chain):
        box(ax, xs[i], cy, label)
        if i > 0:
            arrow(ax, xs[i - 1] + BOX_W / 2, cy, xs[i] - BOX_W / 2, cy)

    # stack multiple extra inputs that target the same index
    from collections import defaultdict
    grouped = defaultdict(list)
    for idx, label in extra_inputs:
        grouped[idx].append(label)
    for idx, labels in grouped.items():
        m = len(labels)
        for j, label in enumerate(labels):
            ex_cy = cy + 0.95
            ex_cx = xs[idx] + (j - (m - 1) / 2) * (BOX_W + 0.15)
            box(ax, ex_cx, ex_cy, label, fc="#fff3e0", ec="#b06a1e", w=1.45, h=0.7, fontsize=9.5)
            arrow(ax, ex_cx, ex_cy - 0.35, xs[idx] + (ex_cx - xs[idx]) * 0.15, cy + BOX_H / 2,
                  color="#b06a1e")

    if below_labels:
        for i, label in enumerate(below_labels):
            if not label:
                continue
            by = cy - 1.0
            box(ax, xs[i], by, label, fc="#eaf7ea", ec="#2f7a3d", h=0.6, fontsize=9.5)
            arrow(ax, xs[i], cy - BOX_H / 2, xs[i], by + 0.3, color="#2f7a3d")

    if wrap_around:
        anchor_y = (cy - 1.0 - 0.3) if below_labels else (cy - BOX_H / 2)
        arrow(ax, xs[-1], anchor_y, xs[0], anchor_y,
              connectionstyle=f"arc3,rad={-0.4 if not below_labels else -0.14}",
              color="#8a2f8a", lw=1.6)

    if note:
        note_y = -0.55 if (wrap_around and below_labels) else 0.15
        ax.text((ax.get_xlim()[0] + ax.get_xlim()[1]) / 2, note_y, note,
                ha="center", va="center", fontsize=9.5, color="#444444")

    plt.tight_layout()
    plt.savefig(out_path, transparent=False, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print("saved", out_path)


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)

draw_chain(f"{OUT}/5_encoder.png",
           ["층별 입력\n스위치 (3개)", "74148\n우선순위\n인코더", "7447\nBCD-세그먼트\n디코더", "7세그먼트\n표시장치"],
           note="동시에 여러 층이 입력돼도 74148이 가장 낮은 층 번호를 우선 출력",
           figsize=(9.2, 3.0))

draw_chain(f"{OUT}/5_mux.png",
           ["신호원 스위치\n(3개)", "74151\n8:1 MUX", "74155\n2:4 DEMUX", "교실 LED\n(4개)"],
           extra_inputs=[(1, "입력 선택\n스위치 S1S0"), (2, "출력 선택\n스위치 D1D0")],
           note="MUX 선택과 DEMUX 선택을 분리해 '누가 보내고 누가 받는지' 독립 제어",
           figsize=(9.6, 3.6))

draw_chain(f"{OUT}/5_comparator.png",
           ["7485\n4비트 비교기", "승리/동점\nLED (3개)"],
           extra_inputs=[(0, "A팀 기록\n스위치(4bit)"), (0, "B팀 기록\n스위치(4bit)")],
           note="A<B → A팀 승리 LED,  A>B → B팀 승리 LED,  A=B → 동점 LED",
           figsize=(7.6, 3.6))

draw_chain(f"{OUT}/5_code_converter.png",
           ["그레이코드\n입력 스위치(4bit)", "XOR 게이트 체인\n(G→B 순차 변환)", "7447\nBCD-세그먼트\n디코더", "7세그먼트\n표시장치"],
           note="최상위 비트부터 순서대로 누적 XOR: B3=G3, B2=B3⊕G2, B1=B2⊕G1, B0=B1⊕G0",
           figsize=(9.6, 3.0))

draw_chain(f"{OUT}/7_register.png",
           ["교실 센서\n스위치(4개)", "PISO 송신\n(7474×4 + 74157)", "직렬선\n1가닥", "SIPO 수신\n(7474×4)", "관리실\nLED(4개)"],
           note="송신·수신 D 플립플롭이 같은 클럭을 공유해야 비트가 밀리지 않음",
           figsize=(10.4, 3.0))

draw_chain(f"{OUT}/7_async_counter.png",
           ["대여 버튼\n(클럭)", "7476 JK-FF\nFa (최하위)", "7476 JK-FF\nFb", "7476 JK-FF\nFc (최상위)", "표시 LED\n(3개, 2진)"],
           note="비동기(리플): Fa의 출력 Q가 Fb의 클럭, Fb의 출력 Q가 Fc의 클럭으로 순차 전파",
           figsize=(10.2, 3.0))

draw_chain(f"{OUT}/7_sync_counter.png",
           ["7476 JK-FF\nFa", "7476 JK-FF\nFb", "7476 JK-FF\nFc", "표시 LED\n(3개, 2진)"],
           extra_inputs=[(0, "공통 클럭\n(Fa·Fb·Fc 동시)"), (0, "모드 선택\n스위치 X")],
           note="X=0: 상향(000→111)  /  X=1: 하향(111→000), 모든 FF가 같은 클럭에 동시 반응",
           figsize=(8.8, 3.6))

draw_chain(f"{OUT}/7_ring_counter.png",
           ["7474 D-FF\nFa", "7474 D-FF\nFb", "7474 D-FF\nFc", "7474 D-FF\nFd", "7474 D-FF\nFe"],
           extra_inputs=[(0, "초기화 스위치\n(Fa=1 설정)"), (0, "'다음 순서'\n버튼(클럭)")],
           below_labels=["1팀 LED", "2팀 LED", "3팀 LED", "4팀 LED", "5팀 LED"],
           wrap_around=True,
           note="D 플립플롭 5개를 Qa→Db→Qb→Dc→…→Qe→Da 순으로 고리 연결, 클럭마다 1이 한 칸씩 이동",
           figsize=(10.8, 4.4))

print("done")
