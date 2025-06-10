document.addEventListener("DOMContentLoaded", () => {
    const flash = document.getElementById("flash-message");
    if (flash) {
        setTimeout(() => {
            flash.remove();
        }, 4000); // remove after 4 seconds
    }
});
