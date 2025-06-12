const video = document.getElementById('video');
const status = document.getElementById('status');
const videoContainer = document.getElementById('video-container');
const partyList = document.querySelector('.party-list');

if (alreadyVoted) {
    if (status) status.textContent = "✅ You have already voted. Thank you!";
    if (video) video.style.display = 'none';
    if (partyList) partyList.style.display = 'none';
} else {
    Promise.all([
        faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models'),
        faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
        faceapi.nets.faceRecognitionNet.loadFromUri('/static/models')
    ]).then(startVideo);

    function startVideo() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
            })
            .catch(err => {
                console.error("❌ Camera error:", err);
                if (status) status.textContent = "Camera access denied.";
            });
    }

    video.addEventListener('play', async () => {
        try {
            const response = await fetch(`/get_face_path/${userId}`);
            const data = await response.json();

            if (data.error) throw new Error(data.error);

            const labeledFaceDescriptor = await loadLabeledImages(data.path);
            const faceMatcher = new faceapi.FaceMatcher(labeledFaceDescriptor, 0.6);

            const canvas = faceapi.createCanvasFromMedia(video);
            canvas.style.position = 'absolute';
            canvas.style.top = `${video.offsetTop}px`;
            canvas.style.left = `${video.offsetLeft}px`;
            canvas.style.zIndex = 2;
            canvas.width = video.offsetWidth;
            canvas.height = video.offsetHeight;
            videoContainer.appendChild(canvas);

            const displaySize = { width: video.offsetWidth, height: video.offsetHeight };
            faceapi.matchDimensions(canvas, displaySize);

            let faceVerified = false;

            const interval = setInterval(async () => {
                const detections = await faceapi
                    .detectAllFaces(video, new faceapi.SsdMobilenetv1Options())
                    .withFaceLandmarks()
                    .withFaceDescriptors();

                const resized = faceapi.resizeResults(detections, displaySize);
                canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);

                const results = resized.map(d => faceMatcher.findBestMatch(d.descriptor));

                results.forEach((result, i) => {
                    const box = resized[i].detection.box;

                    const shrink = 10;
                    const smallBox = {
                        x: box.x + shrink / 2,
                        y: box.y + shrink / 2,
                        width: box.width - shrink,
                        height: box.height - shrink
                    };

                    const drawBox = new faceapi.draw.DrawBox(smallBox, {
                        label: result.toString()
                    });
                    drawBox.draw(canvas);

                    if (result.label !== 'unknown' && !faceVerified) {
                        faceVerified = true;
                        if (status) status.textContent = "✅ Face Verified. You may vote.";
                        document.querySelectorAll('.vote-btn').forEach(btn => {
                            btn.disabled = false;
                            btn.classList.add('enabled');
                        });
                    }
                });
            }, 1000);

            document.querySelectorAll('.party-form').forEach(form => {
                form.addEventListener('submit', () => {
                    clearInterval(interval);
                    if (video.srcObject) {
                        video.srcObject.getTracks().forEach(track => track.stop());
                        video.srcObject = null;
                    }

                    canvas.remove();

                    if (status) status.textContent = "🗳️ Thank you for voting!";
                    document.querySelectorAll('.vote-btn').forEach(btn => {
                        btn.disabled = true;
                        btn.classList.remove('enabled');
                    });
                });
            });

        } catch (err) {
            console.error("❌ Detection error:", err);
            if (status) status.textContent = "Face verification failed: " + err.message;
        }
    });

    async function loadLabeledImages(imageUrl) {
        const img = await faceapi.fetchImage(imageUrl);
        const detection = await faceapi
            .detectSingleFace(img)
            .withFaceLandmarks()
            .withFaceDescriptor();

        if (!detection) throw new Error("No face detected in stored image.");
        return new faceapi.LabeledFaceDescriptors("user", [detection.descriptor]);
    }
}
