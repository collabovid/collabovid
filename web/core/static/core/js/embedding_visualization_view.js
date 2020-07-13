(function ($) {
    $.fn.buildEmbeddingVisualizationView = function (options) {
        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                topics: null,
                colors: null,
                url: null,
                preSelectedPaper: null,
                preSelectedTopic: null,
                atlasImageUrl: null,
                paperFileUrl: null,
                receivePaperUrl: null,
            }, options);
        };

        plugin.init();

        window.visualizationEventRunning = false;
        window.justUsedTouchControls = false;
        window.oldPanSpeed = 0;
        window.oldZoomSpeed = 0;
        window.inFullScreen = false;

        const topics = plugin.settings.topics;
        const colors = plugin.settings.colors;

        const canvas = document.getElementById('visualization-container');
        const selectedCardContainer = $('#selected-card-container');
        const visualization = new EmbeddingVisualization();
        const topicsContainer = $('#topics-container');
        const paperLoadingIndicator = $('#paper-loading-indicator');
        const topicLegend = $('#topic-legend');
        const topicLabel = $('#topic-label');
        const categoryLegend = $('#category-legend');
        const paperSelectedLegend = $('#paper-selected-legend');
        const topicFilterInput = $('#topic-filter-input');
        const fullScreenToggleBtn = $(".full-screen-toggle");
        const embeddingVisualizationContainer = $("#embedding-visualization-container");
        const paperSelectedMessage = $("#paper-selected-message");
        const zoomPanControls = $("#zoom-pan-controls");

        const titleContainer = $("#titleContainer");

        function pushToUrl(identifier = null) {
            let url = window.location.protocol + "//"
                + window.location.host +
                plugin.settings.url;
            if (identifier) {
                url += identifier
            }

            if (url !== window.location.href) {
                window.history.pushState({path: url}, '', url);

            }
        }

        function selectPaper(doi) {
            console.log(doi)
            visualization.papers.forEach((paper, i) => {
                if (paper.doi == doi) {
                    onSelected(i, paper);
                }
            });
        }

        function selectTopic(pk) {
            $(".topic-item[data-topic=" + pk + "] .show-topic:first-of-type").click();
        }

        function selectCategory(pk) {
            $(".category-label[data-category-id=" + pk + "]").click();
        }

        fullScreenToggleBtn.click(function (e) {
            e.preventDefault();
            embeddingVisualizationContainer.toggleClass('full-screen');
            fullScreenToggleBtn.toggle();
            visualization.refreshSize();

            window.inFullScreen = !window.inFullScreen;
        });

        $(document).keyup(function (e) {
            if (window.inFullScreen && e.keyCode === 27) fullScreenToggleBtn[0].click();
        });


        topicFilterInput.on('input', function (e) {
            const query = topicFilterInput.val();
            $('.topic-item').each(function (i) {
                const element = $(this);
                let topicName = element.data('topic-name').toLowerCase();
                if (topicName.includes(query.toLowerCase()) || query.trim() === "") {
                    element.show()
                } else {
                    element.hide()
                }
            })
        });

        const zoomSlider = $("#zoom-slider").slider();
        zoomSlider.on('slide', function (e) {
            visualization.controls.zoomSpeed = e.value;
            visualization.controls.update();
        });

        const panSlider = $("#pan-slider").slider();
        panSlider.on('slide', function (e) {
            visualization.controls.panSpeed = e.value;
            visualization.controls.update();
        });

        function onSelected(idx, paper) {

            if (window.visualizationEventRunning) {
                return;
            }

            window.visualizationEventRunning = true;

            paperLoadingIndicator.show();
            selectedCardContainer.hide();
            topicsContainer.hide();
            categoryLegend.hide();
            topicLegend.hide();

            if (window.inFullScreen) {
                // Show the info box when user is in full screen and cant see the papers.
                paperSelectedMessage.stop().animate({"opacity": 1}, 500, function () {
                    paperSelectedMessage.stop().animate({"null": 1}, 4000, function () {
                        paperSelectedMessage.stop().animate({"opacity": 0}, 500);
                    });
                });
            }


            const indices = visualization.computeNeighbors(paper, 10);
            const dois = [paper.doi];
            indices.forEach((i) => {
                dois.push(visualization.papers[i].doi)
            });
            visualization.selectPaper(idx, indices);

            $.get(plugin.settings.receivePaperUrl, {
                'dois': JSON.stringify(dois)
            }, function (data) {
                selectedCardContainer.html(data);
                paperLoadingIndicator.hide();
                selectedCardContainer.show();
                paperSelectedLegend.show();
                pushToUrl(paper.doi);
                window.visualizationEventRunning = false;
            });
        }

        visualization.renderEmbeddings(canvas, onSelected, {
                'imageUrl': plugin.settings.atlasImageUrl,
                'fileUrl': plugin.settings.paperFileUrl,
                'categoryColors': colors,
                'zoomSpeed': 0.25,
                'panSpeed': 0.5
            },
            function () {
                if (plugin.settings.preSelectedPaper) {
                    selectPaper(plugin.settings.preSelectedPaper);

                } else if (plugin.settings.preSelectedTopic) {
                    selectTopic(plugin.settings.preSelectedTopic);
                }
            }
        );

        visualization.onHover(function (idx = null, paper = null) {
            if (idx && paper) {
                titleContainer.show().text(paper.title);
            } else {
                titleContainer.hide();
            }
        });


        visualization.onTouch(function () {

            if (!window.justUsedTouchControls) {
                zoomPanControls.hide();

                window.justUsedTouchControls = true;
                window.oldPanSpeed = visualization.controls.panSpeed;
                window.oldZoomSpeed = visualization.controls.zoomSpeed;

                visualization.controls.panSpeed = 0.1;
                visualization.controls.zoomSpeed = 0.1;
            }

        });

        visualization.onMouseOver(function () {

            if (window.justUsedTouchControls) {
                zoomPanControls.show();
                window.justUsedTouchControls = false;

                visualization.controls.panSpeed = window.oldPanSpeed;
                visualization.controls.zoomSpeed = window.oldZoomSpeed;
            }
        });

        visualization.onDeselect(function () {
            if (window.visualizationEventRunning) {
                return;
            }

            window.visualizationEventRunning = true;
            selectedCardContainer.hide();
            topicsContainer.show();
            categoryLegend.show();
            paperSelectedLegend.hide();
            topicLegend.hide();

            $(".category-badge").each(function () {
                $(this).removeClass('badge-secondary').css('background-color', $(this).data('background-color'));
            });

            pushToUrl();

            window.visualizationEventRunning = false;
        });

        $('.topic-item .show-topic').on('click', function (e) {
            if (window.visualizationEventRunning) {
                return;
            }

            window.visualizationEventRunning = true;

            const topicItem = $(e.target).closest('.topic-item');
            const topicId = topicItem.data('topic');
            const paperIds = new Set(topics[topicId]);
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            topicLabel.text(topicItem.data('topic-name'));
            topicLegend.show();
            categoryLegend.hide();
            paperSelectedLegend.hide();
            visualization.selectPapers(paperIds, 0xffffff);
            pushToUrl(topicId);
            window.visualizationEventRunning = false;
        });

        $('.category-label').on('click', function (e) {
            if (window.visualizationEventRunning) {
                return;
            }

            window.visualizationEventRunning = true;
            let categoryId = $(this).data('category-id');
            let categroyBadge = $("#" + categoryId + "-badge");

            $(".category-badge:not(#" + categoryId + "-badge)").css('background-color', '#6c757d');
            categroyBadge.css('background-color', categroyBadge.data('background-color'));

            let dois = new Set();
            visualization.papers.forEach(function (paper) {
                if (paper.top_category == categoryId) {
                    dois.add(paper.doi);
                }
            });
            visualization.selectPapers(dois, visualization.colors[categoryId]);

            pushToUrl();
            categoryLegend.show();
            paperSelectedLegend.hide();
            topicLegend.hide();
            window.visualizationEventRunning = false;
        });

        $(document).on("click", ".visualize-link", function (e) {
            e.preventDefault();
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            selectPaper($(this).data('paper-doi'));
        });

        $(document).on("click", ".category-link", function (e) {
            e.preventDefault();
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            selectCategory($(this).data('category-id'));
        });

        $(document).on("click", ".topic-link", function (e) {
            e.preventDefault();
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            selectTopic($(this).data('topic-id'));
        });
    };

}(jQuery));