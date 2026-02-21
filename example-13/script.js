var div = document.querySelectorAll("div")[0];

function start_fade_in(e) {
  div.style = "opacity:0.999";
  e.preventDefault();
}

function start_fade_out(e) {
  div.style = "opacity:0.1";
  e.preventDefault();
}

var fadeoutBtn = document.querySelectorAll("button")[0];
var fadeInBtn = document.querySelectorAll("button")[1];

fadeoutBtn.addEventListener("click", start_fade_out);
fadeInBtn.addEventListener("click", start_fade_in);
