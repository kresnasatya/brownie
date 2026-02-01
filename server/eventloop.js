// Counting animation example
var count = 0;
var outputs = document.querySelectorAll("div");
if (outputs.length > 1) {
  var output = outputs[1];
  function callback() {
    output.innerHTML = "count: " + count++;
    if (count < 100) requestAnimationFrame(callback);
  }
  requestAnimationFrame(callback);
}
