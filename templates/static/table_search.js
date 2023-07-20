(function() {
    var searchInput = document.querySelector("#search-input"),
        rows = document.querySelectorAll("#table tbody tr"),
        timer;

    function filterRows() {
        [].forEach.call(rows, function(row) {

            var cells = row.querySelectorAll("td"),
                containsText = false;

            [].forEach.call(cells, function(cell) {
                var text = cell.textContent.toLowerCase(),
                    search = searchInput.value.toLowerCase();

                if (text.indexOf(search) != -1)
                    containsText = true;
            });

            if (containsText)
                row.style.display = "";
            else
                row.style.display = "none";

        });

    }

    searchInput.onkeyup = function() {

        clearTimeout(timer);

        timer = setTimeout(function() {

            if (searchInput.value != "")
                window.history.pushState(searchInput.value, "", "#search=" + encodeURI(searchInput.value));

        }, 1000);

        filterRows();

    }

    window.onpopstate = function(e) {

        if (e.state !== null) {
            searchInput.value = e.state;

            filterRows();
        } else {
            var searchValue = window.location.hash.split("=").pop();

            searchInput.value = decodeURI(searchValue);

            filterRows();
        }

    }

})();