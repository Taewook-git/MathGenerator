#!/bin/bash

echo "🔑 Gemini API 키 업데이트"
echo "========================"

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 새 API 키 발급 안내
echo -e "${YELLOW}1. 먼저 새 API 키를 발급받으세요:${NC}"
echo "   https://aistudio.google.com/"
echo "   → Get API key → Create API key"
echo ""

# 2. API 키 입력
echo -e "${YELLOW}2. 새 Gemini API 키를 입력하세요:${NC}"
read -s NEW_API_KEY

if [ -z "$NEW_API_KEY" ]; then
    echo -e "${RED}API 키가 입력되지 않았습니다${NC}"
    exit 1
fi

# 3. .env 파일 백업
cp .env .env.backup
echo -e "${GREEN}✓ .env 파일 백업 완료 (.env.backup)${NC}"

# 4. API 키 업데이트
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=\"$NEW_API_KEY\"/" .env
else
    # Linux
    sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=\"$NEW_API_KEY\"/" .env
fi

echo -e "${GREEN}✓ API 키 업데이트 완료${NC}"

# 5. API 키 테스트
echo -e "\n${YELLOW}API 키 테스트 중...${NC}"
response=$(curl -s -H 'Content-Type: application/json' \
    -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
    -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=$NEW_API_KEY")

if echo "$response" | grep -q "error"; then
    echo -e "${RED}❌ API 키 테스트 실패${NC}"
    echo "$response" | grep -o '"message":"[^"]*"'
    echo ""
    echo "이전 API 키로 복원하시겠습니까? (y/n)"
    read restore
    if [ "$restore" = "y" ]; then
        mv .env.backup .env
        echo -e "${GREEN}복원 완료${NC}"
    fi
    exit 1
else
    echo -e "${GREEN}✅ API 키 정상 작동!${NC}"
fi

# 6. 할당량 정보
echo -e "\n${YELLOW}📊 API 할당량 정보:${NC}"
echo "• 무료: 하루 50개 요청 (gemini-2.5-pro)"
echo "• 유료: Pay-as-you-go 플랜 업그레이드 권장"
echo ""
echo -e "${GREEN}✨ 설정 완료! Streamlit 앱을 재시작해주세요.${NC}"