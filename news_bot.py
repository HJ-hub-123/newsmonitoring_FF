import requests
import os
import datetime
import xml.etree.ElementTree as ET # XML 파싱을 위한 도구

# ==========================================
# 1. 설정
# ==========================================
# 지금 당장 테스트하려면 True, 주말에만 작동하게 하려면 False
TEST_MODE = False

# 검색 키워드 리스트 (제공해주신 리스트 유지)
KEYWORDS = [
    "HL", "에이치엘", "만도", "한라", 
    "묘산봉", "정몽원", "이윤행", "로터스PE"
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

    # 요청하신 시간 설정: 토요일(10-21시), 일요일(07-19시)
    if weekday == 5: # 토요일
        return 10 <= hour <= 21
    elif weekday == 6: # 일요일
        return 7 <= hour <= 19
    return False

def clean_text(text):
    """HTML 태그 제거 및 특수기호 정화"""
    if text is None: return ""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

def check_news():
    if not is_work_time():
        print("현재는 모니터링 시간이 아닙니다.")
        return

    print(f"모니터링 시작: {datetime.datetime.now()}")
    
    # 중복 발송 방지를 위해 이번 실행에서 보낸 링크 저장
    sent_links = []
    
    for query in KEYWORDS:
        # [업그레이드] 1. XML 방식으로 변경 / 2. 한 번에 50개씩 가져오기(누락 방지)
        url = f"https://openapi.naver.com/v1/search/news.xml?query={query}&display=50&sort=date"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"네이버 API 에러: {response.status_code}")
                continue

            # XML 파싱
            root = ET.fromstring(response.text)
            items = root.findall('./channel/item')
            
            for item in items:
                pub_date_str = item.find('pubDate').text
                pub_date = datetime.datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S +0900')
                now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
                diff = (now_kst - pub_date).total_seconds()
                
                # [업그레이드] 기사 누락 방지를 위해 시간 범위를 2시간(7200초)으로 확대
                # 1시간 간격으로 실행되므로 2시간 범위를 뒤져야 '시간대 경계'에 있는 기사를 놓치지 않습니다.
                time_limit = 86400 if TEST_MODE else 7200
                
                if 0 <= diff < time_limit:
                    title = clean_text(item.find('title').text)
                    # [업그레이드] 언론사 원문 링크(originallink)를 먼저 가져옴
                    link = item.find('originallink').text if item.find('originallink') is not None else item.find('link').text
                    
                    # 중복 기사 전송 방지
                    if link in sent_links:
                        continue
                    
                    # 텔레그램 메시지 포맷
                    mode_prefix = "[테스트 알림]" if TEST_MODE else "[신규 뉴스 발견]"
                    message = (
                        f"{mode_prefix}\n"
                        f"🔍 키워드: {query}\n"
                        f"📝 제목: {title}\n"
                        f"🔗 원문링크: {link}"
                    )
                    
                    # 텔레그램 발송
                    tel_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    res = requests.get(tel_url, params={"chat_id": TELEGRAM_CHAT_ID, "text": message})
                    
                    if res.status_code == 200:
                        print(f"발송 성공: {title[:20]}...")
                        sent_links.append(link)
                    else:
                        print(f"텔레그램 발송 에러: {res.status_code}")
                        
        except Exception as e:
            print(f"오류 발생 ({query}): {e}")

if __name__ == "__main__":
    check_news()
