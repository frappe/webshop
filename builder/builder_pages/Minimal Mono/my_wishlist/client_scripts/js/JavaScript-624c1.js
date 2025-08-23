// Write your script here
const getSampleRedirect = async (item_code, qty) => {
    console.log("placing order");
    const url = `${page_data.url}/api/v2/method/webshop.webshop.api.test_redirect`;

    try {
        const response = await fetch(url, {
            method: "GET",
            redirect: 'manual' // Important: Tell fetch not to follow redirects
        });
        console.log({response})

        if (response.status === 302) {
            const redirectURL = response.headers.get('Location');
            if (redirectURL) {
                window.location.href = redirectURL; // Manually redirect
            } else {
                console.error("Redirect URL not found in response headers.");
            }
        } else {
            console.warn("Unexpected response status:", response.status);
        }

    } catch (err) {
        console.error("Update error:", err);
    }
};

document.addEventListener("DOMContentLoaded", getSampleRedirect);

