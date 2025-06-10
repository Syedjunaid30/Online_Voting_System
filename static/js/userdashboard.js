
    document.addEventListener("DOMContentLoaded", () => {
        const toast = document.querySelector(".toast-message");
        if (toast) {
            setTimeout(() => toast.remove(), 4000);
        }
    });

