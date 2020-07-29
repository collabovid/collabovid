(function ($) {

    $.fn.publicationsOverTime = function (options) {

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };

        plugin.init();

        let published_dates = [];

        plugin.settings.plot_data['x'].forEach(function (item) {
            published_dates.push(new Date(item));
        });

        return new Chart(plugin, {
            type: 'line',
            data: {
                labels: published_dates,
                datasets: [{
                    label: 'Total published',
                    borderColor: window.chartColors.blue,
                    fill: false,
                    data: plugin.settings.plot_data['total'],
                    yAxisID: 'total'
                },
                    {
                        label: 'Published at date',
                        backgroundColor: window.chartColors.red,
                        type: 'bar',
                        data: plugin.settings.plot_data['added'],
                        yAxisID: 'per-day',
                    }
                ]
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    xAxes: [{
                        type: 'time',
                        time: {
                            parser: 'MM/DD/YYYY',
                            round: 'day',
                            tooltipFormat: 'll'
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Date'
                        }
                    }],
                    yAxes: [{
                        id: 'total',
                        type: 'linear',
                        position: 'left',
                        scaleLabel: {
                            labelString: 'Total',
                            display: true,
                        },

                        ticks: {
                            beginAtZero: true
                        }

                    }, {
                        id: 'per-day',
                        type: 'linear',
                        position: 'right',
                        scaleLabel: {
                            labelString: 'Number of papers/day',
                            display: true,
                        },

                        ticks: {
                            beginAtZero: true
                        }
                    }]
                },
                tooltips:
                    {
                        callbacks: {},
                    },
            }
        });
    }
}(jQuery));


(function ($) {

    $.fn.publicationsOverTimeComparison = function (options) {

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };

        plugin.init();

        let datasets = [];

        let published_dates = [];

        plugin.settings.plot_data[0]['x'].forEach(function (item) {
            published_dates.push(item["week"] + "/" + item["year"]);
        });

        plugin.settings.plot_data.forEach(function (data) {

            datasets.push({
                label: data['label'],
                borderColor: data['color'],
                fill: false,
                data: data['total'],
                yAxisID: 'total',
            });
        });


        return new Chart(plugin, {
            type: 'line',
            data: {
                labels: published_dates,
                datasets: datasets
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        id: 'total',
                        type: 'linear',
                        position: 'left',
                        scaleLabel: {
                            labelString: 'papers published',
                            display: true,
                        },

                        ticks: {
                            beginAtZero: true
                        }

                    }],
                    xAxes: [{
                        scaleLabel: {
                            labelString: 'weeks in year',
                            display: true,
                        }
                    }]
                },
                tooltips:
                    {
                        enabled: true,
                        mode: 'label',
                        callbacks: {
                            title: function (tooltipItems, data) {
                                return 'Week: ' + tooltipItems[0].xLabel;
                            }
                        }
                    },
            }
        });
    }
}(jQuery));


(function ($) {

    $.fn.paperHostDistribution = function (options) {


        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };

        plugin.init();

        let hosts = [];
        let data = [];

        let possible_colors = [chartColors.yellow, chartColors.green, chartColors.blue, chartColors.red, chartColors.limegreen];

        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            hosts.push(key);
            data.push(plugin.settings.plot_data[key]);
        });

        // Sorting by host name
        //1) combine the arrays:
        var list = [];
        for (var j = 0; j < hosts.length; j++)
            list.push({'host': hosts[j], 'count': data[j]});

        //2) sort:
        list.sort(function (a, b) {
            return ((a.host.toLowerCase() < b.host.toLowerCase()) ? -1 : ((a.host === b.host) ? 0 : 1));
            //Sort could be modified to, for example, sort on the age
            // if the name is the same.
        });

        //3) separate them back out:
        for (var k = 0; k < list.length; k++) {
            hosts[k] = list[k].host;
            data[k] = list[k].count;
        }

        return new Chart(plugin, {
            type: "doughnut",
            data: {
                labels: hosts,
                datasets: [{
                    data: data,
                    backgroundColor: possible_colors.slice(0, hosts.length)
                }]
            },
            options: {
                maintainAspectRatio: false
            }
        });


    }
}(jQuery));

(function ($) {

    $.fn.paperTopicDistribution = function (options) {

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };

        plugin.init();

        let topics = [];
        let data = [];
        let labels_nulls = [];

        let possible_colors = [chartColors.orange, chartColors.green, chartColors.blue, chartColors.orange, chartColors.purple, chartColors.yellow, chartColors.grey, chartColors.limegreen, chartColors.pink];

        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            topics.push(key);
            data.push(plugin.settings.plot_data[key]);
            labels_nulls.push(0);
        });

        return new Chart(plugin, {
                type: "bar",
                data: {
                    labels: labels_nulls,
                    datasets: [{
                        data: data,
                        backgroundColor: possible_colors.slice(0, topics.length)
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    legend: {
                        display: false
                    },
                    scales: {
                        xAxes: [{
                            display: false
                        }],
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Number of papers'
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'single',
                        callbacks: {
                            label: function (tooltipItem, point) {
                                let value = data[tooltipItem.index];
                                return "Papers: " + value;
                            },
                            afterBody: function (tooltipItems, data) {

                                let tooltipItem = tooltipItems[0];

                                let text = topics[tooltipItem.index].split(" ");

                                let output = [];
                                let current = "";

                                for (var i = 0; i < text.length; i++) {
                                    current += text[i] + " ";

                                    if (current.length >= 50) {
                                        output.push(current);
                                        current = "";
                                    }
                                }

                                if (current.length > 0) {
                                    output.push(current);
                                }

                                return output;
                            },

                            title: function () {
                            }

                        }
                    }
                }
            }
        );


    }
}(jQuery));

(function ($) {

    $.fn.paperCategoryDistribution = function (options) {

        let plugin = this;

        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };

        plugin.init();

        let categories = [];
        let data = [];
        let backgroundColors = [];

        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            categories.push(key);
            data.push(plugin.settings.plot_data[key]['count']);
            backgroundColors.push(plugin.settings.plot_data[key]['color']);
        });

        return new Chart(plugin, {
                type: "horizontalBar",
                data: {
                    labels: categories,
                    datasets: [{
                        data: data,
                        backgroundColor: backgroundColors
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: false
                    },
                    scales: {
                        xAxes: [{
                            scaleLabel: {
                                display: true,
                                labelString: 'Number of papers'
                            },
                            ticks: {
                                beginAtZero: true
                            },
                        }],
                        yAxes: [{}]
                    },
                    tooltips: {}
                }
            }
        );


    }
}(jQuery));
