document.addEventListener('DOMContentLoaded', () => {
  const video = document.querySelector('.vote-info video');

  if (video) {
    video.pause(); // start paused

    video.style.cursor = 'pointer';

    video.addEventListener('click', () => {
      if (video.paused) {
        video.play();
      } else {
        video.pause();
      }
    });
  }
});

 AOS.init({ duration: 1000 });

        // Accordion behavior
        const buttons = document.querySelectorAll('.accordion-button');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                const content = button.nextElementSibling;
                button.classList.toggle('active');
                content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + "px";
                document.querySelectorAll('.accordion-content').forEach(c => {
                    if (c !== content) c.style.maxHeight = null;
                });
            });
        });

        // Auto-dismiss flash messages after 3 seconds
        window.addEventListener("DOMContentLoaded", () => {
            const flash = document.querySelectorAll('.toast-message');
            flash.forEach(msg => {
                setTimeout(() => {
                    msg.style.opacity = '0';
                    msg.style.transform = 'translateY(-10px)';
                    setTimeout(() => msg.remove(), 300);
                }, 3000);
            });
        });
