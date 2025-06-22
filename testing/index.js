// index.js
window.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("loadProfile");
    const output = document.getElementById("output");

    btn.addEventListener("click", () => {
        // 1) Show the loader text
        output.textContent = "Loading…";

        // 2) Give the browser one frame to render that...
        requestAnimationFrame(() => {
            // 3) Then perform the fetch
            fetch("http://localhost:5000/me", {
                method: "GET",
                mode: "cors", // cross-origin fetch
                credentials: "include", // send the session cookie
            })
                .then(async (res) => {
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.error || res.statusText);
                    }
                    return data;
                })
                .then((user) => {
                    // 4) Success! Pretty-print the JSON
                    output.textContent = JSON.stringify(user, null, 2);
                })
                .catch((err) => {
                    // 5) Failure: network or 4xx/5xx
                    output.textContent = `Error: ${err.message}`;
                });
        });
    });
});
