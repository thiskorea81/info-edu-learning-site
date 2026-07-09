# 정보교육학습사이트

기출문제를 학습하고, 파이썬 코드를 직접 실행/제출해볼 수 있는 학습 사이트입니다.
Vue3(프론트엔드) + FastAPI(백엔드) + SQLite로 만들어졌습니다.

## Docker로 실행하기 (권장)

```bash
docker compose up --build
```

빌드가 끝나면 브라우저에서 http://localhost:8080 으로 접속하면 됩니다.

- 문제/성취기준/학습 기록은 모두 `data/` 폴더에 저장되며, 컨테이너를 내려도 유지됩니다.
- `docker compose down` 으로 종료할 수 있습니다.

> `docker compose` 명령이 없다면 Docker Compose 플러그인을 설치하세요:
> `sudo apt install docker-compose-plugin`
> 권한 오류(permission denied)가 나면 `sudo usermod -aG docker $USER` 후 재로그인하거나, 각 명령 앞에 `sudo`를 붙이세요.

## 로컬에서 직접 실행하기 (Docker 없이)

### 백엔드

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173 으로 접속합니다 (개발 서버가 `/api` 요청을 자동으로 백엔드(8000번 포트)로 전달합니다).

## 폴더 구조

```
backend/    FastAPI 서버 (app/)
frontend/   Vue3 SPA (src/)
data/       문제(questions/), 코딩테스트 문제(problems/), 성취기준(standards.json), 학습 기록(study.db)
```

## 문제 추가하기

사이트 상단의 "문제 등록" 메뉴에서 문제를 하나씩 등록하거나, JSON 파일로 여러 문제를 한 번에 등록할 수 있습니다
(양식 다운로드 버튼으로 형식을 확인할 수 있습니다). `data/problems/`에 같은 형식의 JSON 파일을 추가하면
코딩테스트 문제도 늘릴 수 있습니다.
