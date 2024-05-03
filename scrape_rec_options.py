from selenium import webdriver
import time
import json

BASE_URL = "https://www.saramin.co.kr/zf_user/jobs/list/job-category"
# 헤드리스
options = webdriver.ChromeOptions()
# options.add_argument("headless")
driver = webdriver.Chrome(options=options)

# BASE_URL에 접속
driver.get(BASE_URL)

# 로드 기다리기
time.sleep(3)

# searchPanelArgs.options를 가져옴
ops_object = driver.execute_script("return searchPanelArgs.options")
driver.quit()

# json으로 변환, 파일로 저장
ops_dict = json.loads(ops_object)
with open("searchPanelArgs.options.json", "w", encoding="utf-8") as file:
    json.dump(ops_dict, file, ensure_ascii=False, indent=4)
