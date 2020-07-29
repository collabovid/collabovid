(function ($) {
    $.fn.queriesOverTime = function (options) {
        let plugin = this;
        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };
        plugin.init();
        let created_dates = [];
        plugin.settings.plot_data['x'].forEach(function (item) {
            created_dates.push(new Date(item));
        });
        return new Chart(plugin, {
            type: 'line',
            data: {
                labels: created_dates,
                datasets: [
                    {
                        label: 'Total queries',
                        borderColor: window.chartColors.blue,
                        fill: false,
                        data: plugin.settings.plot_data['total'],
                        yAxisID: 'total'
                    },
                    {
                        label: 'Queries per day',
                        borderColor: window.chartColors.red,
                        type: 'line',
                        fill: false,
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
                            labelString: 'Number of queries/day',
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

var chartColorIndex = 0;

(function ($) {
    $.fn.queryDistribution = function (options) {
        let plugin = this;
        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };
        plugin.init();
        let keys = [];
        let data = [];
        let possible_colors = [];
        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            keys.push(key);
            data.push(plugin.settings.plot_data[key]);
        });
        for (let i = 0; i < keys.length; i++) {
            possible_colors.push(window.chartColors[Object.keys(window.chartColors)[chartColorIndex]])
            chartColorIndex = (chartColorIndex + 1) % Object.keys(window.chartColors).length;
        }

        return new Chart(plugin, {
            type: "doughnut",
            data: {
                labels: keys,
                datasets: [{
                    data: data,
                    backgroundColor: possible_colors.slice(0, keys.length)
                }]
            },
            options: {
                maintainAspectRatio: false
            }
        });
    }
}(jQuery));


(function ($) {
    $.fn.barChart = function (options) {
        let plugin = this;
        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };
        plugin.init();
        let keys = [];
        let data = [];
        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            keys.push(key);
            data.push(plugin.settings.plot_data[key]);
        });
        let possibleColors = []
        for (let i = 0; i < keys.length; i++) {
            possibleColors.push(window.chartColors[Object.keys(window.chartColors)[chartColorIndex]])
            chartColorIndex = (chartColorIndex + 1) % Object.keys(window.chartColors).length;
        }
        return new Chart(plugin, {
            type: 'horizontalBar',
            data: {
                labels: keys,
                datasets: [{
                    label: 'all',
                    data: data,
                    backgroundColor: possibleColors,
                    fill: false
                }]
            },
            options: {}
        });
    }
}(jQuery));

(function ($) {
    $.fn.stackedBarChart = function (options) {
        let plugin = this;
        plugin.init = function () {
            plugin.settings = $.extend({
                plot_data: null,
            }, options);
        };
        plugin.init();

        let data = plugin.settings.plot_data['data']
        let possibleColors = []
        for (let i = 0; i < data.length; i++) {
            possibleColors.push(window.chartColors[Object.keys(window.chartColors)[chartColorIndex]])
            chartColorIndex = (chartColorIndex + 1) % Object.keys(window.chartColors).length;
        }
        let datasets = []
        for (let i = 0; i < data.length; i++) {
            datasets.push({
                label: i + 1,
                data: data[i],
                backgroundColor: possibleColors[i]
            })
        }

        return new Chart(plugin, {
            type: 'horizontalBar',
            data: {
                labels: plugin.settings.plot_data['labels'],
                datasets: datasets
            },
            options: {
                scales: {
                    xAxes: [{
                        stacked: true
                    }],
                    yAxes: [{
                        stacked: true
                    }]
                }
            }
        });
    }
}(jQuery));