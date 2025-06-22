// test.js
window.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("loadProfile");
    const out = document.getElementById("output");

    btn.addEventListener("click", () => {
        out.textContent = "Loading…";
        requestAnimationFrame(async () => {
            // 1) Pull from sessionStorage instead of localStorage
            const token = window.localStorage.getItem("authToken");
            if (!token) {
                out.textContent = "Error: no auth token. Log in first.";
                return;
            }

            try {
                const res = await fetch("http://localhost:5000/me", {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || res.statusText);
                out.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                out.textContent = `Error: ${err.message}`;
            }
        });
    });
});
