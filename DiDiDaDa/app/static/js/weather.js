$(document).ready(function() {
    // 将获取天气的逻辑封装成一个函数
    function getWeatherForCity(city) {
        $.post("/weather", { city: city }, function(data) {
            let htmlContent = "";
            data.forEach(dayWeather => {
                htmlContent += `
                    <div class="daily-weather">
                        <div class="r1">
                            <span class="daily-date">${dayWeather.date}</span>
                            <span class="chinese-date">${dayWeather.day}</span>
                        </div>
                        <div class="r2">
                            <span class="daily-temperature">${dayWeather.temperature}°</span>
                            <span id="rain">☂</span>
                            <span class="rain-chance">${dayWeather.rain_chance}%</span>
                        </div>
                    </div>
                `;
            });
            $("#weather-data").html(htmlContent);
        });
    }

    // 页面加载时立即获取台北市的天气
    getWeatherForCity('新北市');

    

    // 如果用户更改了下拉菜单中的选择，则也可以获取新城市的天气
    $("#city-dropdown").change(function() {
        var selectedCity = $(this).val();
        getWeatherForCity(selectedCity);
    });
});


