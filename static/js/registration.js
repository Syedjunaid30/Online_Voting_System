setTimeout(() => {
        document.querySelectorAll('.flash-message').forEach(msg => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 1000);
        });
    }, 4000);