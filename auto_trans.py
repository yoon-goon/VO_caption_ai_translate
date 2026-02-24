
from google import genai
from google.genai import types
import time
import os
from tenacity import retry, wait_exponential, stop_after_attempt

API_KEY = "API KEY" 
INPUT_FILE = "citadel_generated_vo_koreana.txt"
OUTPUT_FILE = "strings_ko.txt"
PROGRESS_FILE = "progress.txt"

BATCH_SIZE = 800
MODEL_ID = "gemini-3-flash-preview"

client = genai.Client(api_key=API_KEY)

@retry(wait=wait_exponential(multiplier=1, min=4, max=15), stop=stop_after_attempt(7))
def translate_batch(batch_text):
    prompt = f"""
    너는 게임 '데드락(Deadlock)' 전문 번역가야. 아래 스트링을 한국어로 번역해.
    
    [반드시 지켜야 할 용어 사전]
    - 'dynamo' -> '다이나모' (절대 '다이너모'로 번역하지 말 것)
    - 'Calico' -> '칼리코'
    - 'Viscous' -> '비스쿠스'
    - 'Metal Skin' -> '강철 피부'
    - 'Echo Shard' -> '공명의 파편'
    - 'seventh moon' -> '7번째 달'
    
    [번역 규칙]
    1. 형식 엄수: "Key" "Value" 형식을 그대로 유지할 것.
    2. 모든 Value를 번역할 것: 줄을 생략하거나 요약하지 말고 1:1로 대응하게 번역할 것.
    3. 말투: 게임 캐릭터의 개성이 살아있는 자연스러운 한국어 구어체.
    4. 결과물에 설명이나 인사말은 절대 포함하지 말 것.
    5. 앞에 빈칸 유지
    
    [대상 내용]
    {batch_text}
    """
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"\n[에러 발생] 모델 {MODEL_ID} 호출 중 오류: {e}")
        raise #재시도 예외 발생

def start_translation():
    start_line = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            if content: 
                start_line = int(content)
                print(f">>> {start_line}행부터 번역을 재개")

    if not os.path.exists(INPUT_FILE):
        print(f"오류: {INPUT_FILE} 파일이 없습니다")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total = len(all_lines)

    #결과 파일은 'a' (추가) 모드로 열어 이어쓰기 가능
    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
        for i in range(start_line, total, BATCH_SIZE):
            batch = all_lines[i : i + BATCH_SIZE]
            batch_text = "".join(batch)

            print(f"진행 상황: {i}/{total} ({round(i/total*100, 1)}%)", end="\r")

            try:
                result = translate_batch(batch_text)
                if result:
                    out_f.write(result + "\n")
                    #성공 시 진행 상황 파일 갱신
                    with open(PROGRESS_FILE, "w") as p_f:
                        p_f.write(str(i + BATCH_SIZE))
                    
                    #API 리밋 짧은 대기
                    time.sleep(3) 
                else:
                    print(f"\n[주의] {i}행 번역 결과가 비어있습니다")
            except Exception as e:
                print(f"\n[중단] {i}행에서 재시도 후 실패: {e}")
                return

    print("\n[완료]")

start_translation()
