const ten_seconds = 10000;

let context = document.getElementById('myChart');

let timestamps = [];

let open_candles  = [];
let high_candles  = [];
let low_candles   = [];
let close_candles = [];

let candle_data = [];

const data = {
    datasets: [{
        label: 'BTC/USDT',
        data: candle_data
    }]
};


let annotations = {};

const options = {
    locale: 'en',
    animation: {
        duration: 0
    },
    scales: {
        x: { 
            type: 'time',
            time: {
                unit: 'hour',
                displayFormats: {
                  hour: 'H:mm'
                },
            },
            tooltipFormat: 'MMM d, HH:mm',
            ticks: {
                color: '#eeeeee'
            }
        },
        y: {
            ticks: {
                color: '#eeeeee'
            }
        }
    },
    plugins: {
        annotation: {
            annotations: {}
        },
        legend: {
            display: false
        },
        tooltip: {
            displayColors: false
        }
    }
};


const config = {
    type: 'candlestick',
    data: data,
    options: options
};


const chart = new Chart(context, config);

update_chart_values_to_python_values();

setInterval(update_chart_values_to_python_values, ten_seconds);


async function update_chart_values_to_python_values() {
        
    let [ time, open, high, low, close ] = await get_python_values();

    timestamps.length = 0;
    open_candles.length  = 0;
    high_candles.length  = 0;
    low_candles.length   = 0;
    close_candles.length = 0;

    timestamps.push(...time);
    open_candles.push(...open);
    high_candles.push(...high);
    low_candles.push(...low);
    close_candles.push(...close);

    candle_data = timestamps.map((t,i) => ({
        x: t,
        o: open_candles[i],
        h: high_candles[i],
        l: low_candles[i],
        c: close_candles[i]
    }));

    chart.data.datasets[0].data = candle_data;
    
    load_signals();

    chart.update();
}

async function get_python_values() {
    try {
        const response = await fetch("/chart_values");
        const data = await response.json();
        return [ data['timestamps'], data['open_candles'], data['high_candles'], data['low_candles'], data['close_candles'] ];
    }
    catch(err) {
        console.error("Error fetching ohlc:", err);
        return -1;
    }
}

async function get_recent_signals() {
    try {
        const response = await fetch("/signals");
        const data = await response.json();
        return data["recent_signals"];
    }
    catch(err) {
        console.error("Error fetching recent signals:", err);
        return -1;
    }
}


async function load_signals() {
    const signals = await get_recent_signals();

    annotations = {}; // reset annotations
    signals.forEach((signal, i) => {
        annotations['signal' + i] = {
            type: 'line',
            xMin: signal.time,
            xMax: signal.time,
            borderColor: signal.type === 'buy' ? 'green' : 'red',
            borderWidth: 2,
            label: {
                display: true,
                content: signal.type.toUpperCase(),
                position: 'start',
                backgroundColor: signal.type === 'buy' ? 'green' : 'red',
                color: '#fff'
            }
        };
    });

    chart.config.options.plugins.annotation.annotations = annotations;
    chart.update();
}