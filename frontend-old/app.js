/* =========================================================
   AEGIS COMMAND CENTER
   Frontend Application
========================================================= */

const API_URL = "http://127.0.0.1:8000";


/* =========================================================
   CLOCK
========================================================= */

function updateClock() {

    const element =
        document.getElementById("currentTime");

    if (!element) return;

    const now = new Date();

    element.textContent =
        "• " +
        now.toLocaleDateString() +
        " " +
        now.toLocaleTimeString();

}

updateClock();

setInterval(updateClock, 1000);


/* =========================================================
   LOAD BACKEND STATUS
========================================================= */

async function loadBackendStatus() {

    try {

        const response =
            await fetch(`${API_URL}/`);

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data =
            await response.json();

        console.log(
            "AEGIS Backend:",
            data
        );

    } catch (error) {

        console.error(
            "Backend connection failed:",
            error
        );

    }

}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadBackendStatus();

        console.log(
            "AEGIS Command Center initialized."
        );

    }
);