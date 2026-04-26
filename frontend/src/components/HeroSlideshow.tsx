import { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

/**
 * HeroSlideshow
 * ─────────────────────────────────────────────────────────────────
 * Drop your images into  frontend/public/hero/
 * and list the file names in the `slides` array below.
 *
 * Each slide has:
 *   image   → path inside /public  (e.g. "/hero/slide1.jpg")
 *   gradient → fallback shown while image loads or if image is absent
 *   headline / sub → optional overlay text
 */

const slides = [
  {
    image: '/hero/slide1.jpg',
    gradient: 'from-teal-900 via-cyan-800 to-emerald-900',
    headline: 'New Arrivals',
    sub: 'Fresh drops every week',
  },
  {
    image: '/hero/slide2.jpg',
    gradient: 'from-violet-900 via-purple-800 to-indigo-900',
    headline: 'Curated Collection',
    sub: 'Hand-picked for quality',
  },
  {
    image: '/hero/slide3.jpg',
    gradient: 'from-rose-900 via-red-800 to-orange-900',
    headline: 'Street Essentials',
    sub: 'Style that moves with you',
  },
  {
    image: '/hero/slide4.jpg',
    gradient: 'from-emerald-900 via-green-800 to-teal-900',
    headline: 'Premium Selection',
    sub: 'Elevated everyday wear',
  },
  {
    image: '/hero/slide5.jpg',
    gradient: 'from-slate-900 via-zinc-800 to-neutral-900',
    headline: 'Limited Edition',
    sub: 'Get it before it\'s gone',
  },
];

const AUTOPLAY_INTERVAL = 5000;

export default function HeroSlideshow() {
  const [current, setCurrent] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const goTo = useCallback((index: number) => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    setCurrent(index);
    setTimeout(() => setIsTransitioning(false), 600);
  }, [isTransitioning]);

  const next = useCallback(() => {
    goTo((current + 1) % slides.length);
  }, [current, goTo]);

  const prev = useCallback(() => {
    goTo((current - 1 + slides.length) % slides.length);
  }, [current, goTo]);

  // Autoplay
  useEffect(() => {
    if (isPaused) return;
    timerRef.current = setInterval(next, AUTOPLAY_INTERVAL);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [next, isPaused]);

  // Touch swipe
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.touches[0].clientX);
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStart === null) return;
    const diff = touchStart - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) diff > 0 ? next() : prev();
    setTouchStart(null);
  };

  const handleImageError = (index: number) => {
    setImageErrors(prev => new Set(prev).add(index));
  };

  return (
    <div
      className="relative w-full overflow-hidden rounded-2xl"
      style={{ height: 'clamp(260px, 52vw, 580px)' }}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Slides */}
      {slides.map((slide, i) => {
        const showImage = !imageErrors.has(i);
        return (
          <div
            key={i}
            className={`absolute inset-0 transition-all duration-700 ease-in-out ${
              i === current ? 'opacity-100 scale-100 z-10' : 'opacity-0 scale-[1.03] z-0'
            }`}
            aria-hidden={i !== current}
          >
            {/* Background: image or gradient fallback */}
            <div className={`absolute inset-0 bg-gradient-to-br ${slide.gradient}`} />
            {showImage && (
              <img
                src={slide.image}
                alt={slide.headline}
                className="absolute inset-0 w-full h-full object-cover"
                onError={() => handleImageError(i)}
                loading={i === 0 ? 'eager' : 'lazy'}
              />
            )}

            {/* Dark gradient overlay for text legibility */}
            <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-transparent" />

            {/* Text overlay */}
            <div className="absolute inset-0 flex flex-col justify-center px-8 sm:px-14 lg:px-20">
              <div
                className={`transition-all duration-700 delay-200 ${
                  i === current ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}
              >
                <span className="inline-block text-xs sm:text-sm font-semibold tracking-widest uppercase text-white/70 mb-3">
                  eshop · {i + 1}/{slides.length}
                </span>
                <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white leading-tight drop-shadow-lg">
                  {slide.headline}
                </h2>
                <p className="mt-2 text-base sm:text-lg text-white/80 drop-shadow">
                  {slide.sub}
                </p>
              </div>
            </div>
          </div>
        );
      })}

      {/* Left Arrow */}
      <button
        onClick={prev}
        className="absolute left-3 sm:left-5 top-1/2 -translate-y-1/2 z-20
                   w-10 h-10 sm:w-12 sm:h-12 rounded-full
                   bg-black/30 hover:bg-black/60 backdrop-blur-sm
                   border border-white/20 hover:border-white/40
                   flex items-center justify-center
                   text-white transition-all duration-200 hover:scale-105
                   focus:outline-none focus:ring-2 focus:ring-white/50"
        aria-label="Previous slide"
      >
        <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6" />
      </button>

      {/* Right Arrow */}
      <button
        onClick={next}
        className="absolute right-3 sm:right-5 top-1/2 -translate-y-1/2 z-20
                   w-10 h-10 sm:w-12 sm:h-12 rounded-full
                   bg-black/30 hover:bg-black/60 backdrop-blur-sm
                   border border-white/20 hover:border-white/40
                   flex items-center justify-center
                   text-white transition-all duration-200 hover:scale-105
                   focus:outline-none focus:ring-2 focus:ring-white/50"
        aria-label="Next slide"
      >
        <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6" />
      </button>

      {/* Dot Indicators */}
      <div className="absolute bottom-4 sm:bottom-5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            className={`rounded-full transition-all duration-300 focus:outline-none
                        ${i === current
                          ? 'w-7 sm:w-8 h-2.5 sm:h-2.5 bg-white'
                          : 'w-2 h-2 bg-white/40 hover:bg-white/60'
                        }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>

      {/* Progress bar */}
      {!isPaused && (
        <div className="absolute bottom-0 left-0 right-0 z-20 h-[3px] bg-white/10">
          <div
            key={current}
            className="h-full bg-white/60"
            style={{
              animation: `slideProgress ${AUTOPLAY_INTERVAL}ms linear`,
            }}
          />
        </div>
      )}

      <style>{`
        @keyframes slideProgress {
          from { width: 0% }
          to   { width: 100% }
        }
      `}</style>
    </div>
  );
}
