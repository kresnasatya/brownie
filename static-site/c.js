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
