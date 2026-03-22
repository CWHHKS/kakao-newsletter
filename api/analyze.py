import json
import base64
import io
import os
import sys

# Add parent directory to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUMMARY_PROMPT = """당신은 경제·시사 뉴스레터 전문 에디터입니다.
이미지는 신문/뉴스레터 스캔본입니다. 아래 형식을 정확히 따르세요.

[출력 형식]

<YYYY년 M월D일 뉴스>

1. [분야/세부분야] 헤드라인 1줄 요약
2. [분야/세부분야] 헤드라인 1줄 요약
(기사 전체 목차)

▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

1. [분야/세부분야] 헤드라인 1줄 요약
① 핵심: 핵심 사실 1~2문장.
② 포인트: 주목할 시장·경제적 포인트 1~2문장.
③ 시사점: 행동·판단에 참고할 인사이트 1~2문장.
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

2. [분야/세부분야] 헤드라인 1줄 요약
① 핵심: ...
② 포인트: ...
③ 시사점: ...
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

(모든 기사를 빠짐없이 반복)

[규칙]
- 날짜는 이미지에서 추출, 없으면 오늘 날짜
- 분야: [정치][경제][금융][증권][기업][국제][생활][기술][스포츠] + /세부
- ▔ 구분선(25개)은 각 기사 아래 반드시 삽입
- 목차(번호 목록)와 본문(①②③) 두 파트 모두 작성
- 한국어. 길이 제한 없음 — 기사 전부 포함"""


def handler(request):
    """Vercel Python Serverless Function"""
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    }

    if request.method == "OPTIONS":
        return ("", 200, headers)

    if request.method != "POST":
        return (json.dumps({"error": "POST only"}), 405, headers)

    try:
        import google.generativeai as genai
        import PIL.Image

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return (json.dumps({"error": "GEMINI_API_KEY 환경변수가 설정되지 않았습니다."}), 400, headers)

        # 파일 업로드 처리
        if request.content_type and "multipart" in request.content_type:
            file = request.files.get("file")
            if not file:
                return (json.dumps({"error": "파일이 없습니다."}), 400, headers)
            img = PIL.Image.open(file.stream)
        else:
            data = request.get_json() or {}
            b64 = data.get("image_b64", "")
            if not b64:
                return (json.dumps({"error": "이미지가 없습니다."}), 400, headers)
            img_bytes = base64.b64decode(b64)
            img = PIL.Image.open(io.BytesIO(img_bytes))

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content([SUMMARY_PROMPT, img])
        text = response.text.strip()

        return (json.dumps({"result": text}, ensure_ascii=False), 200, headers)

    except Exception as e:
        return (json.dumps({"error": str(e)}, ensure_ascii=False), 500, headers)
