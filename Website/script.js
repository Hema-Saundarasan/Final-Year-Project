// ================= CHANNEL INFO =================

const envChannelID = "3405341";
const envReadAPI = "C338S3QR2F0DZ1XN";

const attChannelID = "3409092";
const attReadAPI = "XWAARJK732ZX2TYN";

// ================= STUDENTS =================

const studentNames = {
    "1": "Muhammad Ali",
    "201": "JeyaKumar Saravanan",
    "251": "Joseph Vijay",
    "258": "Sri",
    "322": "Adriana Sarah Binti Ahmad Faiza"
};

// ================= LABELS =================

function statusLabel(code) {
    switch (parseInt(code)) {
        case 1: return "Present";
        case 2: return "Duplicate Entry";
        case 3: return "Unauthorized";
        case 9: return "Ride Ended";
        default: return "--";
    }
}

function routeLabel(routeNum) {
    switch (parseInt(routeNum)) {
        case 1: return "Home to School";
        case 2: return "School to Home";
        default: return "--";
    }
}

// ================= MAIN FUNCTION =================

async function loadData() {

    try {
        // Fetch Environment Channel Data
        let envResponse = await fetch(
            `https://api.thingspeak.com/channels/${envChannelID}/feeds.json?api_key=${envReadAPI}&results=20`
        );
        let envData = await envResponse.json();
        let envFeeds = envData.feeds || [];

        // Fetch Attendance Channel Data
        let attResponse = await fetch(
            `https://api.thingspeak.com/channels/${attChannelID}/feeds.json?api_key=${attReadAPI}&results=20`
        );
        let attData = await attResponse.json();
        let attFeeds = attData.feeds || [];

        // ================= ENVIRONMENT PROCESSING =================
        let envFeed = [...envFeeds]
            .reverse()
            .find(f => f.field1 !== null);

        if (envFeed) {
            document.getElementById("temp").innerHTML =
                "🌡 Temperature: " + envFeed.field1 + " °C";

            document.getElementById("hum").innerHTML =
                "💧 Humidity: " + envFeed.field2 + " %";

            document.getElementById("gas").innerHTML =
                "☁ Gas Level: " + envFeed.field3;
        } else {
            document.getElementById("temp").innerHTML = "🌡 Temperature: --";
            document.getElementById("hum").innerHTML = "💧 Humidity: --";
            document.getElementById("gas").innerHTML = "☁ Gas Level: --";
        }

        // ================= ATTENDANCE PROCESSING =================
        let attendanceFeed = [...attFeeds]
            .reverse()
            .find(f => f.field4 !== null);

        if (attendanceFeed) {
            document.getElementById("route").innerHTML =
                "🛣 Route: " + routeLabel(attendanceFeed.field5);

            let studentID = attendanceFeed.field4 || "--";
            let studentName = studentNames[studentID] || "--";
                
            document.getElementById("studentid").innerHTML =
                "🪪 Student ID: " + studentID;
            
            document.getElementById("studentname").innerHTML =
                "👤 Student Name: " + studentName;

            document.getElementById("status_code").innerHTML =
                "📋 Status: " + statusLabel(attendanceFeed.field6);
        } else {
            document.getElementById("route").innerHTML = "🛣 Route: --";
            document.getElementById("studentid").innerHTML = "🪪 Student ID: --";
            document.getElementById("studentname").innerHTML = "👤 Student Name: --";
            document.getElementById("status_code").innerHTML = "📋 Status: --";
        }

        // ================= RIDE SUMMARY PROCESSING =================
        // Find the absolute latest entry that contains a status code
        let latestStatusFeed = [...attFeeds]
            .reverse()
            .find(f => f.field6 !== null);

        // Display summary ONLY if the absolute latest state is "Ride Ended" (code 9)
        if (latestStatusFeed && parseInt(latestStatusFeed.field6) === 9) {
            
            document.getElementById("rideStatus").innerHTML =
                "Ride: Ride Ended ✅";

            document.getElementById("rideRoute").innerHTML =
                "Route: " + routeLabel(latestStatusFeed.field5);

            document.getElementById("rideTotal").innerHTML =
                "Total Students: " + (latestStatusFeed.field7 || "0");

            // CLEAR HISTORY: Isolate feeds belonging only to this specific trip
            // 1. Find the index where this trip ended
            let endIdx = attFeeds.indexOf(latestStatusFeed);
            
            // 2. Look backwards from the end index to find where the previous ride ended (if any)
            let startIdx = 0;
            for (let i = endIdx - 1; i >= 0; i--) {
                if (parseInt(attFeeds[i].field6) === 9) {
                    startIdx = i + 1; // The current trip starts right after the old trip's end
                    break;
                }
            }

            // 3. Extract only the entries within this specific trip's window
            let currentTripFeeds = attFeeds.slice(startIdx, endIdx + 1);

            // Filter unique present students from the current trip window only
            let presentStudents = [...new Set(
                currentTripFeeds
                    .filter(f => parseInt(f.field6) === 1 && f.field4)
                    .map(f => f.field4)
            )];

            let list = presentStudents
                .map(id => `${id} - ${studentNames[id] || "Unknown"}`)
                .join("<br>");

            document.getElementById("rideList").innerHTML =
                "Present Students:<br>" + (list || "--");
        } else {
            // Hide everything if button C hasn't been pressed or a new ride has started
            document.getElementById("rideStatus").innerHTML = "Ride: --";
            document.getElementById("rideRoute").innerHTML = "Route: --";
            document.getElementById("rideTotal").innerHTML = "Total Students: --";
            document.getElementById("rideList").innerHTML = "Present Students:<br>--";
        }

    } catch (error) {
        console.log("Error loading data:", error);
    }
}

// ================= START =================

loadData();
setInterval(loadData, 1000);
