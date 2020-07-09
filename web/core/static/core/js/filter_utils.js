(function ($) {

    $.fn.lightDatepicker = function (options) {
        let plugin = this;

        return plugin.datepicker({
            uiLibrary: 'bootstrap4',
            format: 'yyyy-mm-dd'
        }).parent().find('button').removeClass('btn-outline-secondary').addClass('btn-light');
    };
}(jQuery));
(function ($) {
    $.fn.tagifyAjax = function (options) {
        function extendObj(obj1, obj2) {
            for (var key in obj2) {
                if (obj2.hasOwnProperty(key)) {
                    obj1[key] = obj2[key];
                }
            }

            return obj1;
        }

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                initialValues: null,
                tagifySettings: null
            }, options);
        };

        plugin.init();

        let elementId = this.attr('id');
        let url = this.data('url');
        let resultKey = this.data('result-key');
        let externalTagClass = this.data('external-tag-class');

        let inputElm = document.getElementById(elementId);

        let tagify_default_settings = {
            whitelist: plugin.settings.initialValues,
            enforceWhitelist: true,
            skipInvalid: true,
            delimiters: 'a^',
            originalInputValueFormat: valuesArr => valuesArr.map(item => item.pk).join(','),
        };

        let tagify = new Tagify(inputElm, extendObj(tagify_default_settings, plugin.settings.tagifySettings));

        tagify.addTags(plugin.settings.initialValues);

        if (window.tagifyRequests === undefined || window.tagifyRequests === null) {
            window.tagifyRequests = {};
        }

        window.tagifyRequests[elementId] = null;

        let getEntries = (function getEntries(text, on_result) {

            if (window.tagifyRequests[elementId] !== null) {
                window.tagifyRequests[elementId].abort();
            }

            window.tagifyRequests[elementId] = $.ajax({
                url: url,
                type: 'GET',
                data: "query=" + text,
                success: function (data) {
                    on_result(data);
                },
                error: function (request, error) {
                    //console.log("Request: " + JSON.stringify(request));
                    //console.log("Error: " + error);
                }
            });

        });


        // on character(s) added/removed (user is typing/deleting)
        function onInput(e) {
            tagify.settings.whitelist.length = 0; // reset current whitelist
            tagify.loading(true).dropdown.hide.call(tagify);// show the loader animation

            getEntries(e.detail.value, function (result) {
                $.each(result[resultKey], function () {
                    tagify.settings.whitelist.push(this);
                });

                tagify.loading(false).dropdown.show.call(tagify, e.detail.value);
            });
        }

        $(document).on('click', '.' + externalTagClass, function (e) {
            e.preventDefault();
            let object = $(this).data('object');

            tagify.settings.whitelist.push(object);
            tagify.addTags([object]);

            $("#"+elementId).closest('form').submit();

        });

        tagify.on('input', onInput);
    };

}(jQuery));