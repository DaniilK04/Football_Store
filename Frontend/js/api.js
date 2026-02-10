const API_URL = "http://127.0.0.1:8000/api/";

function getToken() {
    return localStorage.getItem('token');
}

async function apiGet(endpoint) {
    const res = await fetch(API_URL + endpoint, {
        headers: getToken() ? { "Authorization": "Token " + getToken() } : {}
    });
    return await res.json();
}

async function apiPost(endpoint, data) {
    const res = await fetch(API_URL + endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(getToken() && { "Authorization": "Token " + getToken() })
        },
        body: JSON.stringify(data)
    });
    return await res.json();
}
