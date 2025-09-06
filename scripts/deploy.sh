#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 KSAT Math AI Cloud Run 배포 스크립트${NC}"
echo "========================================"

# 프로젝트 ID 설정
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}GCP 프로젝트 ID를 입력하세요:${NC}"
    read GCP_PROJECT_ID
fi

# 리전 설정
REGION=${REGION:-"asia-northeast3"}  # 기본값: 서울
SERVICE_NAME="ksat-math-ai"

echo -e "\n${GREEN}설정 정보:${NC}"
echo "- Project ID: $GCP_PROJECT_ID"
echo "- Region: $REGION"
echo "- Service Name: $SERVICE_NAME"

# .env 파일에서 API 키 읽기
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ .env 파일 로드 완료${NC}"
else
    echo -e "${RED}✗ .env 파일을 찾을 수 없습니다${NC}"
    exit 1
fi

# API 키 확인
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}✗ GEMINI_API_KEY가 설정되지 않았습니다${NC}"
    exit 1
fi

# gcloud 설정
echo -e "\n${GREEN}1. GCP 프로젝트 설정 중...${NC}"
gcloud config set project $GCP_PROJECT_ID

# 필요한 API 활성화
echo -e "\n${GREEN}2. 필요한 GCP API 활성화 중...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Docker 이미지 빌드
echo -e "\n${GREEN}3. Docker 이미지 빌드 중...${NC}"
IMAGE_NAME="gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME"
docker build -t $IMAGE_NAME:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Docker 빌드 실패${NC}"
    exit 1
fi

# Container Registry에 이미지 푸시
echo -e "\n${GREEN}4. Container Registry에 이미지 푸시 중...${NC}"
docker push $IMAGE_NAME:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 이미지 푸시 실패${NC}"
    echo -e "${YELLOW}gcloud auth configure-docker를 실행해보세요${NC}"
    exit 1
fi

# Cloud Run 배포
echo -e "\n${GREEN}5. Cloud Run에 배포 중...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY" \
    --port 8080

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 배포 완료!${NC}"
    
    # 서비스 URL 가져오기
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    echo -e "${GREEN}🌐 서비스 URL: $SERVICE_URL${NC}"
    
    # 선택적: 브라우저 열기
    if command -v open &> /dev/null; then
        echo -e "${YELLOW}브라우저에서 열겠습니까? (y/n)${NC}"
        read -r response
        if [[ "$response" == "y" ]]; then
            open "$SERVICE_URL"
        fi
    fi
else
    echo -e "${RED}✗ 배포 실패${NC}"
    exit 1
fi

echo -e "\n${GREEN}📝 다음 단계:${NC}"
echo "1. Cloud Console에서 서비스 확인: https://console.cloud.google.com/run"
echo "2. 로그 확인: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo "3. 서비스 업데이트: 이 스크립트를 다시 실행하면 됩니다"