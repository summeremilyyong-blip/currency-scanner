import os
import tempfile
from datetime import datetime

import requests
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from inference import get_model


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

if not API_KEY:
    raise ValueError(
        "ไม่พบ ROBOFLOW_API_KEY ในไฟล์ .env"
    )

if not MODEL_ID:
    raise ValueError(
        "ไม่พบ MODEL_ID ในไฟล์ .env"
    )


# =========================================================
# LOAD ROBOFLOW MODEL
# =========================================================

print("====================================")
print("Loading Roboflow model...")
print("====================================")

model = get_model(
    model_id=MODEL_ID,
    api_key=API_KEY
)

print("Roboflow model loaded!")
print("====================================")


# =========================================================
# FASTAPI
# =========================================================

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


# =========================================================
# BANKNOTE DATABASE
# =========================================================

BANKNOTES = {

    # -------------------------
    # JAPANESE YEN
    # -------------------------

    "1000 yen": {
        "currency": "JPY",
        "currency_name": "Japanese Yen",
        "symbol": "¥",
        "amount": 1000,
        "country": "Japan",
        "flag": "🇯🇵"
    },

    "2000 yen": {
        "currency": "JPY",
        "currency_name": "Japanese Yen",
        "symbol": "¥",
        "amount": 2000,
        "country": "Japan",
        "flag": "🇯🇵"
    },

    "5000 yen": {
        "currency": "JPY",
        "currency_name": "Japanese Yen",
        "symbol": "¥",
        "amount": 5000,
        "country": "Japan",
        "flag": "🇯🇵"
    },

    "10000 yen": {
        "currency": "JPY",
        "currency_name": "Japanese Yen",
        "symbol": "¥",
        "amount": 10000,
        "country": "Japan",
        "flag": "🇯🇵"
    },


    # -------------------------
    # THAI BAHT
    # -------------------------

    "20 baht": {
        "currency": "THB",
        "currency_name": "Thai Baht",
        "symbol": "฿",
        "amount": 20,
        "country": "Thailand",
        "flag": "🇹🇭"
    },

    "50 baht": {
        "currency": "THB",
        "currency_name": "Thai Baht",
        "symbol": "฿",
        "amount": 50,
        "country": "Thailand",
        "flag": "🇹🇭"
    },

    "100 baht": {
        "currency": "THB",
        "currency_name": "Thai Baht",
        "symbol": "฿",
        "amount": 100,
        "country": "Thailand",
        "flag": "🇹🇭"
    },

    "500 baht": {
        "currency": "THB",
        "currency_name": "Thai Baht",
        "symbol": "฿",
        "amount": 500,
        "country": "Thailand",
        "flag": "🇹🇭"
    },

    "1000 baht": {
        "currency": "THB",
        "currency_name": "Thai Baht",
        "symbol": "฿",
        "amount": 1000,
        "country": "Thailand",
        "flag": "🇹🇭"
    }
}


# =========================================================
# EXCHANGE RATE
# =========================================================

def get_exchange_rate(
    from_currency: str,
    to_currency: str
):

    if from_currency == to_currency:
        return 1.0, datetime.now()

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

    rate = float(
        data["rates"][to_currency]
    )

    rate_date = datetime.strptime(
        data["date"],
        "%Y-%m-%d"
    )

    return rate, rate_date


# =========================================================
# DETECTION
# =========================================================

@app.post("/detect")
async def detect(
    file: UploadFile = File(...)
):

    temp_path = None

    try:

        # =================================================
        # SAVE IMAGE
        # =================================================

        suffix = os.path.splitext(
            file.filename or ".jpg"
        )[1]

        if not suffix:
            suffix = ".jpg"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:

            image_data = await file.read()

            temp.write(image_data)

            temp_path = temp.name


        # =================================================
        # ROBoflow INFERENCE
        # =================================================

        print("Running detection...")

        results = model.infer(
            temp_path,
            confidence=0.25
        )

        if not results:

            return {
                "success": False,
                "message": "ไม่พบผลลัพธ์จากโมเดล"
            }


        result = results[0]


        # =================================================
        # GET PREDICTIONS
        # =================================================

        predictions = result.predictions


        if not predictions:

            return {
                "success": False,
                "message": "ไม่พบธนบัตรในภาพ"
            }


        # =================================================
        # BEST PREDICTION
        # =================================================

        best_prediction = max(
            predictions,
            key=lambda p: float(p.confidence)
        )


        class_name = str(
            best_prediction.class_name
        )

        confidence = float(
            best_prediction.confidence
        )


        print(
            f"Detected: {class_name}"
        )

        print(
            f"Confidence: {confidence:.2%}"
        )


        # =================================================
        # BANKNOTE LOOKUP
        # =================================================

        banknote = BANKNOTES.get(
            class_name.lower().strip()
        )


        if banknote is None:

            return {

                "success": False,

                "message":
                    "ตรวจพบธนบัตร แต่ไม่รู้จักชนิดนี้",

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


        # =================================================
        # EXCHANGE VARIABLES
        # =================================================

        exchange_rate = None

        converted_amount = None

        target_currency = None

        rate_date = None

        rate_time = None


        # =================================================
        # JPY → THB
        # =================================================

        if from_currency == "JPY":

            target_currency = "THB"

            try:

                exchange_rate, rate_datetime = (
                    get_exchange_rate(
                        "JPY",
                        "THB"
                    )
                )

                converted_amount = (
                    amount *
                    exchange_rate
                )

                rate_date = (
                    rate_datetime.strftime(
                        "%Y-%m-%d"
                    )
                )

                rate_time = (
                    datetime.now().strftime(
                        "%H:%M:%S"
                    )
                )

            except Exception as e:

                print(
                    "Exchange rate error:",
                    repr(e)
                )


        # =================================================
        # THB → JPY
        # =================================================

        elif from_currency == "THB":

            target_currency = "JPY"

            try:

                exchange_rate, rate_datetime = (
                    get_exchange_rate(
                        "THB",
                        "JPY"
                    )
                )

                converted_amount = (
                    amount *
                    exchange_rate
                )

                rate_date = (
                    rate_datetime.strftime(
                        "%Y-%m-%d"
                    )
                )

                rate_time = (
                    datetime.now().strftime(
                        "%H:%M:%S"
                    )
                )

            except Exception as e:

                print(
                    "Exchange rate error:",
                    repr(e)
                )


        # =================================================
        # RESULT
        # =================================================

        return {

            "success": True,

            "class": class_name,

            "confidence": round(
                confidence * 100,
                2
            ),

            "currency":
                from_currency,

            "currency_name":
                banknote["currency_name"],

            "symbol":
                banknote["symbol"],

            "country":
                banknote["country"],

            "flag":
                banknote["flag"],

            "amount":
                amount,

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

            "rate_time":
                rate_time
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

        # =================================================
        # DELETE TEMP IMAGE
        # =================================================

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(temp_path)


# =========================================================
# WEBSITE
# =========================================================

app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static"
)


@app.get("/")
def home():

    return FileResponse(
        "static/index.html"
    )