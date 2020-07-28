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
                allWeeks: null,
            }, options);
        };

        plugin.init();

        window.visualizationInitialized = false;
        window.visualizationEventRunning = false;
        window.justUsedTouchControls = false;
        window.oldPanSpeed = 0;
        window.oldZoomSpeed = 0;
        window.inFullScreen = false;

        const TOPIC_COLORS_BADGE = ["#c6759c", "#7ad895", "#cba174", "#ad71b9", "#cf3759", "#93003a"];
        const TOPIC_COLORS_VISUALIZATION = [0xc6759c, 0x7ad895, 0xcba174, 0xad71b9, 0xcf3759, 0x93003a];


        const topics = plugin.settings.topics;
        const colors = plugin.settings.colors;

        const canvas = document.getElementById('visualization-container');
        const selectedCardContainer = $('#selected-card-container');
        const visualization = new EmbeddingVisualization();
        const topicsContainer = $('#topics-container');
        const paperLoadingIndicator = $('#paper-loading-indicator');
        const topicLegend = $('#topic-legend');
        const categoryLegend = $('#category-legend');
        const legend = $('.legend');
        const paperSelectedLegend = $('#paper-selected-legend');
        const topicFilterInput = $('#topic-filter-input');
        const fullScreenToggleBtn = $(".full-screen-toggle");
        const embeddingVisualizationContainer = $("#embedding-visualization-container");
        const paperSelectedMessage = $("#paper-selected-message");
        const zoomPanControls = $("#zoom-pan-controls");

        const titleContainer = $("#titleContainer");

        let rotationTimeoutId = 0;

        let currentColorIndex = 0;


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

        const weekSlider = $("#week-slider").slider({
            //ticks: Array.from(Array(plugin.settings.allWeeks.length).keys()),
            formatter: function (value) {
                return (new Date(plugin.settings.allWeeks[value])).toISOString().substring(0, 10);
            },
            step: 1,
            tooltip_position: 'left',
            orientation: 'vertical',
            reversed: true,
            value: plugin.settings.allWeeks.length - 1,
            min: 0,
            max: plugin.settings.allWeeks.length - 1
        });

        weekSlider.on('change', function (e) {
            let dois = [];

            $.each(visualization.papers, function (index, paper) {
                if (plugin.settings.allWeeks[e.value.newValue] <= paper.published_at) {
                    dois.push(paper.doi)
                }

            });

            let doi_set = new Set(dois);

            $.each(topics, function (index, paper_ids) {
                let count = 0;
                for (let i = 0; i < paper_ids.length; ++i) {
                    if(!doi_set.has(paper_ids[i]))
                    {
                        count++;
                    }
                }
                $(".topic-item[data-topic="+index+"]").find(".paper-count").text(count);
            });

            visualization.hidePapers(doi_set);
        });


        $(".toggle-date-slider").click(function () {
            $(".exchangeable-controls").toggle();
        });

        function onSelected(idx, paper) {

            if (window.visualizationEventRunning) {
                return;
            }

            window.visualizationEventRunning = true;

            paperLoadingIndicator.show();
            selectedCardContainer.hide();
            legend.hide();
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
                legend.show();
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
                window.visualizationInitialized = true;

                if (plugin.settings.preSelectedPaper) {
                    selectPaper(plugin.settings.preSelectedPaper);

                } else if (plugin.settings.preSelectedTopic) {
                    selectTopic(plugin.settings.preSelectedTopic);
                    console.log("selected topic");
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
            if (window.visualizationEventRunning || !window.visualizationInitialized) {
                return;
            }

            window.visualizationEventRunning = true;
            selectedCardContainer.hide();
            topicsContainer.show();
            categoryLegend.show();
            legend.show();
            paperSelectedLegend.hide();
            topicLegend.html("").hide();
            currentColorIndex = 0;

            $(".category-badge").each(function () {
                $(this).removeClass('badge-secondary').css('background-color', $(this).data('background-color'));
            });

            pushToUrl();

            window.visualizationEventRunning = false;
        });

        function highlightTopics() {

            const badges = topicLegend.find('span.badge');
            if (badges.length <= 0) {
                visualization.deselectAll();
            } else {
                let is_first = true;

                badges.each(function () {
                    const paperIds = new Set(topics[$(this).data('id')]);
                    visualization.selectPapers(paperIds, $(this).data('color'), is_first, is_first);
                    is_first = false;
                });

                document.body.scrollTop = 0;
                document.documentElement.scrollTop = 0;

                topicLegend.show();
                categoryLegend.hide();
                legend.show();
                paperSelectedLegend.hide();
            }
        }

        $(document).on('click', '#topic-legend span.badge > span', function (e) {
            e.preventDefault();

            $(this).closest('span.badge').remove();
            highlightTopics();
        });

        $('.topic-item .show-topic').on('click', function (e) {
            if (window.visualizationEventRunning || !window.visualizationInitialized) {
                return;
            }

            const topicItem = $(e.target).closest('.topic-item');
            const topicId = topicItem.data('topic');


            if (topicLegend.find('span.badge[data-id=' + topicId + "]").length > 0) {
                return;
            }

            window.visualizationEventRunning = true;

            if (topicLegend.find('span.badge').length >= TOPIC_COLORS_BADGE.length) {
                topicLegend.find("div:last-of-type").remove();
            }

            const topicBadgeTemplate = '<div><span id="topic-label" ' +
                'style="background-color:{color};" ' +
                'data-id="{id}" ' +
                'data-color="{color-js}" ' +
                'class="badge text-white">{name} <span role="button">&cross;</span></span></div>';

            currentColorIndex = (currentColorIndex + 1) % TOPIC_COLORS_BADGE.length;

            const index = currentColorIndex;
            const badgeColor = TOPIC_COLORS_BADGE[index];
            const visualizationColor = TOPIC_COLORS_VISUALIZATION[index];
            const topicName = topicItem.data('topic-name');
            const topicBadge = topicBadgeTemplate.replace("{name}", topicName)
                .replace("{color}", badgeColor).replace("{id}", topicId)
                .replace("{color-js}", visualizationColor);

            topicLegend.prepend(topicBadge);

            highlightTopics();


            pushToUrl(topicId);
            window.visualizationEventRunning = false;
        });

        $('.category-label').on('click', function (e) {
            if (window.visualizationEventRunning || !window.visualizationInitialized) {
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
            visualization.selectPapers(dois, visualization.colors[categoryId], true, true);

            pushToUrl();
            categoryLegend.show();
            paperSelectedLegend.hide();
            topicLegend.hide();
            window.visualizationEventRunning = false;
        });


        $(".rotation-button").on('mousedown touchstart', function (e) {
            e.preventDefault();

            let isLeft = $(this).hasClass('left');

            let updateRotation = function () {
                visualization.rotate(isLeft);
                $("#rotation-label span.deg")
                    .text(visualization.currentRotationStep * (360 / visualization.rotationMaxSteps));

                rotationTimeoutId = setTimeout(updateRotation, 100);
            };

            rotationTimeoutId = setTimeout(updateRotation, 0);
        }).on('mouseup mouseleave touchend', function (e) {
            e.preventDefault();
            clearTimeout(rotationTimeoutId);
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