window.chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)',
    limegreen: 'rgb(147,207,96)',
    pink: 'rgb(207,80,141)',
};

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

        let possible_colors = [chartColors.orange, chartColors.green, chartColors.blue, chartColors.yellow, chartColors.red];

        Object.keys(plugin.settings.plot_data).forEach(function (key) {
            hosts.push(key);
            data.push(plugin.settings.plot_data[key]);
        });

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
