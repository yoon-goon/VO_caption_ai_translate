import google.generativeai as genai
import time
import os

API_KEY = "APIkey"
INPUT_FILE = "citadel_generated_vo_koreana.txt"
OUTPUT_FILE = "strings_ko.txt"
PROGRESS_FILE = "progress.txt" # 현재 진행 줄 번호를 저장하는 파일
BATCH_SIZE = 150 # 한 번에 번역할 줄 수

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def translate_batch(batch_text):
    prompt = f"""
    게임 번역 전문가로서 다음 스트링을 한국어로 번역해.
    규칙:
    1. "Key" "Value" 형식을 유지할 것.
    2. 'dynamo'는 반드시 '다이나모'로 번역할 것.
    3. 대사 톤은 게임 캐릭터처럼 자연스럽게 할 것.
    4. 번역본 외에 다른 설명은 생략할 것.
    5. 아이템 이름을 정해진 대로 번역할 것(예시: 강철 피부, 공명의 파편)

    내용:
    {batch_text}
    """
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"\n[알림] API 제한 또는 에러 발생: {e}")
        return None

def start_translation():
    # 이전에 어디까지 했는지 확인
    start_line = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            line_content = f.read().strip()
            if line_content:
                start_line = int(line_content)
                print(f">>> 이전 기록 발견: {start_line}행부터 이어갑니다.")

    if not os.path.exists(INPUT_FILE):
        print(f"오류: {INPUT_FILE} 파일이 없습니다.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total = len(all_lines)

    # 파일을 'a' (append) 모드로 열어서 기존 내용 뒤에 붙임
    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
        for i in range(start_line, total, BATCH_SIZE):
            batch = all_lines[i : i + BATCH_SIZE]
            batch_text = "".join(batch)

            print(f"진행 중: {i}/{total} ({round(i/total*100, 1)}%)", end="\r")

            result = translate_batch(batch_text)

            if result:
                out_f.write(result + "\n")
                # 성공할 때마다 진행 상황 파일에 저장
                with open(PROGRESS_FILE, "w") as p_f:
                    p_f.write(str(i + BATCH_SIZE))

                # API 안정성을 위해
                time.sleep(2)
            else:
                print(f"\n[중단] {i}행에서 멈췄습니다. 나중에 다시 실행 버튼을 누르세요.")
                return 

    print("\n[완료] 모든 번역이 끝났습니다!")

start_translation()
