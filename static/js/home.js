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
