$(document).ready(function () {
    function initializeFavoritePaperStorage() {
        const currentValue = localStorage.getItem("favoritePapers");
        if (currentValue === undefined || currentValue === null) {
            localStorage.setItem("favoritePapers", "[]");
        }
    }

    window.update_favorite_badge = function () {
        initializeFavoritePaperStorage();

        let favoriteDois = JSON.parse(localStorage.getItem("favoritePapers"));

        const badge = $("#favorite-papers-badge");
        if (favoriteDois.length > 0)
            badge.text(favoriteDois.length).show();
        else
            badge.text("").hide();
    }

    window.update_favorite_links = function () {
        initializeFavoritePaperStorage();
        let favoriteDois = new Set(JSON.parse(localStorage.getItem("favoritePapers")));
        $(".favorite-paper-link").each(function () {
            const doi = $(this).data("doi");
            if (favoriteDois.has(doi)) {
                $(this).addClass('active');
            } else {
                $(this).removeClass('active');
            }
        });
    }

    $(document).on("click", ".favorite-paper-link", function (e) {
        e.preventDefault();
        initializeFavoritePaperStorage();

        let favoriteDois = JSON.parse(localStorage.getItem("favoritePapers"));

        const doi = $(this).data('doi');
        if (favoriteDois.includes(doi)) {
            favoriteDois = favoriteDois.filter(item => item !== doi);
        } else {
            favoriteDois.push(doi);
        }

        $(this).toggleClass('active');
        localStorage.setItem("favoritePapers", JSON.stringify(favoriteDois));

        window.update_favorite_badge();
    });

    window.update_favorite_badge();
});