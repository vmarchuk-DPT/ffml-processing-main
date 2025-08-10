import requests
import random
import time
from faker import Faker
import uuid

fake = Faker()

BASE_URL = "http://localhost:8000"  # порт второго сервиса — ffml-preprocess-main

def post_to_ffml_process(survey_version: int):
    url = f'{BASE_URL}/{survey_version}'
    print(url)
    response = requests.get(f"{BASE_URL}/{survey_version}", )
    print("\n🔹 POST / to ffml-process-mains")
    print(f"survey_version: {survey_version}")
    print("Status code:", response.status_code)
    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text)


if __name__ == "__main__":
    print("🚀 Отправляем тест в ffml-process-main...")
    post_to_ffml_process(18)



