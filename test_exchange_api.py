from dotenv import load_dotenv
load_dotenv()
import os
print("URL:", os.getenv("KOREAEXIM_API_URL"))
print("KEY:", os.getenv("KOREAEXIM_API_KEY"))