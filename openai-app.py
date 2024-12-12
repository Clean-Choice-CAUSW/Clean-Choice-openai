from flask import Flask, request, jsonify
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")

dto_path = "example.json"
dto_data = open(dto_path, "r").read()

# Helper function to call OpenAI API
def call_openai_api(model, messages, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"OpenAI API call failed: {response.text}")
    return response.json()

def build_system_message(message):
    return {"role": "system", "content": message}

def build_user_message(message):
    return {"role": "user", "content": message}

# Endpoint for genCompletion
@app.route("/gen-completion", methods=["POST"])
def gen_completion():
    request_data = request.get_json()
    html = request_data.get("html")
    imageUrlList = request_data.get("imageUrlList", [])
    
    # Example of how to build messages
    msg_text = dto_data + "\n위 형식 예시에 맞게 아래 건강기능상품 상세 페이지 html과 사진 속에서 정보를 추출해서 json dto로 넘겨줘."
    msg_text = msg_text + " 리스트는 예시라 원소 하나만 넣은거니까 상황에 맞게 여러 개 줘도 되고, 한글 정보는 영어를 번역하고, 없는 정보면 null로 채워줘\n"
    msg_text = msg_text + html
    messages = [
        build_user_message(msg_text),
    ]
    
    # Call OpenAI API
    try:
        response = call_openai_api("gpt-4o-mini", messages)
        content = response["choices"][0]["message"]["content"]

        json_start = content.find("```json")
        json_end = content.rfind("```")

        if json_start == -1 or json_end == -1 or json_start >= json_end:
            raise Exception("JSON not found in completion")
        
        json_data = content[json_start + len("```json"):json_end].strip()

        parsed_json = json.loads(json_data)
        print(parsed_json)
        result = {
            "name": parsed_json.get("name"),
            "productIngredientJoinLLMResponseDtoList": parsed_json.get("productIngredientJoinLLMResponseDtoList", []),
            "brandName": parsed_json.get("brandName"),
            "madeInCountry": parsed_json.get("madeInCountry"),
            "englishNetContent": parsed_json.get("englishNetContent"),
            "koreanNetContent": parsed_json.get("koreanNetContent"),
            "servingSize": parsed_json.get("servingSize"),
            "englishProductType": parsed_json.get("englishProductType"),
            "koreanProductType": parsed_json.get("koreanProductType"),
            "englishSupplementForm": parsed_json.get("englishSupplementForm"),
            "koreanSupplementForm": parsed_json.get("koreanSupplementForm"),
            "englishSuggestedUse": parsed_json.get("englishSuggestedUse"),
            "koreanSuggestedUse": parsed_json.get("koreanSuggestedUse"),
            "englishOtherIngredients": parsed_json.get("englishOtherIngredients"),
            "koreanOtherIngredients": parsed_json.get("koreanOtherIngredients"),
            "productLabelStatementLLMResponseDtoList": parsed_json.get("productLabelStatementLLMResponseDtoList", []),
            "imageUrl": parsed_json.get("imageUrl"),
            "price": parsed_json.get("price"),
            "priceUnit": parsed_json.get("priceUnit"),
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint for getAdvice
@app.route("/get-advice", methods=["POST"])
def get_advice():
    request_data = request.get_json()
    age = request_data.get("age")
    gender = request_data.get("gender")
    is_pregnant = request_data.get("isPregnant", False)
    intakeIngredientListString = request_data.get("intakeIngredientListString")
    selectIngredientListString = request_data.get("selectIngredientListString")
    question = request_data.get("question", "")

    # Build the question string
    question_builder = f"난 {age}살이고, 성별은 {gender}고 "
    if is_pregnant:
        question_builder += "임신 중이야."
    
    intakeIngredientFlag = False
    if intakeIngredientListString != "":
        question_builder += "그리고 다음 건강기능식품 성분을 섭취 중이야\n"
        question_builder += intakeIngredientListString
        intakeIngredientFlag = True

    selectIngredientFlag = False
    if selectIngredientListString != "":
        question_builder += "그리고 내가 지금 구매하려고 고민 중인 제품의 성분은 다음과 같아\n"
        question_builder += selectIngredientListString
        
        if intakeIngredientFlag:
            question_builder += "\n내가 지금 섭취 중인 성분 토대로 구매하려는 성분에 대한 병용 시 주의사항 및 조언 알려줘\n"
        else:
            question_builder += "\n내가 지금 섭취 중인 성분이 없어서, 구매하려는 성분에 대한 병용 시 주의사항 및 조언 알려줘\n"
        
        selectIngredientFlag = True

    question_builder += "내 정보를 기반으로 건강기능식품 선택 시 주의사항 및 조언"
    if intakeIngredientFlag and not selectIngredientFlag:
        question_builder += ", 그리고 내가 지금 복용하고 있는 성분에 대한 주의사항 및 조언을 알려줘"
    else:
        question_builder += "을 알려줘"

    if question:
        question_builder += f"마지막으로 질문이 있는데 따로 답변해줘\n질문: {question}"
    print(question_builder)

    # Call OpenAI API
    messages = [
        build_user_message(question_builder)
    ]
    try:
        response = call_openai_api("gpt-4o", messages)
        content = response["choices"][0]["message"]["content"]
        content = content.replace("*", "").replace("#", "")
        return content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port = 15001)