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

        let paginator = plugin.collabovidJsPaginator(plugin.settings);

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
                    window.Pagination.result_size = data.result_size;

                    paginator.loadDois(data.dois, 1, false);
                },
                error: function (request, error) {
                    console.log("Request: " + JSON.stringify(request));
                    console.log("Error: " + error);
                }
            });
        });

        return {}
    }
}(jQuery));
