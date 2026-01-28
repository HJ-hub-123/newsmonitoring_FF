import requests
import os
import datetime

# ==========================================
# 1. 설정 (이 부분만 확인하세요)
# ==========================================
# 지금 당장 테스트하려면 True, 주말에만 작동하게 하려면 False
TEST_MODE = False

# 검색 키워드 리스트
KEYWORDS = [
    "HL그룹", "에이치엘", "HL만도", "한라", 
    "HL클레무브", "HL로보틱스", "묘산봉", "정몽원 회장", "로터스PEF"
]

# 환경 변수 (GitHub Secrets에서 자동으로 가져옴)
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def is_work_time():
    """작동 시간 체크 (TEST_MODE가 True이면 무조건 통과)"""
    if TEST_MODE:
        return True
        
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9) # KST(한국시간) 변환
    weekday = now.weekday() # 5:토요일, 6:일요일
    hour = now.hour

    if weekday == 5: # 토요일: 아침 10시 ~ 밤 9시
        return 10 <= hour <= 21
    elif weekday == 6: # 일요일: 아침 7시 ~ 저녁 7시
        return 7 <= hour <= 19
    return False

def clean_text(text):
    """HTML 태그 제거"""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')

def check_news():
    if not is_work_time():
        print("현재는 모니터링 시간이 아닙니다. (주말이 아니거나 업무 외 시간)")
        return

    print(f"모니터링 시작: {datetime.datetime.now()}")
    
    for query in KEYWORDS:
        # 네이버 뉴스 검색 API (최신순)
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=10&sort=date"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"네이버 API 에러: {response.status_code}")
                continue

            news_items = response.json().get('items', [])
            
            for item in news_items:
                pub_date = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
                diff = (now_kst - pub_date).total_seconds()
                
                # 테스트 모드일 때는 최근 24시간 뉴스 발송, 평소에는 30분 이내 뉴스만 발송
                time_limit = 86400 if TEST_MODE else 1800
                
                if 0 <= diff < time_limit:
                    title = clean_text(item['title'])
                    link = item['link']
                    
                    # 텔레그램 메시지 포맷
                    mode_prefix = "[테스트 알림]" if TEST_MODE else "[신규 뉴스 발견]"
                    message = (
                        f"{mode_prefix}\n"
                        f"🔍 키워드: {query}\n"
                        f"📝 제목: {title}\n"
                        f"🔗 링크: {link}"
                    )
                    
                    # 텔레그램 발송
                    tel_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    res = requests.get(tel_url, params={"chat_id": TELEGRAM_CHAT_ID, "text": message})
                    
                    if res.status_code == 200:
                        print(f"발송 성공: {title[:20]}...")
                    else:
                        print(f"텔레그램 발송 에러: {res.status_code}")
                        
        except Exception as e:
            print(f"오류 발생 ({query}): {e}")

if __name__ == "__main__":
    check_news()
