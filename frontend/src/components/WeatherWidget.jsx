import React, { useRef } from 'react';
import WeatherCard from './WeatherCard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const WeatherWidget = ({ data }) => {
  const scrollRef = useRef(null);

  if (!data || !data.length) return null;

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { current } = scrollRef;
      const scrollAmount = direction === 'left' ? -340 : 340;
      current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  return (
    <div className="relative group w-full mt-4">
      {data.length > 1 && (
        <>
          <button 
            onClick={() => scroll('left')}
            className="absolute left-[-20px] top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/50 text-slate-800 backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/80 hidden md:flex items-center justify-center border border-slate-200 shadow-md"
          >
            <ChevronLeft size={20} />
          </button>
          <button 
            onClick={() => scroll('right')}
            className="absolute right-[-20px] top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-white/50 text-slate-800 backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/80 hidden md:flex items-center justify-center border border-slate-200 shadow-md"
          >
            <ChevronRight size={20} />
          </button>
        </>
      )}

      <div 
        ref={scrollRef}
        className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory hide-scrollbar custom-scrollbar-hide"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {data.map((record, idx) => (
          <WeatherCard key={`${record.city}-${record.date}-${idx}`} data={record} />
        ))}
      </div>
    </div>
  );
};

export default WeatherWidget;
