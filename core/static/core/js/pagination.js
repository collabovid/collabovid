(function ($) {

    $.fn.paginate = function (options) {


        var plugin = this;


        plugin.init = function () {
            plugin.settings = $.extend({
                searchQuery: null,
                skipHtml: "<li class=\"page-item disabled\"><a class=\"page-link\" data-next=\"false\" data-prev=\"false\" data-page=\"-1\" href=\"#\">...</a></li>",
                elementHtml: "<li class=\"page-item\"><a class=\"page-link\" href=\"#\" data-next=\"false\" data-prev=\"false\"></a></li>"
            }, options);

            plugin.create_modal();
        };


        plugin.create_modal = function () {
            plugin.hide().html("" +
                "<ul class=\"pagination my-3 justify-content-center\">" +
                "            <li class=\"page-item page-item-fixed\">" +
                "               <a class=\"page-link\" href=\"#\" data-page=\"-1\" data-next=\"false\"" +
                "                                                     data-prev=\"true\"><span" +
                "                    aria-hidden=\"true\">&laquo;</span></a>" +
                "</li>" +
                "" +
                "            <li id=\"page-item-next\" class=\"page-item page-item-fixed\"><a class=\"page-link\" href=\"#\"" +
                "                                                                         data-page=\"-1\" data-next=\"true\"" +
                "                                                                         data-prev=\"false\"><span aria-hidden=\"true\">&raquo;</span></a>" +
                "            </li>" +
                "        </ul>");

            console.log("created model.")
        };

        plugin.init();

        window.Pagination = {};

        function insert_page(i, last_page_added) {

            if (i <= last_page_added) {
                return last_page_added;
            }

            if (i - 1 > last_page_added) {
                insert_page_placeholder();
            }

            let element = $(plugin.settings.elementHtml);

            element.insertBefore($("#page-item-next")).find('a').data('page', i).html(i);

            if (i === window.Pagination.current_page) {
                element.addClass("active");
            }

            return i;
        }

        function insert_page_placeholder() {
            $(plugin.settings.skipHtml).insertBefore($("#page-item-next"));
        }

        $(document).on("click", ".page-item:not(.disabled) > a", function (e) {
            e.preventDefault();

            let is_prev = $(this).data("prev");
            let is_next = $(this).data("next");

            let page = -1;


            if (is_prev && window.Pagination.previous_page > 0) {
                page = window.Pagination.previous_page

            } else if (is_next && window.Pagination.next_page > 0) {
                page = window.Pagination.next_page
            } else if (is_next || is_prev) {
                return;
            } else {
                page = $(this).data("page");
            }

            plugin.settings.searchQuery(window.Pagination.last_request, page);

        });

        function update_pagination_container() {
            plugin.find(".page-item:not(.page-item-fixed)").remove();

            if (window.Pagination.pagination_needed) {
                let last_page_added = 0;

                let pages = [window.Pagination.first_page, window.Pagination.previous_page,
                    window.Pagination.current_page, window.Pagination.next_page, window.Pagination.last_page];

                for (let i = 0; i < pages.length; i++) {
                    last_page_added = insert_page(pages[i], last_page_added);
                }
            }

            plugin.fadeIn();
        }

        return update_pagination_container;
    }
}(jQuery));