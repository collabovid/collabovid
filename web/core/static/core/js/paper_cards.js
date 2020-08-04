$(document).ready(function () {
    $(document).on('click', '.toggle-description', function (e) {
        e.preventDefault();
        if ($(this).hasClass('hide')) {
            $(this).closest('.abstract-container').find('.long').hide();
            $(this).closest('.abstract-container').find('.dots').show();
            $(this).parent().find('.toggle-description.show').show();
            $(this).hide();
        } else {
            $(this).closest('.abstract-container').find('.dots').hide();
            $(this).closest('.abstract-container').find('.long').fadeIn();
            $(this).parent().find('.toggle-description.hide').show();
            $(this).hide();
        }
    });

    $(document).on('click', '.show-authors', function (e) {
        e.preventDefault();
        $(this).parent().find('.author.d-none').removeClass('d-none');
        $(this).parent().find('.remove-on-show-authors').remove();
        $(this).remove();
    });

    function initializeFavoritePaperStorage()
    {
        const currentValue = localStorage.getItem("favoritePapers");
        if(currentValue === undefined || currentValue === null)
        {
            localStorage.setItem("favoritePapers", "[]");
        }
    }

    window.update_favorite_links = function ()
    {
        initializeFavoritePaperStorage();
        let favoriteDois = new Set(JSON.parse(localStorage.getItem("favoritePapers")));
        $(".favorite-paper-link").each(function (){
            const doi = $(this).data("doi");
            if(favoriteDois.has(doi))
            {
                $(this).addClass('active');
            } else
            {
                $(this).removeClass('active');
            }
        });
    }

    $(document).on("click", ".favorite-paper-link", function (e){
        e.preventDefault();
        initializeFavoritePaperStorage();

        console.log(localStorage.getItem("favoritePapers"));
        let favoriteDois = JSON.parse(localStorage.getItem("favoritePapers"));

        const doi = $(this).data('doi');
        if(favoriteDois.includes(doi))
        {
            favoriteDois = favoriteDois.filter(item => item !== doi);
        } else {
            favoriteDois.push(doi);
        }

        $(this).toggleClass('active');

        localStorage.setItem("favoritePapers", JSON.stringify(favoriteDois));
    });
});