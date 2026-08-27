import os
import tempfile
from datetime import datetime

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from inference_sdk import InferenceHTTPClient


# ==========================================
# LOAD ENV
# ==========================================

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")
ROBOFLOW_API_URL = os.getenv(
    "ROBOFLOW_API_URL",
    "https://serverless.roboflow.com"
)

if not ROBOFLOW_API_KEY:
    raise ValueError("ไม่พบ ROBOFLOW_API_KEY ใน .env")

if not MODEL_ID:
    raise ValueError("ไม่พบ MODEL_ID ใน .env")


# ==========================================
# ROBOFLOW CLIENT
# ==========================================

client = InferenceHTTPClient(
    api_url=ROBOFLOW_API_URL,
    api_key=ROBOFLOW_API_KEY
)


# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="Currency Scanner",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# BANKNOTE DATA
# ==========================================

BANKNOTES = {

    "1000 yen": {
        "currency": "JPY",
        "amount": 1000,
        "name": "Japanese Yen",
        "country": "Japan",
        "symbol": "¥",
        "flag": "🇯🇵"
    },

    "2000 yen": {
        "currency": "JPY",
        "amount": 2000,
        "name": "Japanese Yen",
        "country": "Japan",
        "symbol": "¥",
        "flag": "🇯🇵"
    },

    "5000 yen": {
        "currency": "JPY",
        "amount": 5000,
        "name": "Japanese Yen",
        "country": "Japan",
        "symbol": "¥",
        "flag": "🇯🇵"
    },

    "10000 yen": {
        "currency": "JPY",
        "amount": 10000,
        "name": "Japanese Yen",
        "country": "Japan",
        "symbol": "¥",
        "flag": "🇯🇵"
    },

    "20 baht": {
        "currency": "THB",
        "amount": 20,
        "name": "Thai Baht",
        "country": "Thailand",
        "symbol": "฿",
        "flag": "🇹🇭"
    },

    "50 baht": {
        "currency": "THB",
        "amount": 50,
        "name": "Thai Baht",
        "country": "Thailand",
        "symbol": "฿",
        "flag": "🇹🇭"
    },

    "100 baht": {
        "currency": "THB",
        "amount": 100,
        "name": "Thai Baht",
        "country": "Thailand",
        "symbol": "฿",
        "flag": "🇹🇭"
    },

    "500 baht": {
        "currency": "THB",
        "amount": 500,
        "name": "Thai Baht",
        "country": "Thailand",
        "symbol": "฿",
        "flag": "🇹🇭"
    },

    "1000 baht": {
        "currency": "THB",
        "amount": 1000,
        "name": "Thai Baht",
        "country": "Thailand",
        "symbol": "฿",
        "flag": "🇹🇭"
    }
}


# ==========================================
# EXCHANGE RATE
# ==========================================

def get_exchange_rate(
    from_currency: str,
    to_currency: str
):

    if from_currency == to_currency:

        return {
            "rate": 1.0,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

    url = (
        "https://api.frankfurter.app/latest"
        f"?from={from_currency}"
        f"&to={to_currency}"
    )

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return {
        "rate": float(
            data["rates"][to_currency]
        ),
        "date": data.get(
            "date",
            datetime.now().strftime("%Y-%m-%d")
        )
    }


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
async def home():

    return FileResponse(
        "static/index.html"
    )


# ==========================================
# DETECT BANKNOTE
# ==========================================

@app.post("/detect")
async def detect(
    file: UploadFile = File(...)
):

    temp_path = None

    try:

        # --------------------------------------
        # SAVE IMAGE
        # --------------------------------------

        suffix = os.path.splitext(
            file.filename or ".jpg"
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:

            image_data = await file.read()

            temp.write(image_data)

            temp_path = temp.name


        # --------------------------------------
        # ROBOFLOW
        # --------------------------------------

        result = client.infer(
            temp_path,
            model_id=MODEL_ID
        )


        # --------------------------------------
        # GET PREDICTIONS
        # --------------------------------------

        predictions = result.get(
            "predictions",
            []
        )

        if not predictions:

            return {
                "success": False,
                "message": "ไม่พบธนบัตรในภาพ"
            }


        # --------------------------------------
        # BEST PREDICTION
        # --------------------------------------

        best_prediction = max(
            predictions,
            key=lambda p: p.get(
                "confidence",
                0
            )
        )

        class_name = best_prediction.get(
            "class",
            ""
        )

        confidence = float(
            best_prediction.get(
                "confidence",
                0
            )
        )


        # --------------------------------------
        # BANKNOTE INFO
        # --------------------------------------

        banknote = BANKNOTES.get(
            class_name.lower()
        )

        if banknote is None:

            return {

                "success": False,

                "message":
                    "ตรวจพบวัตถุ แต่ไม่รู้จักธนบัตร",

                "class":
                    class_name,

                "confidence":
                    round(
                        confidence * 100,
                        2
                    )
            }


        from_currency = banknote["currency"]

        amount = banknote["amount"]

        symbol = banknote["symbol"]

        country = banknote["country"]


        # ======================================
        # TARGET CURRENCY
        # ======================================

        if from_currency == "JPY":

            target_currency = "THB"

        else:

            target_currency = "JPY"


        # ======================================
        # EXCHANGE
        # ======================================

        exchange_rate = None

        converted_amount = None

        rate_date = None


        try:

            rate_data = get_exchange_rate(
                from_currency,
                target_currency
            )

            exchange_rate = rate_data["rate"]

            rate_date = rate_data["date"]

            converted_amount = (
                amount * exchange_rate
            )

        except Exception as e:

            print(
                "Exchange rate error:",
                e
            )


        # ======================================
        # CURRENT TIME
        # ======================================

        now = datetime.now()

        current_date = now.strftime(
            "%Y-%m-%d"
        )

        current_time = now.strftime(
            "%H:%M:%S"
        )


        # ======================================
        # RESPONSE
        # ======================================

        return {

            "success": True,

            "class":
                class_name,

            "currency":
                from_currency,

            "currency_name":
                banknote["name"],

            "country":
                country,

            "symbol":
                symbol,

            "flag":
                banknote["flag"],

            "amount":
                amount,

            "confidence":
                round(
                    confidence * 100,
                    2
                ),

            "target_currency":
                target_currency,

            "exchange_rate":
                round(
                    exchange_rate,
                    6
                )
                if exchange_rate is not None
                else None,

            "converted_amount":
                round(
                    converted_amount,
                    2
                )
                if converted_amount is not None
                else None,

            "rate_date":
                rate_date,

            "checked_date":
                current_date,

            "checked_time":
                current_time
        }


    except Exception as e:

        print(
            "Detection error:",
            repr(e)
        )

        return {

            "success": False,

            "message":
                "เกิดข้อผิดพลาดในการประมวลผล",

            "error":
                str(e)
        }


    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(
                temp_path
            )


# ==========================================
# STATIC FILES
# ==========================================

app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static"
)