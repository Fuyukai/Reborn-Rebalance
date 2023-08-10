const isBrave = (navigator.brave || false)
const isChrome = !isBrave && (window.chrome || false);

if (isChrome) {
    document.getElementById("content").remove();
    document.getElementById("antichrome").classList.add("is-active");
}