# 실행방법

root directory에 `.env`파일 만들기
아래 내용 채워넣기(key 등에 알맞은 키 넣기)
```
OPENAI_API_KEY={API_KEY}
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
```

```bash
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ python app.py
```
