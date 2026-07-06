import React from 'react';
import { 
  Cloud, CloudRain, Sun, CloudFog, CloudLightning, Snowflake, 
  Wind, Thermometer, Droplets, Sunrise, Sunset, AlertTriangle, Clock
} from 'lucide-react';
import { motion } from 'framer-motion';

// Weather code to icon mapping (WMO codes)
const getWeatherDetails = (code) => {
  if (code === 0) return { icon: Sun, label: 'Clear sky', color: 'text-amber-400' };
  if (code <= 3) return { icon: Cloud, label: 'Partly cloudy', color: 'text-slate-300' };
  if (code <= 49) return { icon: CloudFog, label: 'Fog', color: 'text-slate-400' };
  if (code <= 69) return { icon: CloudRain, label: 'Rain', color: 'text-blue-400' };
  if (code <= 79) return { icon: Snowflake, label: 'Snow', color: 'text-sky-300' };
  if (code <= 99) return { icon: CloudLightning, label: 'Thunderstorm', color: 'text-purple-400' };
  return { icon: Cloud, label: 'Unknown', color: 'text-slate-400' };
};

const formatTime = (dateStr) => {
  if (!dateStr) return '--:--';
  const date = new Date(dateStr);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const WeatherCard = ({ data }) => {
  const { city, date, type, forecast } = data;
  const { 
    temperature_2m_max, temperature_2m_min, 
    apparent_temperature_max, apparent_temperature_min,
    weather_code, precipitation_probability_max, precipitation_sum,
    wind_speed_10m_max, wind_gusts_10m_max, uv_index_max,
    sunrise, sunset
  } = forecast || {};

  const weatherDetails = getWeatherDetails(weather_code);
  const WeatherIcon = weatherDetails.icon;

  const displayDate = new Date(date).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  });

  const isRainWarning = precipitation_probability_max > 50 || precipitation_sum > 10;
  const isHighUV = uv_index_max > 7;
  const isHistorical = type === 'historical';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white backdrop-blur-xl border border-slate-200 rounded-3xl overflow-hidden shadow-lg w-[85vw] sm:w-[320px] max-w-sm flex-shrink-0 snap-center relative"
      style={{
        backgroundImage: `linear-gradient(to bottom, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.4) 40%, rgba(255,255,255,0.9) 65%, white 75%), url('https://loremflickr.com/800/600/${encodeURIComponent(city)},landmark/all')`,
        backgroundSize: 'cover',
        backgroundPosition: 'top center',
      }}
    >
      {/* Smart Badges */}
      <div className="flex flex-wrap gap-2 px-5 pt-5 pb-2">
        {isRainWarning && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-xs font-semibold border border-blue-200">
            <CloudRain size={14} /> Rain Warning
          </div>
        )}
        {isHighUV && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-semibold border border-orange-200">
            <AlertTriangle size={14} /> High UV
          </div>
        )}
        {isHistorical && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold border border-slate-200">
            <Clock size={14} /> Historical
          </div>
        )}
      </div>

      {/* Hero Header */}
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-800 capitalize">{city}</h2>
          <p className="text-slate-500 font-medium mt-1">{displayDate}</p>
          <div className="mt-4 flex items-center gap-3">
            <span className="text-4xl font-bold tracking-tighter text-slate-800">
              {temperature_2m_max !== null ? Math.round(temperature_2m_max) : '--'}°
            </span>
            <div className="text-slate-500 text-sm leading-tight font-medium">
              <div>High</div>
              <div>Low {temperature_2m_min !== null ? Math.round(temperature_2m_min) : '--'}°</div>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center">
          <WeatherIcon size={72} strokeWidth={1.5} className={`drop-shadow-sm ${weatherDetails.color}`} />
          <span className="text-xs font-medium text-slate-500 mt-2">{weatherDetails.label}</span>
        </div>
      </div>

      {/* Multi-Metric Grid */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-3">
          {/* Thermal Comfort */}
          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100 hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
              <Thermometer size={14} className="text-rose-400" /> Feels Like
            </div>
            <div className="text-lg font-semibold text-slate-700">
              {apparent_temperature_min !== null ? Math.round(apparent_temperature_min) : '--'}° 
              <span className="text-slate-400 font-normal mx-1">-</span> 
              {apparent_temperature_max !== null ? Math.round(apparent_temperature_max) : '--'}°
            </div>
          </div>

          {/* Wind Vector */}
          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100 hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
              <Wind size={14} className="text-teal-500" /> Wind & Gusts
            </div>
            <div className="text-lg font-semibold text-slate-700">
              {wind_speed_10m_max !== null ? Math.round(wind_speed_10m_max) : '--'} <span className="text-sm font-normal text-slate-500">km/h</span>
            </div>
            {wind_gusts_10m_max !== null && (
              <div className="text-xs font-medium text-slate-500">Gusts: {Math.round(wind_gusts_10m_max)} km/h</div>
            )}
          </div>

          {/* Rain Probability */}
          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100 hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider">
              <Droplets size={14} className="text-blue-500" /> Precipitation
            </div>
            <div className="text-lg font-semibold text-slate-700">
              {precipitation_probability_max !== null ? `${precipitation_probability_max}%` : '--'}
            </div>
            {precipitation_sum !== null && precipitation_sum > 0 && (
              <div className="text-xs font-medium text-slate-500">{precipitation_sum} mm expected</div>
            )}
            {precipitation_sum === 0 && (
              <div className="text-xs font-medium text-slate-500">No rain expected</div>
            )}
          </div>

          {/* Sun Cycle */}
          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col justify-between border border-slate-100 hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <Sun size={14} className="text-amber-500" /> Sun Cycle
            </div>
            <div className="flex items-center justify-between text-sm font-semibold text-slate-700">
              <div className="flex items-center gap-1.5">
                <Sunrise size={14} className="text-slate-500" /> {formatTime(sunrise)}
              </div>
            </div>
            <div className="flex items-center justify-between text-sm font-semibold text-slate-700 mt-1">
              <div className="flex items-center gap-1.5">
                <Sunset size={14} className="text-slate-500" /> {formatTime(sunset)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default WeatherCard;
