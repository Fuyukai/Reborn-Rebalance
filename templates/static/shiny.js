function swapWithShinyIcon(el) {
    el.setAttribute("src", "/sprites/" + el.getAttribute("x-idx") + "_shiny.png");
}

function unswapWithShinyIcon(el) {
    el.setAttribute("src", "/sprites/" + el.getAttribute("x-idx") + ".png");
}

function swapWithShinyBattler(el) {
    el.setAttribute("src", "/sprites/battler_" + el.getAttribute("x-idx") + "_shiny.png");
}

function unswapWithShinyBattler(el) {
    el.setAttribute("src", "/sprites/battler_" + el.getAttribute("x-idx") + ".png");
}