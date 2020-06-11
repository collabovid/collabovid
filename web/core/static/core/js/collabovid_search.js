(function ($) {

    $.fn.collabovidSearch = function (options) {
        /**
         * Provides functions to perform a search request.
         * @param value
         * @returns {*|boolean}
         */

        const isFunction = value => value && (Object.prototype.toString.call(value) === "[object Function]" ||
            "function" === typeof value || value instanceof Function);

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                indicator: null,
                paper_container: null,
                pagination_container: null,
            }, options);
        };

        plugin.init();

        window.formAjaxAllowed = true;

        let update_pagination_container = plugin.settings.pagination_container.paginate({
            searchQuery: search_query,
        });

        function search_query(data, page, scroll = false, initialize, on_success) {

            // This parameter prevents that multiple ajax request are executed at the same time.
            if (!window.formAjaxAllowed) {
                return false;
            }

            window.formAjaxAllowed = false;

            plugin.settings.pagination_container.hide();


            if (initialize) {
                initialize();
            }

            plugin.settings.paper_container.hide();
            plugin.settings.indicator.show();

            if (isFunction(data)) {
                data = data();
            }

            data += "&page=" + page;

            $.ajax({
                url: plugin.attr("action"),
                type: 'POST',
                data: data,
                success: function (data) {
                    plugin.settings.paper_container.html(data);

                    plugin.settings.indicator.hide();
                    plugin.settings.paper_container.fadeIn();

                    update_pagination_container();

                    if (scroll) {
                        $('html, body').scrollTop(plugin.settings.paper_container.offset().top - 50);
                    }

                    window.Pagination.last_request = data;

                    if (on_success) {
                        on_success();
                    }

                    window.formAjaxAllowed = true;
                },
                error: function (request, error) {
                    console.log("Request: " + JSON.stringify(request));
                    console.log("Error: " + error);
                }
            });
        }

        function push_request_to_url(data, shorten = true) {

            if (shorten) {
                data = data.replace(/[^&]+=\.?(?:&|$)/g, '').replace(/&$/, '');
            }

            let url = window.location.protocol + "//" + window.location.host + window.location.pathname;
            if (data.length > 0) {
                url += "?" + data;
            }

            window.history.pushState({path: url}, '', url);
        }


        return {
            searchQuery: search_query,
            pushToUrl: push_request_to_url
        }
    }
}(jQuery));
