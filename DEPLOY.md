# Cloud Run 배포 가이드

## 사전 준비

1. **GCP 계정 및 프로젝트 생성**
   - [Google Cloud Console](https://console.cloud.google.com) 접속
   - 새 프로젝트 생성 또는 기존 프로젝트 선택

2. **gcloud CLI 설치**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # 또는 공식 설치 가이드 참조
   # https://cloud.google.com/sdk/docs/install
   ```

3. **gcloud 인증**
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

4. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일에 GEMINI_API_KEY 입력
   ```

## 빠른 배포

```bash
# 배포 스크립트 실행
./scripts/deploy.sh
```

## 수동 배포

### 1. Docker 이미지 빌드
```bash
docker build -t gcr.io/[PROJECT-ID]/ksat-math-ai:latest .
```

### 2. 이미지 푸시
```bash
docker push gcr.io/[PROJECT-ID]/ksat-math-ai:latest
```

### 3. Cloud Run 배포
```bash
gcloud run deploy ksat-math-ai \
    --image gcr.io/[PROJECT-ID]/ksat-math-ai:latest \
    --region asia-northeast3 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --set-env-vars "GEMINI_API_KEY=[YOUR-API-KEY]"
```

## CI/CD 설정 (선택사항)

### Cloud Build 트리거 설정
1. Cloud Console > Cloud Build > 트리거 생성
2. GitHub 저장소 연결
3. 트리거 구성:
   - 이벤트: Push to branch
   - 브랜치: main
   - 구성: cloudbuild.yaml
   - 대체 변수: _GEMINI_API_KEY 추가

## 비용 최적화 팁

1. **최소 인스턴스 0 설정**: 사용하지 않을 때 비용 절감
2. **리전 선택**: asia-northeast3 (서울) 사용으로 레이턴시 감소
3. **메모리 최적화**: 2Gi로 시작, 필요시 조정

## 모니터링

### 로그 확인
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ksat-math-ai" --limit 50
```

### 메트릭 확인
Cloud Console > Cloud Run > ksat-math-ai > 측정항목

## 문제 해결

### 할당량 초과 에러
- .env에 OPENAI_API_KEY 추가하여 폴백 활성화
- Gemini API 유료 플랜 업그레이드

### 메모리 부족
```bash
gcloud run services update ksat-math-ai --memory 4Gi --region asia-northeast3
```

### 콜드 스타트 개선
```bash
gcloud run services update ksat-math-ai --min-instances 1 --region asia-northeast3
```