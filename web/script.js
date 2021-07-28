function byId(i) { return document.getElementById(i); };
function allowDrop(ev) { ev.preventDefault(); }
function drag(ev) { ev.dataTransfer.setData("text", ev.target.id); }

let recipes
fetch('craft.json').then(r => r.json()).then(d => recipes = d);

function useItems() {
    for (let i = 0; i <= 8; i += 1) {
        byId("box" + i).innerHTML = ""
    }
    byId("result").innerHTML = ""
}

function checkRecipe() {
    let items = ["", "", "", "", "", "", "", "", ""]
    for (let i = 0; i <= 8; i += 1) {
        if (byId("box" + i).innerHTML) {
            items[i] = byId("box" + i).children[0].getAttribute("blockType")
        }
    }
    console.log(items)
    for (i in recipes) {
        if (recipes[i].recipe.toString() == items.toString()) {
            newItem = new Image()
            newItem.src = recipes[i].texture;
            newItem.id = "newitem"
            newItem.className = "center"
            newItem.setAttribute("ondragstart", "drag(event)")
            newItem.setAttribute("blockType", i)
            byId("result").appendChild(newItem)
        }
    }
}

function drop(ev) {
    let path = ev.path[0]
    //Allow dragging only to empty divs (or back to home)
    if ((ev.target.children.length === 0 && path.nodeName === "DIV")
        || path.id === "home") {
        ev.preventDefault();
        var data = ev.dataTransfer.getData("text");
        ev.target.appendChild(byId(data));
        if (data == "newitem") {
            byId("newitem").id = "9" //placeholder to prevent it from being cleared
            useItems()
        }
        checkRecipe()
    }
}

let intervalId = window.setInterval(function () {
    if (byId("box7").children.length === 1) {
        eel.say_hello_py("dirt");  // Call a Python function, placeholder just to test. put a block in cell 7
        console.log("Ran?!")
    }
}, 1000);

window.addEventListener("keydown", function (e) {
    if (e.key == "Escape") {
        window.close()
    }
})