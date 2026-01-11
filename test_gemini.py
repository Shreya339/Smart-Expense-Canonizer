import google.generativeai as genai

genai.configure(api_key="")

model = genai.GenerativeModel("gemini-2.5-flash")

resp = model.generate_content("Return only the word hello")
print(resp.text)
