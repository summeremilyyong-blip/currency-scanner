// =====================================================
// ELEMENTS
// =====================================================

const imageInput = document.getElementById("imageInput");
const previewContainer = document.getElementById("previewContainer");
const preview = document.getElementById("preview");
const scanButton = document.getElementById("scanButton");
const result = document.getElementById("result");
const loading = document.getElementById("loading");

const camera = document.getElementById("camera");
const cameraContainer = document.getElementById("cameraContainer");
const cameraButton = document.getElementById("cameraButton");
const captureButton = document.getElementById("captureButton");
const switchCameraButton = document.getElementById("switchCameraButton");
const newScanButton = document.getElementById("newScanButton");

// =====================================================
// RESULT ELEMENTS
// =====================================================

const currencyName = document.getElementById("currencyName");
const amount = document.getElementById("amount");
const confidence = document.getElementById("confidence");
const confidenceBar = document.getElementById("confidenceBar");
const flag = document.getElementById("flag");

const exchangeRate = document.getElementById("exchangeRate");
const converted = document.getElementById("converted");
const rateDate = document.getElementById("rateDate");
const rateTime = document.getElementById("rateTime");

const currencyCode = document.getElementById("currencyCode");
const country = document.getElementById("country");
const targetCurrency = document.getElementById("targetCurrency");

// =====================================================
// VARIABLES
// =====================================================

let selectedFile = null;
let cameraStream = null;
let currentFacingMode = "environment";

// =====================================================
// FORMAT MONEY
// =====================================================

function formatMoney(value, decimals = 2) {
    return Number(value).toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// =====================================================
// GET COUNTRY
// =====================================================

function getCountry(currency) {

    if (currency === "JPY") {
        return "Japan";
    }

    if (currency === "THB") {
        return "Thailand";
    }

    return "-";
}

// =====================================================
// GET CURRENCY SYMBOL
// =====================================================

function getCurrencySymbol(currency) {

    if (currency === "JPY") {
        return "¥";
    }

    if (currency === "THB") {
        return "฿";
    }

    return "";
}

// =====================================================
// START CAMERA
// =====================================================

async function startCamera() {

    try {

        if (!navigator.mediaDevices) {

            alert(
                "กล้องไม่สามารถใช้งานบน browser นี้ได้"
            );

            return;
        }

        if (cameraStream) {

            cameraStream
                .getTracks()
                .forEach(track => track.stop());

        }

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: {

                    facingMode: currentFacingMode,

                    width: {
                        ideal: 1280
                    },

                    height: {
                        ideal: 720
                    }

                },

                audio: false

            });

        camera.srcObject = cameraStream;

        await camera.play();

        cameraContainer.style.display = "block";

        captureButton.style.display = "block";

        switchCameraButton.style.display = "block";

        cameraButton.textContent =
            "⏹ Stop Camera";

    }

    catch (error) {

        console.error(
            "Camera error:",
            error
        );

        alert(
            "ไม่สามารถเปิดกล้องได้\n\n" +
            "กรุณาอนุญาต Camera ใน browser"
        );

    }

}

// =====================================================
// STOP CAMERA
// =====================================================

function stopCamera() {

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(track => track.stop());

        cameraStream = null;

    }

    camera.srcObject = null;

    cameraContainer.style.display = "none";

    captureButton.style.display = "none";

    switchCameraButton.style.display = "none";

    cameraButton.textContent =
        "📷 Start Camera";
}

// =====================================================
// CAMERA BUTTON
// =====================================================

cameraButton.addEventListener(
    "click",
    async function () {

        if (cameraStream) {

            stopCamera();

        } else {

            await startCamera();

        }

    }
);

// =====================================================
// SWITCH CAMERA
// =====================================================

switchCameraButton.addEventListener(
    "click",
    async function () {

        if (!cameraStream) {
            return;
        }

        currentFacingMode =
            currentFacingMode === "environment"
                ? "user"
                : "environment";

        await startCamera();

    }
);

// =====================================================
// CAPTURE CAMERA IMAGE
// =====================================================

captureButton.addEventListener(
    "click",
    async function () {

        if (!cameraStream) {

            alert(
                "กรุณาเปิดกล้องก่อน"
            );

            return;
        }

        const canvas =
            document.createElement("canvas");

        canvas.width =
            camera.videoWidth;

        canvas.height =
            camera.videoHeight;

        const context =
            canvas.getContext("2d");

        context.drawImage(
            camera,
            0,
            0,
            canvas.width,
            canvas.height
        );

        canvas.toBlob(
            async function (blob) {

                if (!blob) {

                    alert(
                        "ไม่สามารถจับภาพจากกล้องได้"
                    );

                    return;
                }

                const file =
                    new File(
                        [blob],
                        "camera-scan.jpg",
                        {
                            type: "image/jpeg"
                        }
                    );

                selectedFile = file;

                preview.src =
                    URL.createObjectURL(file);

                previewContainer.style.display =
                    "block";

                await scanFile(file);

            },
            "image/jpeg",
            0.92
        );

    }
);

// =====================================================
// IMAGE UPLOAD
// =====================================================

imageInput.addEventListener(
    "change",
    function () {

        const file = this.files[0];

        if (!file) {
            return;
        }

        selectedFile = file;

        preview.src =
            URL.createObjectURL(file);

        previewContainer.style.display =
            "block";

        result.style.display =
            "none";

        scanButton.style.display =
            "block";

        loading.style.display =
            "none";

    }
);

// =====================================================
// UPLOAD SCAN BUTTON
// =====================================================

scanButton.addEventListener(
    "click",
    async function () {

        if (!selectedFile) {

            alert(
                "Please choose an image first."
            );

            return;
        }

        await scanFile(selectedFile);

    }
);

// =====================================================
// SCAN FILE
// =====================================================

async function scanFile(file) {

    try {

        result.style.display = "none";

        loading.style.display = "block";

        scanButton.disabled = true;

        captureButton.disabled = true;

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        console.log(
            "Sending image to server..."
        );

        const response =
            await fetch(
                "/detect",
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!response.ok) {

            const text =
                await response.text();

            console.error(
                "Server error:",
                response.status,
                text
            );

            throw new Error(
                "Server returned HTTP " +
                response.status
            );

        }

        const data =
            await response.json();

        console.log(
            "Server response:",
            data
        );

        if (!data.success) {

            alert(
                data.message ||
                "ไม่พบธนบัตร"
            );

            return;
        }

        // =================================================
        // DISPLAY RESULT
        // =================================================

        result.style.display = "block";

        // =================================================
        // CURRENCY NAME
        // =================================================

        currencyName.textContent =
            data.currency_name ||
            data.currency ||
            "-";

        // =================================================
        // FLAG
        // =================================================

        flag.textContent =
            data.flag ||
            (
                data.currency === "JPY"
                    ? "🇯🇵"
                    : data.currency === "THB"
                        ? "🇹🇭"
                        : "💵"
            );

        // =================================================
        // AMOUNT
        // =================================================

        const symbol =
            getCurrencySymbol(
                data.currency
            );

        amount.textContent =
            symbol +
            formatMoney(
                data.amount,
                0
            );

        // =================================================
        // CONFIDENCE
        // =================================================

        const confidenceValue =
            Number(
                data.confidence || 0
            );

        confidence.textContent =
            confidenceValue.toFixed(2) +
            "%";

        confidenceBar.style.width =
            Math.min(
                confidenceValue,
                100
            ) + "%";

        // =================================================
        // DETAILS
        // =================================================

        currencyCode.textContent =
            data.currency || "-";

        country.textContent =
            data.country ||
            getCountry(data.currency);

        targetCurrency.textContent =
            data.target_currency ||
            "-";

        // =================================================
        // EXCHANGE RATE
        // =================================================

        if (
            data.exchange_rate !== null &&
            data.exchange_rate !== undefined &&
            data.converted_amount !== null &&
            data.converted_amount !== undefined
        ) {

            exchangeRate.textContent =
                "1 " +
                data.currency +
                " = " +
                Number(
                    data.exchange_rate
                ).toFixed(6) +
                " " +
                data.target_currency;

            const targetSymbol =
                getCurrencySymbol(
                    data.target_currency
                );

            converted.textContent =
                "≈ " +
                targetSymbol +
                formatMoney(
                    data.converted_amount,
                    2
                );

            rateDate.textContent =
                data.rate_date || "-";

            rateTime.textContent =
                data.rate_time || "-";

        }

        else {

            exchangeRate.textContent =
                "Exchange rate unavailable";

            converted.textContent =
                "—";

            rateDate.textContent =
                "-";

            rateTime.textContent =
                "-";

        }

        // =================================================
        // SCROLL TO RESULT
        // =================================================

        result.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }

    catch (error) {

        console.error(
            "Connection error:",
            error
        );

        alert(
            "เกิดข้อผิดพลาดในการเชื่อมต่อ Server\n\n" +
            "กรุณาตรวจสอบว่า Server กำลังทำงานอยู่"
        );

    }

    finally {

        loading.style.display = "none";

        scanButton.disabled = false;

        captureButton.disabled = false;

    }

}

// =====================================================
// NEW SCAN
// =====================================================

newScanButton.addEventListener(
    "click",
    function () {

        selectedFile = null;

        imageInput.value = "";

        preview.src = "";

        previewContainer.style.display =
            "none";

        scanButton.style.display =
            "none";

        result.style.display =
            "none";

        loading.style.display =
            "none";

        confidenceBar.style.width =
            "0%";

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }
);

// =====================================================
// CLEAN CAMERA WHEN LEAVING PAGE
// =====================================================

window.addEventListener(
    "beforeunload",
    function () {

        stopCamera();

    }
);