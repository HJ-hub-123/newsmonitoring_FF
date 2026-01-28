import requests
import os
import datetime

# 1. 환경 변수 설정
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 2. 감시 키워드 리스트
KEYWORDS = [
    "HL그룹", "에이치엘", "HL만도", "HL클레무브", 
    "HL로보틱스", "묘산봉", "정몽원", "로터스 자동차",
    "한라그룹", "HL홀딩스"
]

def is_work_time():
    """주말 특정 시간에만 True 반환"""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9) # KST 변환
    weekday = now.weekday() # 5:토, 6:일
    hour = now.hour

    if weekday == 5: # 토요일: 08시~21시
        return 8 <= hour <= 21
    elif weekday == 6: # 일요일: 08시~19시
        return 8 <= hour <= 19
    return False

def clean_text(text):
    """HTML 태그 제거 및 특수문자 정화"""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')

def check_news():
    if not is_work_time():
        print("현재는 모니터링 시간이 아닙니다.")
        return

    print(f"모니터링 시작: {datetime.datetime.now()}")
    
    for query in KEYWORDS:
        # 네이버 뉴스 검색 API 호출 (최신순)
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=date"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        try:
            response = requests.get(url, headers=headers)
            news_items = response.json().get('items', [])
            
            for item in news_items:
                # 뉴스 발행 시간 파싱
                pub_date = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
                
                # 실행 시점 기준, 최근 1시간(3600초) 이내 등록된 뉴스만 필터링
                diff = (now_kst - pub_date).total_seconds()
                
                if 0 <= diff < 3600:
                    title = clean_text(item['title'])
                    link = item['link']
                    
                    message = (
                        f"🚨 [HL 관련 신규 뉴스]\n"
                        f"🔍 키워드: {query}\n"
                        f"📝 제목: {title}\n"
                        f"🔗 링크: {link}"
                    )
                    
                    # 텔레그램 메시지 전송
                    tel_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    requests.get(tel_url, params={"chat_id": TELEGRAM_CHAT_ID, "text": message})
                    print(f"알림 발송 완료: {title[:20]}...")
                    
        except Exception as e:
            print(f"에러 발생 ({query}): {e}")

if __name__ == "__main__":
    check_news()