
  window.addEventListener('load', () => {
    setTimeout(() => {
      document.getElementById('log').classList.add('glow-effect');
    }, 3000); // 4 seconds delay
});



function speakWelcome() {

    let audio = new Audio("/static/audio/welcome.wav");

    audio.play().catch(function(error){
        console.log("Audio play blocked:", error);
    });
}

document.body.addEventListener("click", speakWelcome, { once: true });

