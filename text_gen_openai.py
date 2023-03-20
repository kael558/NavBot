"""curl https://api.openai.com/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "text-davinci-003",
    "prompt": "Say this is a test",
    "max_tokens": 7,
    "temperature": 0
  }'
  response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        best_of=3
    )
    return response.choices[0].text
"""
import json
import os

import requests
from dotenv import load_dotenv


def generate(**kwargs):
    # Write a request to the OpenAI API with the prompt and parameters

    headers = {
        "Content-Type": "application/json",
        "Authorization":  "Bearer " + os.environ.get("OPENAI_API_KEY")
    }
    data = json.dumps({"model": "text-davinci-003",**kwargs})

    response = requests.post("https://api.openai.com/v1/completions",
                             data=data,
                             headers=headers,
                             timeout=20
                             )

    return response.json()['choices'][0]['text']

if __name__ == "__main__":
    load_dotenv()
    print(generate("Say this is a test", 0.5, 3, 50))

