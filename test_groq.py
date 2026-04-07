import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

#테스트 용, 나중에 지울 예정

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    messages=[
        {"role": "system", "content": "너는 뉴스 요약 도우미다."},
        {"role": "user", "content": "환율이 오를 때 대학생에게 어떤 영향이 있는지 3문장으로 설명해줘."}
    ],
    temperature=0.2,
)

print(response.choices[0].message.content)