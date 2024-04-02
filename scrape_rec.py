# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import pickle

# Constants
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'}
BASE_URL = "https://www.saramin.co.kr/zf_user/jobs/list/job-category"
KEYWORDS = {'전산총무': 415, '자동차': 2218}

# Function to fetch and parse job data
def fetch_job_data(keyword_code, pages=2):
    session = requests.Session()
    data = []

    for page in range(1, pages + 1):
        response = session.get(f"{BASE_URL}?cat_kewd={keyword_code}&page={page}&page_count=1000&sort=RD", headers=HEADERS)
        if response.status_code == 200:
            data.append(response.text)
        else:
            break
    
    return data

# Function to process job postings into a DataFrame
def process_job_postings(data, keyword):
    item_list = []

    for html in data:
        soup = BeautifulSoup(html, 'html.parser')
        box_item_list = soup.select('div.box_item')

        for box_item in box_item_list:
            item = {
                'company_name': box_item.select_one('.company_nm > .str_tit').text.strip(),
                'company_sn': box_item.select_one('.interested_corp')['csn'],
                'is_headhunting': '헤드헌팅' in box_item.select_one(".company_nm").text,
                'job_idx': int(box_item.find('button', attrs={'rec_idx': True})['rec_idx']),
                'job_title': box_item.select_one('.notification_info a.str_tit')['title'],
                'job_link': f"https://www.saramin.co.kr{box_item.select_one('.notification_info a.str_tit')['href']}",
                'job_sectors': [i.text for i in box_item.select('.notification_info .job_meta .job_sector span')] + [keyword],
                'work_place': box_item.select_one('.recruit_info .work_place').text if box_item.select_one('.recruit_info .work_place') else None,
                'career_info': box_item.select_one('.recruit_info .career').text,
                'education_info': box_item.select_one('.recruit_info .education').text,
                'support_date': box_item.select_one('.support_info .date').text,
                'deadline': box_item.select_one('.support_info .deadlines').text,
                'update': pd.to_datetime("now")
            }
            item_list.append(item)
    
    df = pd.DataFrame(item_list)
    df = df.apply(process_deadline, xis=1)
    df.set_index("job_idx", inplace=True)
    return df

# Function to process the deadline field
def process_deadline(row):
    x = row["deadline"]

    word = x.split(" ")[0]

    if "일" in word:
        delta = pd.Timedelta(days=int(word.split("일")[0]))
    elif "시간" in word:
        delta = pd.Timedelta(hours=int(word.split("시간")[0]))
    elif "분" in word:
        delta = pd.Timedelta(minutes=int(word.split("분")[0]))

    if "등록" in x:
        row["resistered"] = row["update"] - delta
    elif "수정" in x:
        row["modified"] = row["update"] - delta
    else:
        pass

    return row


def load_dataframes():
    try:
        with open('df_combined.pickle', 'rb') as file:
            df_combined = pickle.load(file)
    except FileNotFoundError:
        df_combined = pd.DataFrame()  # Define your combined DataFrame structure

    try:
        with open('df_key.pickle', 'rb') as file:
            df_key = pickle.load(file)
    except FileNotFoundError:
        df_key = pd.DataFrame(columns=['job_idx', 'job_sectors'])
    return df_combined, df_key

def update_combined_dataframe(df_combined, df_new):
    df_combined = df_new.combine_first(df_combined)

    # resistered가 비어있는 경우, modified로 채우기
    df_combined["resistered"] = df_combined["resistered"].combine_first(df_combined["modified"])
    assert df_combined.shape[1] == 14, "The number of columns is not 14."
    print("The number of columns is 14.")
    return df_combined

def update_keyword_dataframe(df_key, df_new):
    # Your logic to update df_key with new keywords from df_new
    df_key = df_new[['job_sectors']]
    df_key.reset_index(inplace=True)
    df_key = df_key.explode('job_sectors', ignore_index=True)
    df_key.drop_duplicates(inplace=True)
    return df_key

def save_dataframes(df_combined, df_key):
    with open('df_combined.pickle', 'wb') as file:
        pickle.dump(df_combined, file)
    with open('df_key.pickle', 'wb') as file:
        pickle.dump(df_key, file)

# Process and update data for each keyword
for keyword, code in KEYWORDS.items():
    df_combined, df_key = load_dataframes()
    data = fetch_job_data(code)
    df_new = process_job_postings(data, keyword)
    df_combined = update_combined_dataframe(df_combined, df_new)
    df_key = update_keyword_dataframe(df_key, df_new)
    save_dataframes(df_combined, df_key)

