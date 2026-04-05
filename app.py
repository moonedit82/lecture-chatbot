import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import anthropic

# .env 파일에서 API 키 로드
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# lecture_content.txt 로드 (앱과 같은 폴더 또는 환경변수 경로)
CONTENT_FILE = os.environ.get(
    "LECTURE_CONTENT_PATH",
    os.path.join(os.path.dirname(__file__), "lecture_content.txt")
)

print(f"강의 자료 파일 로드 중: {CONTENT_FILE}")
with open(CONTENT_FILE, encoding="utf-8") as f:
    DOCUMENT_CONTENT = f.read()
print(f"로드 완료. 총 {len(DOCUMENT_CONTENT):,} 글자")

SYSTEM_PROMPT = f"""당신은 강의 자료 기반 Q&A 챗봇입니다.

아래 강의 자료의 내용을 바탕으로만 학생의 질문에 답변하세요.
자료에 없는 내용은 절대 추측하거나 일반 지식으로 답변하지 말고,
"강의 자료에 없습니다."라고 안내하세요.

답변 규칙:
1. 반드시 강의 자료에 있는 내용만 답변합니다
2. 자료에 없는 내용은 "강의 자료에 없습니다."라고 말합니다
3. 한국어로 친절하고 이해하기 쉽게 답변합니다
4. 어느 파일/슬라이드에서 나온 내용인지 언급하면 좋습니다
5. 답변은 핵심 위주로 명확하게 합니다

=== 강의 자료 전체 내용 ===
{DOCUMENT_CONTENT}
"""

TEMPLATE = os.environ.get("TEMPLATE_STYLE", "pinterest")

@app.route("/")
def index():
    if TEMPLATE == "classic":
        return render_template("index_classic.html")
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "잘못된 요청입니다"}), 400

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "메시지가 없습니다"}), 400

    api_key = ANTHROPIC_API_KEY or data.get("api_key", "")
    if not api_key:
        return jsonify({"error": "API 키가 설정되지 않았습니다"}), 400

    def generate():
        try:
            client = anthropic.Anthropic(api_key=api_key)
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            ) as stream:
                for text in stream.text_stream:
                    safe = text.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"
        except anthropic.AuthenticationError:
            yield "data: ⚠️ API 키가 올바르지 않습니다.\\n\n\n"
        except anthropic.RateLimitError:
            yield "data: ⚠️ API 사용 한도 초과입니다. 잠시 후 다시 시도해주세요.\\n\n\n"
        except Exception as e:
            yield f"data: ⚠️ 오류: {str(e)[:100]}\\n\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

if __name__ == "__main__":
    print("\n챗봇 서버 시작!")
    print("브라우저에서 http://localhost:5000 을 열어주세요\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
