# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Vue3 + FastAPI + SQLite 기반 학습 사이트. `backend/`(FastAPI API 서버), `frontend/`(Vue3 SPA), `data/`(문제·성취기준 JSON) 구조.

# 프로젝트 개요
 - 이름 : 정보ON
 - 목표 : 기출문제를 학습하고, 학생들이 코딩 테스트를 할 수 있게 제공
 - 언어: vue.js, fastapi, sqlite

# 문제 교차 검증 가이드라인

모든 문제 작성 시 확인 사항
1. 정답이 하나뿐인가?
  - 다른 해석 가능 시 조건 명시
2. 최상급 표현에 기준이 있는가?
  - '가장 큰', '최초의' 등 표현에 측정 기준 명시
3. 시간과 범위가 명확한가?
  - 변할 수 있는 정보는 시점 명시
  - 코드 문제는 파이썬으로 한정
4. 교차 검증했는가?
  - 의심스러운 정보는 2개 이상 출처 확인
  - 논란 있는 내용은 주류 학설 기준