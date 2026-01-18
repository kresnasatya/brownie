// throw Error("bad");

var paragraphs = document.querySelectorAll("p");
console.log(paragraphs);

inputs = document.querySelectorAll("input");
for (var i = 0; i < inputs.length; i++) {
  var name = inputs[i].getAttribute("name");
  var value = inputs[i].getAttribute("value");
  if (value.length > 15) {
    console.log("Input " + name + " has too much text.");
  }
}

function lengthCheck() {
  var name = this.getAttribute("name");
  var value = this.getAttribute("value");
  if (value.length > 10) {
    console.log("Input " + name + " has too much text.");
  }
}

var inputs = document.querySelectorAll("input");
for (var i = 0; i < inputs.length; i++) {
  inputs[i].addEventListener("keydown", lengthCheck);
}
