document.getElementById('accept-btn').addEventListener('click', function() {
    document.cookie = "yuki=True; max-age=31536000; path=/";
    location.href = "/";
    return;
});

document.getElementById('reject-btn').addEventListener('click', function() {
    hideCookieNotice();
    localStorage.setItem('cookieAccepted', 'false');
});

window.onload = function() {
    const cookieAccepted = localStorage.getItem('cookieAccepted');
    if (cookieAccepted !== 'true') {
        showCookieNotice();
    }
};

function showCookieNotice() {
    const cookieNotice = document.getElementById('cookie-notice');
    cookieNotice.style.opacity = '1';
    cookieNotice.style.transform = 'translateY(0)';
}

function hideCookieNotice() {
    const cookieNotice = document.getElementById('cookie-notice');
    cookieNotice.style.opacity = '0';
    cookieNotice.style.transform = 'translateY(20px)';
    setTimeout(() => {
        cookieNotice.style.display = 'none';
    }, 500);
}