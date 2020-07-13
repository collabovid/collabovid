(function ($) {

    $.fn.collabovidSimilarSearch = function (options) {
        /**
         * Provides functions to perform a search request.
         * @param value
         * @returns {*|boolean}
         */

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                indicator: null,
                paper_container: null,
                pagination_container: null,
                receivePaperUrl: null,
                per_page: 10
            }, options);
        };

        plugin.init();

        window.formAjaxAllowed = true;

        let update_pagination_container = plugin.settings.pagination_container.paginate({
            searchQuery: load_dois,
        });

        plugin.submit(function (e) {
            e.preventDefault();
            // This parameter prevents that multiple ajax request are executed at the same time.
            if (!window.formAjaxAllowed) {
                return false;
            }

            window.formAjaxAllowed = false;

            plugin.settings.pagination_container.hide();

            plugin.settings.paper_container.hide();
            plugin.settings.indicator.show();

            $.ajax({
                url: plugin.attr("action"),
                type: 'POST',
                data: plugin.serialize(),
                success: function (data) {

                    window.Pagination.last_request = data.dois;
                    window.formAjaxAllowed = true;

                    load_dois(data.dois, 1, false);
                },
                error: function (request, error) {
                    console.log("Request: " + JSON.stringify(request));
                    console.log("Error: " + error);
                }
            });
        });

        function load_dois(dois, page, scroll = false) {

            // This parameter prevents that multiple ajax request are executed at the same time.
            if (!window.formAjaxAllowed) {
                return false;
            }

            window.formAjaxAllowed = false;

            plugin.settings.pagination_container.hide();
            plugin.settings.paper_container.hide();
            plugin.settings.indicator.show();

            let bottom = (page - 1) * plugin.settings.per_page;
            let top = bottom + plugin.settings.per_page;

            let page_dois = dois.slice(bottom, top);

            $.get(plugin.settings.receivePaperUrl, {
                    'dois': JSON.stringify(page_dois)
                }, function (data) {

                    plugin.settings.paper_container.html(data);

                    plugin.settings.indicator.hide();
                    plugin.settings.paper_container.fadeIn();

                    update_pagination_container();

                    if (scroll) {
                        $('html, body').scrollTop(plugin.settings.paper_container.offset().top - 50);
                    }

                    window.formAjaxAllowed = true;
                }
            );
        }

        return {}
    }
}(jQuery));
