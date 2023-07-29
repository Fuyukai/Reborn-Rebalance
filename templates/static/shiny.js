function swapWithShinyIcon(el) {
    el.setAttribute("src", "/sprites/" + el.getAttribute("x-idx") + "_shiny.png");
}

function unswapWithShinyIcon(el) {
    el.setAttribute("src", "/sprites/" + el.getAttribute("x-idx") + ".png");
}

function swapWithShinyBattler(el) {
    if (el.dataset.form !== "Normal") {
        el.setAttribute("src", "/sprites/battler_" + el.dataset.idx + "_" + el.dataset.form + "_shiny.png")
    } else {
        el.setAttribute("src", "/sprites/battler_" + el.dataset.idx + "_shiny.png");
    }
}

function unswapWithShinyBattler(el) {
    if (el.dataset.form !== "Normal") {
        el.setAttribute("src", "/sprites/battler_" + el.dataset.idx + "_" + el.dataset.form + ".png")
    } else {
        el.setAttribute("src", "/sprites/battler_" + el.dataset.idx + ".png");
    }
}