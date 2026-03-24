# FarmGPT - AI 농업 컨설팅 플랫폼

스마트농업 AI 경진대회를 위한 통합 농업 컨설팅 AI 플랫폼입니다.

## 핵심 기능

| 모듈 | 기능 | 기술 |
|------|------|------|
| AI 컨설팅 | RAG 기반 농업 전문 챗봇 | Claude API + ChromaDB |
| 작물 진단 | 텍스트/이미지 병해충 진단 | Claude Vision API |
| 스마트팜 | 환경 시뮬레이션 + 제어 최적화 | 물리 모델 + PID 제어 |
| 데이터 분석 | 가격/수확량 예측 | 시계열 분석 + 환경 보정 |

## 기술 스택

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **AI/LLM**: Claude API (Anthropic)
- **RAG**: ChromaDB (벡터 DB)
- **DB**: PostgreSQL, Redis
- **Infra**: Docker Compose

## 빠른 시작

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 2. Docker로 실행
docker compose up --build

# 3. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

## 개별 실행

```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 지식베이스 인덱싱 (ChromaDB 실행 필요)
python -m scripts.index_knowledge

# 프론트엔드
cd frontend
npm install
npm run dev

# 테스트
cd backend
pytest -v
```

## API 엔드포인트

### Chat
- `POST /api/chat/` - RAG 기반 챗봇 (SSE 스트리밍)

### Diagnosis
- `POST /api/diagnosis/text` - 텍스트 기반 진단
- `POST /api/diagnosis/image` - 이미지 기반 진단
- `GET /api/diagnosis/crops` - 지원 작물 목록

### Smart Farm
- `POST /api/smartfarm/analyze` - 환경 데이터 AI 분석
- `POST /api/smartfarm/simulate` - 24시간 시뮬레이션
- `POST /api/smartfarm/compare` - 제어 전략 비교

### Analytics
- `POST /api/analytics/predict-price` - 가격 예측
- `POST /api/analytics/predict-yield` - 수확량 예측
- `GET /api/analytics/price-history/{crop}` - 가격 히스토리

### Knowledge
- `POST /api/knowledge/index` - 지식베이스 인덱싱
- `GET /api/knowledge/search` - 벡터 검색
- `POST /api/knowledge/upload` - 문서 업로드

## 프로젝트 구조

```
farm-gpt/
├── backend/
│   ├── app/
│   │   ├── api/          # API 라우터 (chat, diagnosis, smartfarm, analytics, knowledge)
│   │   ├── core/         # 설정, DB
│   │   ├── models/       # Pydantic 스키마
│   │   └── services/
│   │       ├── llm/      # Claude API 연동
│   │       ├── rag/      # RAG 엔진 (벡터 저장소, 데이터 수집)
│   │       ├── vision/   # 이미지 진단
│   │       ├── prediction/ # 가격/수확량 예측
│   │       └── smartfarm/  # 시뮬레이터 + 최적화
│   ├── data/knowledge_base/ # 농업 지식 문서 (6개)
│   └── tests/            # pytest 테스트
├── frontend/
│   └── src/
│       ├── components/   # UI 컴포넌트 (6개 뷰)
│       └── lib/          # API 클라이언트
└── docker-compose.yml    # 5개 서비스
```

## 지식베이스

| 문서 | 내용 |
|------|------|
| strawberry.md | 딸기 품종, 재배환경, 병해충, 스마트팜 전략 |
| tomato.md | 토마토 재배 가이드 |
| paprika.md | 파프리카 재배 가이드 |
| smartfarm_basics.md | 스마트팜 센서, 제어, 세대 구분 |
| pest_management.md | IPM 원칙, 천적 활용, 친환경 방제 |
| climate_farming.md | 기후변화 대응 기술 |

## 대회 특화 (Phase 6)

대회 주제 발표 후:
1. 대회 데이터셋 적용
2. 해당 작물 모듈 특화
3. 실증 재배 전략 수립
4. 제출물 문서 작성
